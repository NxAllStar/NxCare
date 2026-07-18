"""HTTP tests for the arrival-time endpoints (extends FR-02).

Mounts the intake router over an in-memory repo seeded with the arrival fixtures. The reasoning
client is patched to the deterministic `RuleBasedArrivalChatLLM` (and triage likewise) so no request
reaches a provider - a real network call in a test is a defect (testing.md). The live provider is
covered separately by `scripts/check_llm.py`, run by hand.
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from vaic.agents.intake.arrival_chat import RuleBasedArrivalChatLLM
from vaic.agents.intake.llm_client import RuleBasedTriageLLM
from vaic.api.demo_state import ARRIVAL_DEMO_ANCHOR, seed_arrival_demo
from vaic.api.intake_routes import build_intake_router
from vaic.models import Appointment
from vaic.state import InMemoryRepository


def _client_and_repo() -> tuple[TestClient, InMemoryRepository]:
    repo = InMemoryRepository()
    seed_arrival_demo(repo)
    with (
        patch(
            "vaic.api.intake_routes.build_arrival_chat_llm",
            return_value=RuleBasedArrivalChatLLM(),
        ),
        patch("vaic.api.intake_routes.build_triage_llm", return_value=RuleBasedTriageLLM()),
    ):
        router = build_intake_router(repo)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app), repo


def test_suggest_returns_message_and_time_blocks():
    client, _ = _client_and_repo()

    response = client.post(
        "/api/intake/arrival/suggest", json={"text": "khi nao toi nen den kham?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["emergencySuspected"] is False
    assert body["reply"]["text"]  # the agent's natural-language answer is present
    blocks = body["recommendations"]
    assert len(blocks) > 0
    counts = [b["reservationCount"] for b in blocks]
    assert counts == sorted(counts)  # least-crowded first
    assert counts[0] == 0  # the seeded data has empty working hours
    first = blocks[0]
    assert {"date", "startHour", "endHour", "reservationCount", "reason"} <= first.keys()
    assert first["endHour"] > first["startHour"]


def test_suggest_flags_emergency_and_does_not_schedule():
    client, _ = _client_and_repo()

    response = client.post(
        "/api/intake/arrival/suggest", json={"text": "toi bi dau nguc du doi va kho tho"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["emergencySuspected"] is True
    assert body["recommendations"] == []


def test_confirm_persists_appointment_without_owner():
    client, repo = _client_and_repo()
    before = len(repo.list(Appointment))
    patient_id = str(uuid4())
    start = ARRIVAL_DEMO_ANCHOR.replace(hour=6).isoformat()

    response = client.post(
        "/api/intake/arrival/confirm",
        json={"patientId": patient_id, "specialty": "NOI_TONG_QUAT", "start": start},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PROPOSED"
    assert body["ownerId"] is None
    assert len(repo.list(Appointment)) == before + 1
    saved = repo.get(Appointment, UUID(body["appointmentId"]))
    assert saved is not None and str(saved.patient_id) == patient_id


def test_confirm_rejects_bad_datetime():
    client, _ = _client_and_repo()

    response = client.post(
        "/api/intake/arrival/confirm",
        json={"patientId": str(uuid4()), "specialty": "NOI_TONG_QUAT", "start": "not-a-datetime"},
    )

    assert response.status_code == 422

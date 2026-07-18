"""HTTP tests for the arrival-time endpoints (extends FR-02).

Mounts the intake router on a bare FastAPI app over an in-memory repo seeded with the arrival demo
fixtures, so the whole path - triage -> rank -> suggest, and confirm -> persist - is exercised
end to end. `build_triage_llm` is patched to the deterministic `RuleBasedTriageLLM` so no request
ever reaches a provider (a real network call would be a defect, testing.md), regardless of whether
a local `.env` has provider keys set.
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from vaic.agents.intake.llm_client import RuleBasedTriageLLM
from vaic.api.demo_state import ARRIVAL_DEMO_ANCHOR, ARRIVAL_DOCTOR_B, seed_arrival_demo
from vaic.api.intake_routes import build_intake_router
from vaic.models import Appointment
from vaic.state import InMemoryRepository


def _client_and_repo() -> tuple[TestClient, InMemoryRepository]:
    repo = InMemoryRepository()
    seed_arrival_demo(repo)
    with patch(
        "vaic.api.intake_routes.build_triage_llm", return_value=RuleBasedTriageLLM()
    ):
        router = build_intake_router(repo)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app), repo


def test_suggest_returns_top_three_least_crowded():
    client, _ = _client_and_repo()

    response = client.post("/api/intake/arrival/suggest", json={"text": "toi muon kham tong quat"})

    assert response.status_code == 200
    body = response.json()
    assert body["emergencySuspected"] is False
    assert body["specialty"] == "NOI_TONG_QUAT"
    suggestions = body["suggestions"]
    assert 0 < len(suggestions) <= 3
    counts = [item["participants"] for item in suggestions]
    assert counts == sorted(counts)  # least-crowded first
    assert counts[0] == 0  # an empty slot exists in the seeded fixtures


def test_confirm_persists_appointment():
    client, repo = _client_and_repo()
    before = len(repo.list(Appointment))
    patient_id = str(uuid4())
    start = (ARRIVAL_DEMO_ANCHOR.replace(hour=11)).isoformat()

    response = client.post(
        "/api/intake/arrival/confirm",
        json={
            "patientId": patient_id,
            "specialty": "NOI_TONG_QUAT",
            "ownerId": str(ARRIVAL_DOCTOR_B),
            "start": start,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PROPOSED"
    assert body["ownerId"] == str(ARRIVAL_DOCTOR_B)
    # the choice is on record for later use
    after = repo.list(Appointment)
    assert len(after) == before + 1
    saved = repo.get(Appointment, UUID(body["appointmentId"]))
    assert saved is not None and str(saved.patient_id) == patient_id


def test_confirm_rejects_bad_datetime():
    client, _ = _client_and_repo()

    response = client.post(
        "/api/intake/arrival/confirm",
        json={
            "patientId": str(uuid4()),
            "specialty": "NOI_TONG_QUAT",
            "ownerId": str(ARRIVAL_DOCTOR_B),
            "start": "not-a-datetime",
        },
    )

    assert response.status_code == 422

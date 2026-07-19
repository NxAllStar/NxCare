"""HTTP tests for the unified patient chat: /chat, /confirm, /status, /queue, and /tasks.

Mounts the intake router over an in-memory repo seeded with the arrival fixtures. The assistant
client is patched to the deterministic `RuleBasedArrivalChatLLM` so no request reaches a provider -
a real network call in a test is a defect (testing.md). The live provider is covered separately by
`scripts/check_llm.py`, run by hand.
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from vaic.agents.intake.arrival_chat import RuleBasedArrivalChatLLM
from vaic.api.demo_state import ARRIVAL_DEMO_ANCHOR, seed_arrival_demo
from vaic.api.intake_routes import build_intake_router
from vaic.models import (
    Appointment,
    CarePlan,
    CarePlanStatus,
    Diagnosis,
    ExecutionStatus,
    PaymentStatus,
    QueueSubjectType,
    QueueTicket,
    ServiceOrder,
    ServiceType,
    Task,
)
from vaic.state import InMemoryRepository


def _client_and_repo() -> tuple[TestClient, InMemoryRepository]:
    repo = InMemoryRepository()
    seed_arrival_demo(repo)
    with patch(
        "vaic.api.intake_routes.build_arrival_chat_llm", return_value=RuleBasedArrivalChatLLM()
    ):
        router = build_intake_router(repo)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app), repo


def test_chat_scheduling_intent_returns_time_blocks():
    client, _ = _client_and_repo()

    response = client.post("/api/intake/chat", json={"text": "khi nao toi nen den kham?"})

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "SCHEDULE"
    assert body["emergencySuspected"] is False
    assert body["reply"]["text"]
    blocks = body["recommendations"]
    assert len(blocks) > 0
    counts = [b["reservationCount"] for b in blocks]
    assert counts == sorted(counts)
    assert counts[0] == 0
    assert {"date", "startHour", "endHour", "reservationCount", "reason"} <= blocks[0].keys()


def test_chat_normal_message_is_plain_chat_no_blocks():
    client, _ = _client_and_repo()

    response = client.post("/api/intake/chat", json={"text": "cam on bac si nhieu"})

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "CHAT"
    assert body["recommendations"] == []
    assert body["emergencySuspected"] is False


def test_chat_flags_emergency_and_does_not_schedule():
    client, _ = _client_and_repo()

    response = client.post("/api/intake/chat", json={"text": "toi bi dau nguc du doi va kho tho"})

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "EMERGENCY"
    assert body["emergencySuspected"] is True
    assert body["recommendations"] == []


def test_confirm_logs_the_time():
    client, repo = _client_and_repo()
    before = len(repo.list(Appointment))
    patient_id = str(uuid4())
    start = ARRIVAL_DEMO_ANCHOR.replace(hour=6).isoformat()

    response = client.post(
        "/api/intake/confirm", json={"patientId": patient_id, "start": start}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PROPOSED"
    assert body["ownerId"] is None
    assert len(repo.list(Appointment)) == before + 1
    saved = repo.get(Appointment, UUID(body["appointmentId"]))
    assert saved is not None and str(saved.patient_id) == patient_id
    assert body["patientCode"].startswith("P-")  # a scannable code was created (FR-17)


def test_confirm_creates_patient_record_once_and_keeps_code():
    client, repo = _client_and_repo()
    from vaic.models import Patient

    patient_id = str(uuid4())
    start = ARRIVAL_DEMO_ANCHOR.replace(hour=6).isoformat()

    first = client.post(
        "/api/intake/confirm", json={"patientId": patient_id, "start": start}
    ).json()
    second = client.post(
        "/api/intake/confirm", json={"patientId": patient_id, "start": start}
    ).json()

    assert first["patientCode"] == second["patientCode"]  # same patient -> same code
    assert len(repo.list(Patient, id=UUID(patient_id))) == 1


def test_confirm_rejects_bad_datetime():
    client, _ = _client_and_repo()

    response = client.post(
        "/api/intake/confirm", json={"patientId": str(uuid4()), "start": "not-a-datetime"}
    )

    assert response.status_code == 422


def test_confirm_also_issues_a_consult_ticket():
    client, repo = _client_and_repo()
    patient_id = str(uuid4())
    start = ARRIVAL_DEMO_ANCHOR.replace(hour=6).isoformat()

    response = client.post("/api/intake/confirm", json={"patientId": patient_id, "start": start})

    assert response.status_code == 200
    body = response.json()
    assert body["ticketLabel"].startswith("DepA-")
    tickets = [
        t
        for t in repo.list(QueueTicket, subject_type=QueueSubjectType.CONSULT)
        if str(t.patient_id) == patient_id
    ]
    assert len(tickets) == 1
    assert tickets[0].ticket_label == body["ticketLabel"]
    assert str(tickets[0].subject_id) == body["appointmentId"]


# ---- /status --------------------------------------------------------------------------------


def test_status_pre_diagnosis_for_unknown_patient():
    client, _ = _client_and_repo()

    response = client.get(f"/api/intake/status/{uuid4()}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PRE_DIAGNOSIS"
    assert body["queue"] is None
    assert body["planTasks"] == []


def test_status_awaiting_consult_after_confirm():
    client, _ = _client_and_repo()
    patient_id = str(uuid4())
    start = ARRIVAL_DEMO_ANCHOR.replace(hour=6).isoformat()
    confirm_body = client.post(
        "/api/intake/confirm", json={"patientId": patient_id, "start": start}
    ).json()

    response = client.get(f"/api/intake/status/{patient_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "AWAITING_CONSULT"
    assert body["queue"]["label"] == confirm_body["ticketLabel"]
    assert body["queue"]["peopleAhead"] == 0
    assert body["queue"]["etaMinutes"] == 0


def test_status_rejects_bad_patient_id():
    client, _ = _client_and_repo()

    response = client.get("/api/intake/status/not-a-uuid")

    assert response.status_code == 422


# ---- /queue -----------------------------------------------------------------------------------


def test_queue_overview_is_empty_before_any_confirm():
    client, _ = _client_and_repo()

    response = client.get("/api/intake/queue")

    assert response.status_code == 200
    assert response.json() == {"peopleWaiting": 0, "etaMinutes": 0}


def test_queue_overview_grows_as_patients_confirm():
    client, _ = _client_and_repo()
    start = ARRIVAL_DEMO_ANCHOR.replace(hour=6).isoformat()
    for _ in range(3):
        client.post(
            "/api/intake/confirm", json={"patientId": str(uuid4()), "start": start}
        )

    response = client.get("/api/intake/queue")

    assert response.status_code == 200
    body = response.json()
    assert body["peopleWaiting"] == 3
    assert body["etaMinutes"] == 3 * 15


# ---- /tasks -------------------------------------------------------------------------------------


def test_tasks_empty_when_patient_has_no_care_plan():
    client, _ = _client_and_repo()

    response = client.get(f"/api/intake/tasks/{uuid4()}")

    assert response.status_code == 200
    assert response.json() == {"tasks": []}


def test_tasks_lists_every_task_with_status_and_queue_position():
    client, repo = _client_and_repo()
    patient_id = uuid4()
    diagnosis = repo.save(
        Diagnosis(patient_id=patient_id, appointment_id=uuid4(), diagnosed_by=uuid4())
    )
    plan = repo.save(
        CarePlan(patient_id=patient_id, diagnosis_id=diagnosis.id, status=CarePlanStatus.ACTIVE)
    )
    service_type = repo.save(ServiceType(code="BLOOD_TEST", display_label="Blood Test"))
    order = repo.save(
        ServiceOrder(
            patient_id=patient_id,
            diagnosis_id=diagnosis.id,
            service_type_id=service_type.id,
            ordered_by=uuid4(),
        )
    )
    repo.save(
        Task(
            care_plan_id=plan.id,
            service_order_id=order.id,
            owner_id=uuid4(),
            execution_status=ExecutionStatus.PENDING,
            payment_status=PaymentStatus.PAID,
            estimated_duration_min=10,
            sequence_index=0,
        )
    )

    response = client.get(f"/api/intake/tasks/{patient_id}")

    assert response.status_code == 200
    tasks = response.json()["tasks"]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["serviceTypeCode"] == "BLOOD_TEST"
    assert task["serviceTypeLabel"] == "Blood Test"
    assert task["executionStatus"] == "PENDING"
    assert task["paymentStatus"] == "PAID"
    assert task["queue"] == {"label": None, "peopleAhead": 0, "etaMinutes": 0}


def test_tasks_rejects_bad_patient_id():
    client, _ = _client_and_repo()

    response = client.get("/api/intake/tasks/not-a-uuid")

    assert response.status_code == 422


# ---- /service-queue and /suggest-task-order ---------------------------------------------------


def _patient_with_tasks(repo, client) -> str:
    """Confirm a patient, call them, and complete with 2 ordered tests. Returns patientId."""
    from vaic.api.demo_state import ARRIVAL_SERVICE_TYPES, seed_service_types_demo
    from vaic.api.staff_routes import build_staff_router

    seed_service_types_demo(repo)
    staff = FastAPI()
    staff.include_router(build_staff_router(repo))
    staff_client = TestClient(staff)

    pid = str(uuid4())
    client.post("/api/intake/confirm", json={"patientId": pid,
                "start": ARRIVAL_DEMO_ANCHOR.replace(hour=6).isoformat()})
    owner = str(uuid4())
    called = None
    for _ in range(12):
        c = staff_client.post("/api/staff/queue/call-next", json={"ownerId": owner}).json()
        if c.get("patientId") == pid:
            called = c
            break
    blood_id = str(ARRIVAL_SERVICE_TYPES[0][0])
    ecg_id = str(ARRIVAL_SERVICE_TYPES[3][0])
    staff_client.post(
        f"/api/staff/appointments/{called['appointmentId']}/complete",
        json={"diagnosedBy": owner, "conditions": ["x"], "serviceTypeIds": [blood_id, ecg_id]},
    )
    return pid


def test_service_queue_404_for_unknown_service_type():
    client, _ = _client_and_repo()

    response = client.get(f"/api/intake/service-queue/{uuid4()}")

    assert response.status_code == 404


def test_service_queue_reports_zero_for_a_seeded_but_idle_service():
    client, repo = _client_and_repo()
    from vaic.api.demo_state import ARRIVAL_SERVICE_TYPES, seed_service_types_demo

    seed_service_types_demo(repo)
    blood_id = str(ARRIVAL_SERVICE_TYPES[0][0])

    response = client.get(f"/api/intake/service-queue/{blood_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["peopleWaiting"] == 0
    assert body["etaMinutes"] == 0


def test_suggest_task_order_returns_an_order_over_the_patient_tasks():
    client, repo = _client_and_repo()
    pid = _patient_with_tasks(repo, client)

    response = client.post("/api/intake/suggest-task-order", json={"patientId": pid})

    assert response.status_code == 200
    body = response.json()
    assert body["message"]
    codes = {entry["serviceTypeCode"] for entry in body["order"]}
    assert codes == {"BLOOD_TEST", "ECG"}  # both remaining services appear exactly once
    assert len(body["order"]) == 2


def test_suggest_task_order_empty_for_patient_without_a_plan():
    client, _ = _client_and_repo()

    response = client.post("/api/intake/suggest-task-order", json={"patientId": str(uuid4())})

    assert response.status_code == 200
    assert response.json()["order"] == []


def test_suggest_task_order_rejects_bad_patient_id():
    client, _ = _client_and_repo()

    response = client.post("/api/intake/suggest-task-order", json={"patientId": "not-a-uuid"})

    assert response.status_code == 422

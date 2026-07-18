"""HTTP tests for the staff/front-desk consult actions: call-next, complete (+outcome), requeue,
service-types.

Mounts the staff router over an in-memory repo seeded with the arrival fixtures, same pattern as
`test_intake_arrival_api.py`.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from vaic.agents.intake.patient_status import issue_consult_ticket
from vaic.api.demo_state import (
    ARRIVAL_DEPARTMENT_ID,
    ARRIVAL_SERVICE_TYPES,
    seed_arrival_demo,
    seed_service_types_demo,
)
from vaic.api.staff_routes import build_staff_router
from vaic.models import (
    Appointment,
    AppointmentStatus,
    CarePlan,
    Department,
    Diagnosis,
    ExecutionStatus,
    Patient,
    PaymentStatus,
    PriorityLevel,
    Task,
)
from vaic.state import InMemoryRepository


def _client_and_repo() -> tuple[TestClient, InMemoryRepository]:
    repo = InMemoryRepository()
    seed_arrival_demo(repo)
    seed_service_types_demo(repo)
    router = build_staff_router(repo)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app), repo


def _waiting_patient(repo: InMemoryRepository) -> tuple[str, str]:
    """Seed one PROPOSED appointment + WAITING consult ticket. Returns (patientId, ticketId)."""
    patient_id = uuid4()
    appointment = repo.save(
        Appointment(
            patient_id=patient_id, specialty="NOI_TONG_QUAT", status=AppointmentStatus.PROPOSED
        )
    )
    department = repo.get(Department, ARRIVAL_DEPARTMENT_ID)
    ticket = issue_consult_ticket(
        repo, department, appointment.id, patient_id, PriorityLevel.ROUTINE
    )
    return str(patient_id), str(ticket.id)


def test_call_next_returns_404_when_nobody_waiting():
    client, _ = _client_and_repo()

    response = client.post("/api/staff/queue/call-next", json={"ownerId": str(uuid4())})

    assert response.status_code == 404


def test_call_next_calls_the_waiting_patient():
    client, repo = _client_and_repo()
    patient_id, _ticket_id = _waiting_patient(repo)
    owner_id = str(uuid4())

    response = client.post("/api/staff/queue/call-next", json={"ownerId": owner_id})

    assert response.status_code == 200
    body = response.json()
    assert body["patientId"] == patient_id
    assert body["ownerId"] == owner_id
    assert body["ticketLabel"].startswith("DepA-")


def test_call_next_rejects_bad_owner_id():
    client, _ = _client_and_repo()

    response = client.post("/api/staff/queue/call-next", json={"ownerId": "not-a-uuid"})

    assert response.status_code == 422


def test_complete_marks_appointment_done():
    client, repo = _client_and_repo()
    _patient_id, _ticket_id = _waiting_patient(repo)
    called = client.post(
        "/api/staff/queue/call-next", json={"ownerId": str(uuid4())}
    ).json()

    response = client.post(f"/api/staff/appointments/{called['appointmentId']}/complete")

    assert response.status_code == 200
    assert response.json()["status"] == "DONE"


def test_complete_returns_409_when_never_called():
    client, repo = _client_and_repo()
    appointment = repo.save(
        Appointment(
            patient_id=uuid4(), specialty="NOI_TONG_QUAT", status=AppointmentStatus.PROPOSED
        )
    )

    response = client.post(f"/api/staff/appointments/{appointment.id}/complete")

    assert response.status_code == 404


def test_complete_returns_404_for_unknown_appointment():
    client, _ = _client_and_repo()

    response = client.post(f"/api/staff/appointments/{uuid4()}/complete")

    assert response.status_code == 404


def test_requeue_puts_ticket_back_to_waiting():
    client, repo = _client_and_repo()
    _patient_id, _ticket_id = _waiting_patient(repo)
    called = client.post(
        "/api/staff/queue/call-next", json={"ownerId": str(uuid4())}
    ).json()

    response = client.post(f"/api/staff/queue/{called['ticketId']}/requeue")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "WAITING"
    assert body["ticketLabel"] == called["ticketLabel"]

    # calling next again picks the same (requeued) ticket back up
    recalled = client.post("/api/staff/queue/call-next", json={"ownerId": str(uuid4())}).json()
    assert recalled["ticketId"] == called["ticketId"]


def test_requeue_returns_409_when_ticket_still_waiting():
    client, repo = _client_and_repo()
    _patient_id, ticket_id = _waiting_patient(repo)  # never called

    response = client.post(f"/api/staff/queue/{ticket_id}/requeue")

    assert response.status_code == 409


def test_requeue_rejects_bad_ticket_id():
    client, _ = _client_and_repo()

    response = client.post("/api/staff/queue/not-a-uuid/requeue")

    assert response.status_code == 422


# ---- complete WITH a consult outcome (diagnosis + ordered tests -> tasks) ---------------------


def test_complete_with_diagnosis_records_outcome_and_closes_visit():
    client, repo = _client_and_repo()
    _waiting_patient(repo)
    called = client.post("/api/staff/queue/call-next", json={"ownerId": str(uuid4())}).json()
    blood_id = str(ARRIVAL_SERVICE_TYPES[0][0])
    xray_id = str(ARRIVAL_SERVICE_TYPES[1][0])

    response = client.post(
        f"/api/staff/appointments/{called['appointmentId']}/complete",
        json={
            "diagnosedBy": called["ownerId"],
            "conditions": ["hypertension"],
            "serviceTypeIds": [blood_id, xray_id],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "DONE"
    assert body["outcome"] is not None
    assert len(body["outcome"]["taskIds"]) == 2

    # the diagnosis + tasks are actually persisted for the patient
    patient_id = called["patientId"]
    from uuid import UUID

    assert repo.list(Diagnosis, patient_id=UUID(patient_id))
    care_plan_id = UUID(body["outcome"]["carePlanId"])
    assert len(repo.list(Task, care_plan_id=care_plan_id)) == 2


def test_complete_requires_diagnosed_by_when_recording():
    client, repo = _client_and_repo()
    _waiting_patient(repo)
    called = client.post("/api/staff/queue/call-next", json={"ownerId": str(uuid4())}).json()

    response = client.post(
        f"/api/staff/appointments/{called['appointmentId']}/complete",
        json={"conditions": ["flu"], "serviceTypeIds": []},  # conditions but no diagnosedBy
    )

    assert response.status_code == 422


def test_complete_with_unknown_service_type_leaves_visit_open():
    client, repo = _client_and_repo()
    _waiting_patient(repo)
    called = client.post("/api/staff/queue/call-next", json={"ownerId": str(uuid4())}).json()

    response = client.post(
        f"/api/staff/appointments/{called['appointmentId']}/complete",
        json={"diagnosedBy": called["ownerId"], "serviceTypeIds": [str(uuid4())]},
    )

    assert response.status_code == 422
    # the visit was NOT closed - a second (valid) complete still works
    ok = client.post(f"/api/staff/appointments/{called['appointmentId']}/complete")
    assert ok.status_code == 200
    assert ok.json()["status"] == "DONE"


# ---- /service-types ---------------------------------------------------------------------------


def test_service_types_lists_the_seeded_orderable_tests():
    client, _ = _client_and_repo()

    response = client.get("/api/staff/service-types")

    assert response.status_code == 200
    types = response.json()["serviceTypes"]
    assert len(types) == len(ARRIVAL_SERVICE_TYPES)
    codes = {t["code"] for t in types}
    assert "BLOOD_TEST" in codes and "XRAY" in codes


# ---- task lifecycle: confirm-payment (FR-05) + scan (FR-17) -----------------------------------


def _locked_task(repo: InMemoryRepository) -> tuple[str, str, str]:
    """Seed a LOCKED/UNPAID task + patient (scannable code). Returns (taskId, ownerId, code)."""
    patient = repo.save(Patient(full_name="", patient_code="P-TEST0001"))
    owner_id = uuid4()
    plan = repo.save(CarePlan(patient_id=patient.id, diagnosis_id=uuid4()))
    task = repo.save(
        Task(
            care_plan_id=plan.id,
            service_order_id=uuid4(),
            owner_id=owner_id,
            execution_status=ExecutionStatus.LOCKED,
            payment_status=PaymentStatus.UNPAID,
        )
    )
    return str(task.id), str(owner_id), patient.patient_code


def test_confirm_payment_unlocks_task_to_pending():
    client, repo = _client_and_repo()
    task_id, _owner, _code = _locked_task(repo)

    response = client.post(
        f"/api/staff/tasks/{task_id}/confirm-payment", json={"confirmedBy": str(uuid4())}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["executionStatus"] == "PENDING"
    assert body["paymentStatus"] == "PAID"


def test_confirm_payment_rejects_unauthorised_role():
    client, repo = _client_and_repo()
    task_id, _owner, _code = _locked_task(repo)

    response = client.post(
        f"/api/staff/tasks/{task_id}/confirm-payment",
        json={"confirmedBy": str(uuid4()), "actorRole": "role_doctor"},  # not authorised (BR-11)
    )

    assert response.status_code == 409


def test_confirm_payment_404_for_unknown_task():
    client, _ = _client_and_repo()

    response = client.post(
        f"/api/staff/tasks/{uuid4()}/confirm-payment", json={"confirmedBy": str(uuid4())}
    )

    assert response.status_code == 404


def test_scan_advances_paid_task_to_in_progress():
    client, repo = _client_and_repo()
    task_id, owner_id, code = _locked_task(repo)
    client.post(f"/api/staff/tasks/{task_id}/confirm-payment", json={"confirmedBy": str(uuid4())})

    response = client.post(
        f"/api/staff/tasks/{task_id}/scan", json={"scannedBy": owner_id, "patientCode": code}
    )

    assert response.status_code == 200
    assert response.json()["executionStatus"] == "IN_PROGRESS"


def test_scan_rejects_locked_task_before_payment():
    client, repo = _client_and_repo()
    task_id, owner_id, code = _locked_task(repo)  # still LOCKED, not paid

    response = client.post(
        f"/api/staff/tasks/{task_id}/scan", json={"scannedBy": owner_id, "patientCode": code}
    )

    assert response.status_code == 409


def test_scan_rejects_non_owner():
    client, repo = _client_and_repo()
    task_id, _owner, code = _locked_task(repo)
    client.post(f"/api/staff/tasks/{task_id}/confirm-payment", json={"confirmedBy": str(uuid4())})

    response = client.post(
        f"/api/staff/tasks/{task_id}/scan",
        json={"scannedBy": str(uuid4()), "patientCode": code},  # not the task owner (BR-26)
    )

    assert response.status_code == 409


def test_scan_rejects_wrong_patient_code():
    client, repo = _client_and_repo()
    task_id, owner_id, _code = _locked_task(repo)
    client.post(f"/api/staff/tasks/{task_id}/confirm-payment", json={"confirmedBy": str(uuid4())})

    response = client.post(
        f"/api/staff/tasks/{task_id}/scan",
        json={"scannedBy": owner_id, "patientCode": "P-WRONG999"},
    )

    assert response.status_code == 409


def _in_progress_task(client, repo) -> tuple[str, str]:
    """Drive a task LOCKED -> PENDING -> IN_PROGRESS. Returns (taskId, ownerId)."""
    task_id, owner_id, code = _locked_task(repo)
    client.post(f"/api/staff/tasks/{task_id}/confirm-payment", json={"confirmedBy": str(uuid4())})
    client.post(
        f"/api/staff/tasks/{task_id}/scan", json={"scannedBy": owner_id, "patientCode": code}
    )
    return task_id, owner_id


def test_complete_task_marks_it_done():
    client, repo = _client_and_repo()
    task_id, owner_id = _in_progress_task(client, repo)

    response = client.post(
        f"/api/staff/tasks/{task_id}/complete", json={"completedBy": owner_id}
    )

    assert response.status_code == 200
    assert response.json()["executionStatus"] == "DONE"


def test_complete_task_rejects_non_owner():
    client, repo = _client_and_repo()
    task_id, _owner_id = _in_progress_task(client, repo)

    response = client.post(
        f"/api/staff/tasks/{task_id}/complete", json={"completedBy": str(uuid4())}
    )

    assert response.status_code == 409


def test_complete_task_rejects_task_not_in_progress():
    client, repo = _client_and_repo()
    task_id, owner_id, _code = _locked_task(repo)  # still LOCKED, never started
    client.post(f"/api/staff/tasks/{task_id}/confirm-payment", json={"confirmedBy": str(uuid4())})

    response = client.post(
        f"/api/staff/tasks/{task_id}/complete", json={"completedBy": owner_id}  # only PENDING
    )

    assert response.status_code == 409


def test_complete_task_404_for_unknown_task():
    client, _ = _client_and_repo()

    response = client.post(
        f"/api/staff/tasks/{uuid4()}/complete", json={"completedBy": str(uuid4())}
    )

    assert response.status_code == 404

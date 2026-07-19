"""HTTP tests for the coordinator console backend (FR-09 / FR-10): snapshot, approval queue,
trigger, approve, reject.

Mounts the coordinator router over an in-memory repo, same pattern as `test_staff_routes.py`.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from vaic.api.coordinator_routes import build_coordinator_router
from vaic.models import (
    CarePlan,
    CarePlanStatus,
    ExecutionStatus,
    Patient,
    PaymentStatus,
    Resource,
    ResourceType,
    Task,
)
from vaic.state import InMemoryRepository

DEPT = UUID("00000000-0000-0000-0000-0000000000e0")


def _resource(repo, *, available=True):
    return repo.save(
        Resource(type=ResourceType.EQUIPMENT, department_id=DEPT, is_available=available)
    )


def _patient_task_on(repo, owner_id, *, duration=20):
    patient = repo.save(Patient(full_name="Synthetic", patient_code="PT-X", phone="0000000000"))
    plan = repo.save(
        CarePlan(patient_id=patient.id, diagnosis_id=uuid4(), status=CarePlanStatus.ACTIVE)
    )
    return repo.save(
        Task(
            care_plan_id=plan.id,
            service_order_id=uuid4(),
            owner_id=owner_id,
            execution_status=ExecutionStatus.PENDING,
            payment_status=PaymentStatus.PAID,
            estimated_duration_min=duration,
        )
    )


def _client(n_patients, *, alternates=1):
    repo = InMemoryRepository()
    failed = _resource(repo)
    alts = [_resource(repo) for _ in range(alternates)]
    tasks = [_patient_task_on(repo, failed.id) for _ in range(n_patients)]
    app = FastAPI()
    app.include_router(build_coordinator_router(repo))
    return TestClient(app), repo, failed, alts, tasks


def test_snapshot_endpoint_reports_load():
    client, repo, failed, alts, tasks = _client(3)
    res = client.get("/coordinator/snapshot")
    assert res.status_code == 200
    body = res.json()
    failed_cell = next(o for o in body["owners"] if o["ownerId"] == str(failed.id))
    assert failed_cell["queueDepth"] == 3 and failed_cell["loadMinutes"] == 60
    assert body["busiestOwnerId"] == str(failed.id)


def test_trigger_small_disruption_auto_resolves():
    client, repo, failed, alts, tasks = _client(3, alternates=1)
    res = client.post("/coordinator/disruptions", json={"resourceId": str(failed.id)})
    assert res.status_code == 200
    body = res.json()
    assert body["tier"] == "auto" and body["executed"] is True
    assert body["status"] == "AUTO_RESOLVED"


def test_trigger_unknown_resource_is_404():
    client, repo, failed, alts, tasks = _client(1)
    res = client.post("/coordinator/disruptions", json={"resourceId": str(uuid4())})
    assert res.status_code == 404


def test_large_disruption_appears_in_approval_queue_then_approve():
    client, repo, failed, alts, tasks = _client(7, alternates=2)
    trigger = client.post("/coordinator/disruptions", json={"resourceId": str(failed.id)})
    assert trigger.json()["tier"] == "approval_required"

    queue = client.get("/coordinator/disruptions").json()
    assert len(queue["pendingApproval"]) == 1
    did = queue["pendingApproval"][0]["disruptionId"]

    approve = client.post(
        f"/coordinator/disruptions/{did}/approve", json={"decidedBy": str(uuid4())}
    )
    assert approve.status_code == 200
    assert approve.json()["executed"] is True and approve.json()["status"] == "APPROVED"
    # queue now empty
    assert client.get("/coordinator/disruptions").json()["pendingApproval"] == []


def test_reject_keeps_plan_and_empties_queue():
    client, repo, failed, alts, tasks = _client(7, alternates=2)
    trigger = client.post("/coordinator/disruptions", json={"resourceId": str(failed.id)})
    did = trigger.json()["disruptionId"]

    reject = client.post(
        f"/coordinator/disruptions/{did}/reject", json={"decidedBy": str(uuid4())}
    )
    assert reject.status_code == 200 and reject.json()["status"] == "REJECTED"
    # original plan intact: every task still owned by the failed resource
    assert all(repo.get(Task, t.id).owner_id == failed.id for t in tasks)


def test_approve_unknown_disruption_is_409():
    client, repo, failed, alts, tasks = _client(1)
    res = client.post(
        f"/coordinator/disruptions/{uuid4()}/approve", json={"decidedBy": str(uuid4())}
    )
    assert res.status_code == 409

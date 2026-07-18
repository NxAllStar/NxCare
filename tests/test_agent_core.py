"""Agent-core spine: closed action space, constraint checker, audit log (TASK-004)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel

from vaic.agents.core import ActionExecutor
from vaic.models import (
    ExecutionStatus,
    PaymentStatus,
    Resource,
    ResourceType,
    Slot,
    Task,
)
from vaic.state import InMemoryRepository
from vaic.tools import Action, AuditLog, ConstraintChecker, Tool, ToolRegistry

# ---- lightweight tools that exercise the spine (domain tools come in later tasks) --------------

class StartTaskIn(BaseModel):
    task_id: UUID
    actor_id: UUID


class ScanIn(BaseModel):
    task_id: UUID
    scanned_by: UUID
    patient_id: UUID


class AllocateIn(BaseModel):
    task_id: UUID
    resource_id: UUID
    start: datetime


class OrderIn(BaseModel):
    diagnosis_id: UUID
    service_type_id: UUID
    ordered_by: UUID
    actor_role: str


class ReplanIn(BaseModel):
    blast_radius: int = 0
    approved: bool = False


class NoopIn(BaseModel):
    value: int  # required, to test schema validation


def _set_in_progress(p, repo):
    task = repo.get(Task, p.task_id)
    task.execution_status = ExecutionStatus.IN_PROGRESS
    repo.save(task)
    return {"task_id": str(p.task_id)}


def _build():
    repo = InMemoryRepository()
    reg = ToolRegistry()
    reg.register(Tool("start_task", StartTaskIn, _set_in_progress))
    reg.register(Tool("scan_patient", ScanIn, _set_in_progress))
    reg.register(Tool("allocate_slot", AllocateIn,
                      lambda p, r: {"slot": str(r.save(
                          Slot(patient_id=uuid4(), task_id=p.task_id, owner_id=p.resource_id,
                               start=p.start)).id)}))
    reg.register(Tool("create_service_order", OrderIn, lambda p, r: {"ok": True}))
    reg.register(Tool("execute_replan", ReplanIn, lambda p, r: {"replanned": True}))
    reg.register(Tool("noop", NoopIn, lambda p, r: {"value": p.value}))
    audit = AuditLog(repo)
    ex = ActionExecutor(repo, reg, ConstraintChecker(repo, replan_threshold=5), audit)
    return repo, ex, audit


def _task(repo, **kw) -> Task:
    base = dict(care_plan_id=uuid4(), service_order_id=uuid4(), owner_id=uuid4())
    base.update(kw)
    return repo.save(Task(**base))


def test_unknown_tool_is_outside_the_action_space():
    repo, ex, audit = _build()
    res = ex.execute(Action(tool="drop_database", actor="agent-core-dev"))
    assert res.allowed is False and "action space" in res.reason
    assert audit.entries()[-1].action == "BLOCKED:drop_database"


def test_start_locked_task_is_blocked_and_not_executed():
    repo, ex, audit = _build()
    owner = uuid4()
    t = _task(repo, owner_id=owner, payment_status=PaymentStatus.UNPAID,
              execution_status=ExecutionStatus.LOCKED)
    res = ex.execute(Action(tool="start_task", actor="journey-dev",
                            params={"task_id": t.id, "actor_id": owner}))
    assert res.allowed is False and "LOCKED" in res.reason
    # side effect must NOT be applied when blocked
    assert repo.get(Task, t.id).execution_status is ExecutionStatus.LOCKED


def test_start_paid_pending_task_succeeds():
    repo, ex, _ = _build()
    owner = uuid4()
    t = _task(repo, owner_id=owner, payment_status=PaymentStatus.PAID,
              execution_status=ExecutionStatus.PENDING)
    res = ex.execute(Action(tool="start_task", actor="journey-dev",
                            params={"task_id": t.id, "actor_id": owner}))
    assert res.allowed and res.ok
    assert repo.get(Task, t.id).execution_status is ExecutionStatus.IN_PROGRESS


def test_start_task_wrong_owner_blocked():
    repo, ex, _ = _build()
    t = _task(repo, payment_status=PaymentStatus.PAID, execution_status=ExecutionStatus.PENDING)
    res = ex.execute(Action(tool="start_task", actor="x",
                            params={"task_id": t.id, "actor_id": uuid4()}))
    assert res.allowed is False and "owner" in res.reason


def test_scan_locked_and_wrong_owner_blocked_then_ok():
    repo, ex, _ = _build()
    owner, patient = uuid4(), uuid4()
    locked = _task(repo, owner_id=owner, payment_status=PaymentStatus.UNPAID,
                   execution_status=ExecutionStatus.LOCKED)
    assert ex.execute(Action(tool="scan_patient", actor="x",
                             params={"task_id": locked.id, "scanned_by": owner,
                                     "patient_id": patient})).allowed is False
    paid = _task(repo, owner_id=owner, payment_status=PaymentStatus.PAID,
                 execution_status=ExecutionStatus.PENDING)
    assert ex.execute(Action(tool="scan_patient", actor="x",
                             params={"task_id": paid.id, "scanned_by": uuid4(),
                                     "patient_id": patient})).allowed is False  # wrong owner
    ok = ex.execute(Action(tool="scan_patient", actor="x",
                           params={"task_id": paid.id, "scanned_by": owner, "patient_id": patient}))
    assert ok.allowed and ok.ok


def test_allocate_to_unavailable_resource_blocked():
    repo, ex, _ = _build()
    dept = uuid4()
    closed = repo.save(
        Resource(type=ResourceType.EQUIPMENT, department_id=dept, is_available=False))
    t = _task(repo)
    res = ex.execute(Action(tool="allocate_slot", actor="careplan-dev",
                            params={"task_id": t.id, "resource_id": closed.id,
                                    "start": datetime.now(UTC)}))
    assert res.allowed is False and "unavailable" in res.reason


def test_create_service_order_requires_doctor():
    repo, ex, _ = _build()
    base = {"diagnosis_id": uuid4(), "service_type_id": uuid4(), "ordered_by": uuid4()}
    blocked = ex.execute(Action(tool="create_service_order", actor="agent-core-dev",
                                params={**base, "actor_role": "role_coordinator"}))
    assert blocked.allowed is False and "doctor" in blocked.reason
    ok = ex.execute(Action(tool="create_service_order", actor="role_doctor",
                           params={**base, "actor_role": "role_doctor"}))
    assert ok.allowed and ok.ok


def test_replan_tiered_autonomy():
    repo, ex, _ = _build()
    over = ex.execute(Action(tool="execute_replan", actor="disruption",
                             params={"blast_radius": 30, "approved": False}))
    assert over.allowed is False and "approval" in over.reason
    approved = ex.execute(Action(tool="execute_replan", actor="disruption",
                                 params={"blast_radius": 30, "approved": True}))
    assert approved.allowed and approved.ok
    small = ex.execute(Action(tool="execute_replan", actor="disruption",
                              params={"blast_radius": 3}))
    assert small.allowed and small.ok


def test_tool_input_is_schema_validated():
    repo, ex, _ = _build()
    res = ex.execute(Action(tool="noop", actor="x", params={"value": "not-an-int-and-required?"}))
    # "not-an-int" -> pydantic int coercion fails -> ToolError -> allowed but not ok
    res2 = ex.execute(Action(tool="noop", actor="x", params={}))  # missing required
    assert res.ok is False or res2.ok is False
    assert res2.allowed is True and res2.ok is False and "invalid" in res2.reason


def test_audit_is_append_only():
    repo, ex, audit = _build()
    assert not hasattr(audit, "update")
    assert not hasattr(audit, "delete")
    before = len(audit.entries())
    ex.execute(Action(tool="execute_replan", actor="disruption", params={"blast_radius": 1}))
    assert len(audit.entries()) == before + 1

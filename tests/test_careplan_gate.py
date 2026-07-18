"""FR-05 proceed gate / paid flag (TASK-008).

AC-05.1: an UNPAID task never appears in owner queue/load/ETA.
AC-05.2 / AC-05.4: an authorised source confirms payment -> Payment.status PAID,
confirmed_by/confirmed_at recorded, task LOCKED -> PENDING, enqueued at its allocated slot.
AC-05.3 (negative): an agent trying to start_task on an UNPAID task is blocked and audited - the
wiring is proven with a task this module produced, routed through the shared ActionExecutor.
BR-11: only an authorised source flips PAID; no agent flips it.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel

from vaic.agents.careplan.gate import (
    DEFAULT_AUTHORISED_PAYMENT_ROLES,
    build_confirm_payment_tool,
    is_authorised_payment_confirmer,
)
from vaic.agents.core import ActionExecutor
from vaic.models import (
    ExecutionStatus,
    Payment,
    PaymentStatus,
    PaymentSubjectType,
    Slot,
    Task,
)
from vaic.state import InMemoryRepository, owner_load_minutes, owner_queue
from vaic.tools import Action, AuditLog, ConstraintChecker, Tool, ToolRegistry


class _StartTaskStubIn(BaseModel):
    """A minimal stand-in for the (journey-dev-owned) start_task tool, registered ONLY so this
    test can prove a LOCKED task this module produced is blocked by the shared constraint checker
    when something tries to start it. Does not implement or alter journey-dev's real tool.
    """

    task_id: UUID
    actor_id: UUID


def _set_in_progress(params: _StartTaskStubIn, repo) -> dict:
    task = repo.get(Task, params.task_id)
    task.execution_status = ExecutionStatus.IN_PROGRESS
    repo.save(task)
    return {"task_id": str(params.task_id)}


def _build(with_start_task_stub: bool = False):
    repo = InMemoryRepository()
    registry = ToolRegistry()
    registry.register(build_confirm_payment_tool())
    if with_start_task_stub:
        registry.register(Tool("start_task", _StartTaskStubIn, _set_in_progress))
    audit = AuditLog(repo)
    executor = ActionExecutor(repo, registry, ConstraintChecker(repo), audit)
    return repo, executor, audit


def _locked_task(repo, owner_id, **kw) -> Task:
    base = dict(care_plan_id=uuid4(), service_order_id=uuid4(), owner_id=owner_id,
                execution_status=ExecutionStatus.LOCKED, payment_status=PaymentStatus.UNPAID,
                estimated_duration_min=15, sequence_index=0)
    base.update(kw)
    return repo.save(Task(**base))


def test_ac_05_1_unpaid_task_excluded_from_queue_and_load():
    repo, _, _ = _build()
    owner = uuid4()
    _locked_task(repo, owner, sequence_index=0, estimated_duration_min=99)
    paid = repo.save(Task(care_plan_id=uuid4(), service_order_id=uuid4(), owner_id=owner,
                           execution_status=ExecutionStatus.PENDING,
                           payment_status=PaymentStatus.PAID,
                           estimated_duration_min=10, sequence_index=1))

    q = owner_queue(repo, owner)
    assert [t.id for t in q] == [paid.id]
    assert owner_load_minutes(repo, owner) == 10  # the LOCKED task's 99 minutes never count


def test_ac_05_2_and_05_4_authorised_confirmation_unlocks_and_enqueues_at_allocated_slot():
    repo, executor, audit = _build()
    owner = uuid4()
    task = _locked_task(repo, owner)
    slot = repo.save(Slot(task_id=task.id, owner_id=owner, start=task.created_at))
    staff_id = uuid4()

    before = len(audit.entries())
    role = next(iter(DEFAULT_AUTHORISED_PAYMENT_ROLES))
    result = executor.execute(
        Action(
            tool="confirm_payment",
            actor="front-desk-staff",
            params={"task_id": task.id, "actor_role": role, "confirmed_by": staff_id},
        )
    )

    assert result.allowed and result.ok
    assert len(audit.entries()) == before + 1

    updated = repo.get(Task, task.id)
    assert updated.execution_status is ExecutionStatus.PENDING
    assert updated.payment_status is PaymentStatus.PAID

    payments = repo.list(Payment, subject_type=PaymentSubjectType.TASK, subject_id=task.id)
    assert len(payments) == 1
    assert payments[0].status is PaymentStatus.PAID
    assert payments[0].confirmed_by == staff_id
    assert payments[0].confirmed_at is not None

    # enters the queue at its allocated slot
    q = owner_queue(repo, owner)
    assert [t.id for t in q] == [task.id]
    assert repo.get(Slot, slot.id).task_id == task.id


def test_br_11_unauthorised_actor_cannot_flip_paid_and_is_audited():
    repo, executor, audit = _build()
    task = _locked_task(repo, uuid4())
    before = len(audit.entries())

    for bad_role in ("role_patient", "agent:disruption", "role_journey_agent"):
        result = executor.execute(
            Action(
                tool="confirm_payment",
                actor=bad_role,
                params={"task_id": task.id, "actor_role": bad_role, "confirmed_by": uuid4()},
            )
        )
        assert result.allowed is True  # no checker rule for this tool...
        assert result.ok is False  # ...but the handler itself refuses (BR-11)
        assert "authorised" in result.reason

    assert repo.get(Task, task.id).execution_status is ExecutionStatus.LOCKED
    assert repo.list(Payment, subject_id=task.id) == []
    assert len(audit.entries()) == before + 3
    assert all(e.action == "FAILED:confirm_payment" for e in audit.entries()[before:])


def test_cannot_confirm_payment_twice():
    repo, executor, _ = _build()
    task = _locked_task(repo, uuid4())
    role = next(iter(DEFAULT_AUTHORISED_PAYMENT_ROLES))
    first = executor.execute(
        Action(tool="confirm_payment", actor="staff",
               params={"task_id": task.id, "actor_role": role, "confirmed_by": uuid4()})
    )
    assert first.ok
    second = executor.execute(
        Action(tool="confirm_payment", actor="staff",
               params={"task_id": task.id, "actor_role": role, "confirmed_by": uuid4()})
    )
    assert second.ok is False
    assert "LOCKED" in second.reason


def test_confirm_payment_authorised_predicate_is_swappable():
    only_billing_system = lambda role: role == "hospital_billing_system"  # noqa: E731
    tool = build_confirm_payment_tool(is_authorised=only_billing_system)
    registry = ToolRegistry()
    registry.register(tool)
    repo = InMemoryRepository()
    audit = AuditLog(repo)
    executor = ActionExecutor(repo, registry, ConstraintChecker(repo), audit)
    task = _locked_task(repo, uuid4())

    default_role = next(iter(DEFAULT_AUTHORISED_PAYMENT_ROLES))
    refused = executor.execute(
        Action(tool="confirm_payment", actor="staff",
               params={"task_id": task.id, "actor_role": default_role, "confirmed_by": uuid4()})
    )
    assert refused.ok is False  # the default role no longer authorises under the swapped predicate

    ok = executor.execute(
        Action(tool="confirm_payment", actor="hospital-system",
               params={"task_id": task.id, "actor_role": "hospital_billing_system",
                       "confirmed_by": uuid4()})
    )
    assert ok.ok


def test_default_predicate_matches_the_documented_default_set():
    assert is_authorised_payment_confirmer("role_staff") is True
    assert is_authorised_payment_confirmer("role_coordinator") is True
    assert is_authorised_payment_confirmer("role_patient") is False
    assert is_authorised_payment_confirmer("agent:coordinator") is False


def test_ac_05_3_start_task_on_unpaid_task_blocked_and_audited():
    repo, executor, audit = _build(with_start_task_stub=True)
    owner = uuid4()
    task = _locked_task(repo, owner)
    before = len(audit.entries())

    result = executor.execute(
        Action(tool="start_task", actor="journey-agent",
               params={"task_id": task.id, "actor_id": owner})
    )

    assert result.allowed is False
    assert "LOCKED" in result.reason
    assert repo.get(Task, task.id).execution_status is ExecutionStatus.LOCKED
    assert len(audit.entries()) == before + 1
    assert audit.entries()[-1].action == "BLOCKED:start_task"

"""FR-04 Care Plan Agent generation, wired through the ActionExecutor spine (TASK-008).

Covers: tasks are created and slotted through the guarded spine (constraint-checked, audited),
the CarePlan reaches ACTIVE ("ready" state for FR-06 hand-off), and BR-09 (duration always comes
from the injected estimator, mocked here - never a real forecast/LLM call).

TASK-008 fix round (code-review/security-review MUST-FIX items):
- cM4: owner_resolver is resolved exactly once per order and threaded to the Task, never
  re-resolved independently for duration estimation vs. task assignment.
- cM5: an empty candidate list for one task fails that task's allocation cleanly - the CarePlan
  stays DRAFT, no orphan ACTIVE plan, and the failure is audited.
- cM6 / sM1: CarePlan creation, Task creation, and the DRAFT->ACTIVE transition are routed through
  the ActionExecutor spine and are each audited (FR-13).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from vaic.agents.careplan.care_plan import (
    build_activate_care_plan_tool,
    build_create_care_plan_tool,
    build_create_task_tool,
    generate_care_plan,
)
from vaic.agents.careplan.slots import SlotCandidate, build_allocate_slot_tool
from vaic.agents.core import ActionExecutor
from vaic.models import (
    CarePlan,
    CarePlanStatus,
    Diagnosis,
    ExecutionStatus,
    PaymentStatus,
    Resource,
    ResourceType,
    ServiceOrder,
    ServiceType,
    Task,
)
from vaic.state import InMemoryRepository
from vaic.tools import AuditLog, ConstraintChecker, ToolRegistry


def _build(repo=None):
    repo = repo or InMemoryRepository()
    registry = ToolRegistry()
    registry.register(build_create_care_plan_tool())
    registry.register(build_create_task_tool())
    registry.register(build_allocate_slot_tool())
    registry.register(build_activate_care_plan_tool())
    audit = AuditLog(repo)
    executor = ActionExecutor(repo, registry, ConstraintChecker(repo), audit)
    return repo, executor, audit


def _order_and_type(repo, code: str, diagnosis_id, **type_kw):
    st = repo.save(ServiceType(code=code, display_label=code, **type_kw))
    order = repo.save(ServiceOrder(diagnosis_id=diagnosis_id, service_type_id=st.id,
                                    ordered_by=uuid4()))
    return order, st


def test_generate_care_plan_creates_one_task_per_order_and_activates_the_plan():
    repo, executor, audit = _build()
    diagnosis = repo.save(Diagnosis(appointment_id=uuid4(), diagnosed_by=uuid4()))
    room = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                               capacity_per_hour=5))

    blood, blood_st = _order_and_type(repo, "BLOOD_TEST", diagnosis.id,
                                       requires_fasting=True, turnaround_minutes=45)
    ultra, ultra_st = _order_and_type(repo, "ULTRASOUND", diagnosis.id)
    xray, xray_st = _order_and_type(repo, "XRAY", diagnosis.id)

    calls: list[str] = []  # proves duration always flows through the injected estimator (BR-09)

    def fake_duration_estimator(service_type, owner_id):
        calls.append(service_type.code)
        return {"BLOOD_TEST": 10, "ULTRASOUND": 40, "XRAY": 15}[service_type.code]

    result = generate_care_plan(
        repo,
        executor,
        actor="care-plan-agent",
        patient_id=uuid4(),
        diagnosis=diagnosis,
        orders_with_types=[(blood, blood_st), (ultra, ultra_st), (xray, xray_st)],
        estimate_duration=fake_duration_estimator,
        owner_resolver=lambda order, st: room.id,
        candidates_for=lambda task, seq: [
            SlotCandidate(resource_id=room.id, start=datetime.now(UTC))
        ],
    )

    assert calls == ["BLOOD_TEST", "ULTRASOUND", "XRAY"]  # every order got a real estimate
    assert len(result.tasks) == 3  # BR-07: one task per order, never more, never fewer
    assert {repo.get(ServiceOrder, t.service_order_id).id for t in result.tasks} == {
        blood.id, ultra.id, xray.id
    }
    # AC-04.1 ordering carried through to persisted tasks
    by_type = {repo.get(ServiceType, repo.get(ServiceOrder, t.service_order_id).service_type_id)
               .code: t.sequence_index for t in result.tasks}
    assert by_type["BLOOD_TEST"] < by_type["XRAY"] < by_type["ULTRASOUND"]

    assert result.all_slotted
    assert result.care_plan.status is CarePlanStatus.ACTIVE
    assert repo.get(CarePlan, result.care_plan.id).status is CarePlanStatus.ACTIVE

    # every task starts LOCKED/UNPAID - the proceed gate (FR-05) has not been crossed yet
    for task in result.tasks:
        assert task.execution_status is ExecutionStatus.LOCKED
        assert task.payment_status is PaymentStatus.UNPAID

    # slot allocation was constraint-checked and audited, not a bare repo write
    assert any(e.action == "allocate_slot" for e in audit.entries())


def test_generate_care_plan_never_adds_a_service_beyond_the_single_order():
    repo, executor, _ = _build()
    diagnosis = repo.save(Diagnosis(appointment_id=uuid4(), diagnosed_by=uuid4()))
    room = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                               capacity_per_hour=5))
    ultra, ultra_st = _order_and_type(repo, "ULTRASOUND", diagnosis.id)

    result = generate_care_plan(
        repo,
        executor,
        actor="care-plan-agent",
        patient_id=uuid4(),
        diagnosis=diagnosis,
        orders_with_types=[(ultra, ultra_st)],
        estimate_duration=lambda st, owner_id: 20,
        owner_resolver=lambda order, st: room.id,
        candidates_for=lambda task, seq: [
            SlotCandidate(resource_id=room.id, start=datetime.now(UTC))
        ],
    )

    assert len(result.tasks) == 1
    assert repo.list(Task, care_plan_id=result.care_plan.id) == result.tasks


def test_cm4_owner_resolved_once_and_threaded_to_the_task():
    """A stateful/round-robin owner_resolver called TWICE (once for duration estimation, once for
    task assignment) would disagree between calls. This proves it is called exactly once per order
    and the SAME resolved owner both estimates the duration and owns the persisted Task."""
    repo, executor, _ = _build()
    diagnosis = repo.save(Diagnosis(appointment_id=uuid4(), diagnosed_by=uuid4()))
    room_a = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                                 capacity_per_hour=5))
    room_b = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                                 capacity_per_hour=5))
    ultra, ultra_st = _order_and_type(repo, "ULTRASOUND", diagnosis.id)

    owners = iter([room_a.id, room_b.id])
    calls: list = []

    def owner_resolver(order, st):
        owner = next(owners)
        calls.append(owner)
        return owner

    result = generate_care_plan(
        repo,
        executor,
        actor="care-plan-agent",
        patient_id=uuid4(),
        diagnosis=diagnosis,
        orders_with_types=[(ultra, ultra_st)],
        estimate_duration=lambda st, owner_id: 20,
        owner_resolver=owner_resolver,
        candidates_for=lambda task, seq: [
            SlotCandidate(resource_id=task.owner_id, start=datetime.now(UTC))
        ],
    )

    assert len(calls) == 1  # resolved exactly once (cM4), never re-resolved for the Task
    assert result.tasks[0].owner_id == calls[0]
    assert result.sequenced[0].owner_id == calls[0]


def test_cm5_empty_candidates_reports_failure_cleanly_no_orphan_active_plan():
    repo, executor, audit = _build()
    diagnosis = repo.save(Diagnosis(appointment_id=uuid4(), diagnosed_by=uuid4()))
    room = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                               capacity_per_hour=5))
    ultra, ultra_st = _order_and_type(repo, "ULTRASOUND", diagnosis.id)

    result = generate_care_plan(
        repo,
        executor,
        actor="care-plan-agent",
        patient_id=uuid4(),
        diagnosis=diagnosis,
        orders_with_types=[(ultra, ultra_st)],
        estimate_duration=lambda st, owner_id: 20,
        owner_resolver=lambda order, st: room.id,
        candidates_for=lambda task, seq: [],  # no candidates at all - must not crash
    )

    assert result.all_slotted is False
    assert len(result.tasks) == 1  # the Task IS persisted - not rolled back, just not activated
    assert result.care_plan.status is CarePlanStatus.DRAFT  # never promoted: no orphan ACTIVE plan
    assert repo.get(CarePlan, result.care_plan.id).status is CarePlanStatus.DRAFT

    failed = [e for e in audit.entries() if e.action == "FAILED:allocate_slot"]
    assert len(failed) == 1
    assert "no slot candidates" in failed[0].reasoning
    assert not any(e.action == "activate_care_plan" for e in audit.entries())


def test_cm6_sm1_plan_and_task_writes_are_routed_through_the_executor_and_audited():
    repo, executor, audit = _build()
    diagnosis = repo.save(Diagnosis(appointment_id=uuid4(), diagnosed_by=uuid4()))
    room = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                               capacity_per_hour=5))
    ultra, ultra_st = _order_and_type(repo, "ULTRASOUND", diagnosis.id)
    before = len(audit.entries())

    generate_care_plan(
        repo,
        executor,
        actor="care-plan-agent",
        patient_id=uuid4(),
        diagnosis=diagnosis,
        orders_with_types=[(ultra, ultra_st)],
        estimate_duration=lambda st, owner_id: 20,
        owner_resolver=lambda order, st: room.id,
        candidates_for=lambda task, seq: [
            SlotCandidate(resource_id=room.id, start=datetime.now(UTC))
        ],
    )

    actions = [e.action for e in audit.entries()[before:]]
    assert "create_care_plan" in actions  # cM6/sM1: no bare repo.save() for the plan
    assert "create_task" in actions  # ... nor for the task
    assert "allocate_slot" in actions
    assert "activate_care_plan" in actions  # ... nor for the DRAFT -> ACTIVE transition

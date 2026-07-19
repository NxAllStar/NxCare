"""Coordinator + Disruption tiered autonomy (TASK-010, FR-09 / FR-10).

Proves the acceptance criteria:
- AC-09.1 blast radius <= N auto-executes and notifies affected patients with a reason.
- AC-09.2 blast radius > N is proposed (PENDING_APPROVAL), not executed.
- AC-09.3 a rejected re-plan keeps the original plan and audits the rejection.
- AC-10.1 the Coordinator perceives a snapshot, delegates, and audits its reasoning.
- AC-10.2 an action outside the closed tool set is rejected by the spine.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from vaic.agents.core import (
    CoordinatorEvent,
    build_coordinator_stack,
    build_snapshot,
    compute_blast_radius,
)
from vaic.models import (
    CarePlan,
    CarePlanStatus,
    DisruptionEventType,
    DisruptionStatus,
    ExecutionStatus,
    Patient,
    PaymentStatus,
    Resource,
    ResourceType,
    Slot,
    Task,
)
from vaic.models.entities import _now
from vaic.state import InMemoryRepository
from vaic.tools import Action

DEPT = UUID("00000000-0000-0000-0000-0000000000d0")


def _resource(repo, *, available=True, rtype=ResourceType.EQUIPMENT):
    return repo.save(Resource(type=rtype, department_id=DEPT, is_available=available))


def _patient_task_on(repo, owner_id, *, duration=20):
    """One paid, PENDING task owned by `owner_id`, with its own patient and care plan."""
    patient = repo.save(
        Patient(full_name="Synthetic Patient", patient_code="PT-SYNTH", phone="0000000000")
    )
    plan = repo.save(
        CarePlan(patient_id=patient.id, diagnosis_id=uuid4(), status=CarePlanStatus.ACTIVE)
    )
    task = repo.save(
        Task(
            care_plan_id=plan.id,
            service_order_id=uuid4(),
            owner_id=owner_id,
            execution_status=ExecutionStatus.PENDING,
            payment_status=PaymentStatus.PAID,
            estimated_duration_min=duration,
        )
    )
    repo.save(Slot(patient_id=patient.id, task_id=task.id, owner_id=owner_id, start=_now()))
    return patient, plan, task


def _scenario(n_patients, *, threshold=5, alternates=1):
    repo = InMemoryRepository()
    failed = _resource(repo)
    alts = [_resource(repo) for _ in range(alternates)]
    tasks = [_patient_task_on(repo, failed.id)[2] for _ in range(n_patients)]
    stack = build_coordinator_stack(repo, threshold=threshold)
    return repo, failed, alts, tasks, stack


# ---- snapshot (FR-10 perceive) ------------------------------------------------------------------

def test_snapshot_reports_load_per_available_owner():
    repo, failed, alts, tasks, _ = _scenario(3, alternates=1)
    snapshot = build_snapshot(repo)
    failed_load = next(o for o in snapshot.owners if o.owner_id == failed.id)
    assert failed_load.queue_depth == 3
    assert failed_load.load_minutes == 60  # 3 x 20 minutes
    assert snapshot.busiest().owner_id == failed.id


def test_blast_radius_counts_distinct_patients_only():
    repo, failed, _, tasks, _ = _scenario(4)
    # a second paid task for an existing patient must NOT inflate the count
    extra_owner = failed.id
    plan_id = tasks[0].care_plan_id
    repo.save(
        Task(
            care_plan_id=plan_id,
            service_order_id=uuid4(),
            owner_id=extra_owner,
            execution_status=ExecutionStatus.PENDING,
            payment_status=PaymentStatus.PAID,
            estimated_duration_min=10,
        )
    )
    assert compute_blast_radius(repo, failed.id) == 4


# ---- FR-09 tiered autonomy ----------------------------------------------------------------------

def test_ac_09_1_small_blast_radius_auto_executes_and_notifies():
    repo, failed, alts, tasks, stack = _scenario(3, threshold=5, alternates=1)

    outcome = stack.disruption.handle(failed.id, event_type=DisruptionEventType.EQUIPMENT_FAILURE)

    assert outcome.tier == "auto" and outcome.executed is True
    assert outcome.status == DisruptionStatus.AUTO_RESOLVED.value
    # affected tasks were re-plated onto the available alternate
    assert all(repo.get(Task, t.id).owner_id == alts[0].id for t in tasks)
    # every affected patient got a timeline notification carrying a reason (AC-09.1)
    notes = _notifications(repo)
    assert len(notes) == 3
    assert all(n.reason for n in notes)


def test_ac_09_2_large_blast_radius_is_proposed_not_executed():
    repo, failed, alts, tasks, stack = _scenario(7, threshold=5, alternates=2)

    outcome = stack.disruption.handle(failed.id, event_type=DisruptionEventType.EQUIPMENT_FAILURE)

    assert outcome.tier == "approval_required" and outcome.executed is False
    assert outcome.status == DisruptionStatus.PENDING_APPROVAL.value
    # nothing moved: the original plan is intact until a human approves
    assert all(repo.get(Task, t.id).owner_id == failed.id for t in tasks)
    assert not _notifications(repo)


def test_ac_09_2_then_approve_executes_the_replan():
    repo, failed, alts, tasks, stack = _scenario(7, threshold=5, alternates=2)
    pending = stack.disruption.handle(failed.id)
    coordinator_id = uuid4()

    approved = stack.disruption.approve(pending.disruption_id, decided_by=coordinator_id)

    assert approved.executed is True
    assert approved.status == DisruptionStatus.APPROVED.value
    assert all(repo.get(Task, t.id).owner_id in {a.id for a in alts} for t in tasks)
    assert len(_notifications(repo)) == 7


def test_ac_09_3_reject_keeps_original_plan_and_audits():
    repo, failed, alts, tasks, stack = _scenario(7, threshold=5, alternates=2)
    pending = stack.disruption.handle(failed.id)
    coordinator_id = uuid4()

    rejected = stack.disruption.reject(pending.disruption_id, decided_by=coordinator_id)

    assert rejected.executed is False
    assert rejected.status == DisruptionStatus.REJECTED.value
    # original plan kept: every task still owned by the failed resource, nobody notified
    assert all(repo.get(Task, t.id).owner_id == failed.id for t in tasks)
    assert not _notifications(repo)
    # the rejection decision is on the append-only audit log (BR-18)
    actions = [e.action for e in stack.audit.entries()]
    assert any("REJECTED" in a for a in actions)


def test_replan_input_is_schema_validated_bad_params_do_not_execute():
    repo, failed, alts, tasks, stack = _scenario(3)
    # a hand-built action with a malformed resource id is rejected by the tool schema, not executed
    result = stack.executor.execute(
        Action(
            tool="execute_replan",
            actor="disruption",
            params={"resource_id": "not-a-uuid", "blast_radius": 1, "approved": False},
        )
    )
    assert result.allowed is True and result.ok is False and "invalid" in result.reason
    assert all(repo.get(Task, t.id).owner_id == failed.id for t in tasks)


# ---- FR-10 coordinator loop ---------------------------------------------------------------------

def test_ac_10_1_coordinator_perceives_delegates_and_audits():
    repo, failed, alts, tasks, stack = _scenario(3, threshold=5, alternates=1)

    results = stack.coordinator.handle(
        [CoordinatorEvent(kind="equipment_failure", resource_id=failed.id)]
    )

    assert len(results) == 1 and results[0].delegated is True
    assert results[0].disruption is not None and results[0].disruption.executed is True
    # the coordinator recorded its own reasoning before delegating (AC-10.1 / BR-18)
    coordinate_entries = [e for e in stack.audit.entries() if e.action.startswith("coordinate:")]
    assert coordinate_entries and coordinate_entries[0].reasoning


def test_ac_10_1_check_in_reads_snapshot_and_audits():
    repo, failed, alts, tasks, stack = _scenario(1, threshold=5, alternates=1)

    results = stack.coordinator.handle(
        [CoordinatorEvent(kind="check_in", resource_id=failed.id)]
    )

    assert len(results) == 1
    coordinate_entries = [e for e in stack.audit.entries() if e.action == "coordinate:check_in"]
    assert coordinate_entries and coordinate_entries[0].reasoning


def test_ac_10_2_action_outside_the_tool_set_is_rejected():
    repo, failed, alts, tasks, stack = _scenario(1)

    class OutOfSpaceBrain:
        def decide(self, event, snapshot):
            from vaic.agents.core.coordinator import CoordinatorDecision

            return CoordinatorDecision(
                reasoning="model proposed an unknown tool",
                action=Action(tool="drop_database", actor="coordinator"),
            )

    stack.coordinator._brain = OutOfSpaceBrain()
    results = stack.coordinator.handle([CoordinatorEvent(kind="check_in", resource_id=failed.id)])

    assert results[0].action_result is not None
    assert results[0].action_result.allowed is False
    assert "action space" in results[0].action_result.reason


def test_coordinator_batches_multiple_events():
    repo, failed, alts, tasks, stack = _scenario(2, threshold=5, alternates=1)
    events = [
        CoordinatorEvent(kind="check_in", resource_id=failed.id),
        CoordinatorEvent(kind="equipment_failure", resource_id=failed.id),
    ]
    results = stack.coordinator.handle(events)
    assert len(results) == 2  # BR-20: a batch of events processed in one pass


# ---- helpers ------------------------------------------------------------------------------------

def _notifications(repo):
    from vaic.models import Notification

    return repo.list(Notification)

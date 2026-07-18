"""FR-08 slot allocation (TASK-008).

AC-08.1: capacity available -> task gets a valid slot that does not clash with another owner.
AC-08.2 (negative): a closed room is blocked (BR-16, via the constraint checker) and
`allocate_task_slot` picks a different valid slot.

TASK-008 fix round (code-review/security-review MUST-FIX items):
- cM1: `capacity_per_hour` is an hourly throughput cap, not a concurrent-overlap cap.
- cM3: a task's real owner cannot be double-booked on a different resource.
- cM5: an empty candidate list is a graceful failure, never a crash.
- sec-m1 / BR-14: a non-positive duration is rejected before it can invert a slot.
- m2: a CANCELLED/DONE task's slot never blocks a new allocation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from vaic.agents.careplan.slots import SlotCandidate, allocate_task_slot, build_allocate_slot_tool
from vaic.agents.core import ActionExecutor
from vaic.models import ExecutionStatus, Resource, ResourceType, Slot, Task
from vaic.state import InMemoryRepository
from vaic.tools import AuditLog, ConstraintChecker, ToolRegistry


def _build():
    repo = InMemoryRepository()
    registry = ToolRegistry()
    registry.register(build_allocate_slot_tool())
    audit = AuditLog(repo)
    executor = ActionExecutor(repo, registry, ConstraintChecker(repo), audit)
    return repo, executor, audit


def _task(repo, **kw) -> Task:
    base = dict(care_plan_id=uuid4(), service_order_id=uuid4(), owner_id=uuid4(),
                estimated_duration_min=10)
    base.update(kw)
    return repo.save(Task(**base))


def test_ac_08_1_capacity_available_slot_assigned_without_clash():
    repo, executor, _ = _build()
    room = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                               capacity_per_hour=2))
    start = datetime(2026, 7, 18, 9, 0, tzinfo=UTC)
    task_a = _task(repo, owner_id=room.id, estimated_duration_min=10)
    task_b = _task(repo, owner_id=room.id, estimated_duration_min=10)

    res_a = allocate_task_slot(repo, executor, "care-plan-agent", task_a,
                                [SlotCandidate(resource_id=room.id, start=start)])
    assert res_a.ok
    res_b = allocate_task_slot(repo, executor, "care-plan-agent", task_b,
                                [SlotCandidate(resource_id=room.id, start=start)])
    assert res_b.ok  # capacity is 2/hour, two overlapping slots both fit

    slots = repo.list(Slot, owner_id=room.id)
    assert len(slots) == 2
    assert {s.task_id for s in slots} == {task_a.id, task_b.id}


def test_over_capacity_rejected_then_next_candidate_used():
    repo, executor, _ = _build()
    room = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                               capacity_per_hour=1))
    start = datetime(2026, 7, 18, 9, 0, tzinfo=UTC)
    later = start + timedelta(hours=2)

    task_a = _task(repo, owner_id=room.id, estimated_duration_min=10)
    task_b = _task(repo, owner_id=room.id, estimated_duration_min=10)

    assert allocate_task_slot(
        repo, executor, "care-plan-agent", task_a, [SlotCandidate(resource_id=room.id, start=start)]
    ).ok

    # same room, same overlapping window, capacity already full for task_a -> falls through to
    # the later candidate (AC-08.1's "no clash", proven by exercising the fallback path)
    res_b = allocate_task_slot(
        repo,
        executor,
        "care-plan-agent",
        task_b,
        [
            SlotCandidate(resource_id=room.id, start=start),
            SlotCandidate(resource_id=room.id, start=later),
        ],
    )
    assert res_b.ok
    slot_b = repo.list(Slot, task_id=task_b.id)[0]
    assert slot_b.start == later


def test_cm1_capacity_is_hourly_throughput_not_concurrent_overlap():
    """cM1: book capacity_per_hour+1 NON-overlapping slots in one clock hour; the last is rejected
    even though none of the bookings overlap each other in time - capacity_per_hour caps how many
    bookings START in the same hour, not how many are simultaneously in progress."""
    repo, executor, _ = _build()
    room = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                               capacity_per_hour=2))
    base = datetime(2026, 7, 18, 9, 0, tzinfo=UTC)

    for i in range(2):  # two 10-minute, back-to-back, non-overlapping bookings, same clock hour
        task = _task(repo, owner_id=room.id, estimated_duration_min=10)
        result = allocate_task_slot(
            repo, executor, "care-plan-agent", task,
            [SlotCandidate(resource_id=room.id, start=base + timedelta(minutes=i * 15))],
        )
        assert result.ok

    # a third booking, still 9:xx (same hour), still non-overlapping with the first two - capacity
    # is exhausted for the HOUR, so this is rejected purely on throughput, not on any time clash
    third = _task(repo, owner_id=room.id, estimated_duration_min=10)
    result = allocate_task_slot(
        repo, executor, "care-plan-agent", third,
        [SlotCandidate(resource_id=room.id, start=base + timedelta(minutes=45))],
    )
    assert result.ok is False
    assert "capacity" in result.reason
    assert repo.list(Slot, task_id=third.id) == []

    # the NEXT clock hour has fresh capacity
    fourth = _task(repo, owner_id=room.id, estimated_duration_min=10)
    result = allocate_task_slot(
        repo, executor, "care-plan-agent", fourth,
        [SlotCandidate(resource_id=room.id, start=base + timedelta(hours=1))],
    )
    assert result.ok


def test_cm3_task_owner_double_booked_across_different_resources_is_rejected():
    """cM3: the task's real owner (Task.owner_id) already has a live, overlapping slot on a
    DIFFERENT resource than the one this candidate proposes - the owner cannot be in two places
    at once, even though the candidate resource's own capacity is free."""
    repo, executor, _ = _build()
    doctor = repo.save(Resource(type=ResourceType.DOCTOR, department_id=uuid4(),
                                 capacity_per_hour=5))
    room_a = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                                 capacity_per_hour=5))
    room_b = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                                 capacity_per_hour=5))
    start = datetime(2026, 7, 18, 9, 0, tzinfo=UTC)

    task_a = _task(repo, owner_id=doctor.id, estimated_duration_min=10)
    assert allocate_task_slot(
        repo, executor, "care-plan-agent", task_a,
        [SlotCandidate(resource_id=room_a.id, start=start)],
    ).ok

    task_b = _task(repo, owner_id=doctor.id, estimated_duration_min=10)
    result = allocate_task_slot(
        repo, executor, "care-plan-agent", task_b,
        [SlotCandidate(resource_id=room_b.id, start=start + timedelta(minutes=5))],
    )
    assert result.ok is False
    assert "owner" in result.reason
    assert repo.list(Slot, task_id=task_b.id) == []


def test_cm3_no_owner_clash_when_overlap_is_after_the_owners_first_booking_ends():
    """Sanity companion to the owner-clash test: a non-overlapping window for the same owner, on
    a different resource, is fine - the check is about time overlap, not "ever double-booked"."""
    repo, executor, _ = _build()
    doctor = repo.save(Resource(type=ResourceType.DOCTOR, department_id=uuid4(),
                                 capacity_per_hour=5))
    room_a = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                                 capacity_per_hour=5))
    room_b = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                                 capacity_per_hour=5))
    start = datetime(2026, 7, 18, 9, 0, tzinfo=UTC)

    task_a = _task(repo, owner_id=doctor.id, estimated_duration_min=10)
    assert allocate_task_slot(
        repo, executor, "care-plan-agent", task_a,
        [SlotCandidate(resource_id=room_a.id, start=start)],
    ).ok

    task_b = _task(repo, owner_id=doctor.id, estimated_duration_min=10)
    result = allocate_task_slot(
        repo, executor, "care-plan-agent", task_b,
        [SlotCandidate(resource_id=room_b.id, start=start + timedelta(minutes=30))],
    )
    assert result.ok


def test_m2_cancelled_task_slot_excluded_from_capacity_and_owner_clash():
    repo, executor, _ = _build()
    room = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                               capacity_per_hour=1))
    start = datetime(2026, 7, 18, 9, 0, tzinfo=UTC)

    cancelled_task = _task(repo, owner_id=room.id, estimated_duration_min=10,
                            execution_status=ExecutionStatus.CANCELLED)
    repo.save(Slot(task_id=cancelled_task.id, owner_id=room.id, start=start,
                    end=start + timedelta(minutes=10)))

    # capacity is nominally "full" (1/hour) from the stale, cancelled booking alone - a live task
    # must still get the slot, proving cancelled bookings are excluded from the count (m2)
    live_task = _task(repo, owner_id=room.id, estimated_duration_min=10)
    result = allocate_task_slot(
        repo, executor, "care-plan-agent", live_task,
        [SlotCandidate(resource_id=room.id, start=start)],
    )
    assert result.ok


def test_sec_m1_negative_duration_rejected_at_slot_allocation():
    repo, executor, _ = _build()
    room = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                               capacity_per_hour=5))
    task = _task(repo, owner_id=room.id, estimated_duration_min=-15)  # a bad forecast value

    result = allocate_task_slot(
        repo, executor, "care-plan-agent", task,
        [SlotCandidate(resource_id=room.id, start=datetime(2026, 7, 18, 9, 0, tzinfo=UTC))],
    )
    assert result.ok is False
    assert "duration" in result.reason
    assert repo.list(Slot, task_id=task.id) == []


def test_ac_08_2_closed_room_blocked_then_a_different_slot_is_chosen():
    repo, executor, audit = _build()
    closed = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                                 is_available=False, capacity_per_hour=5))
    open_room = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                                    capacity_per_hour=5))
    start = datetime(2026, 7, 18, 9, 0, tzinfo=UTC)
    task = _task(repo, estimated_duration_min=10)

    result = allocate_task_slot(
        repo,
        executor,
        "care-plan-agent",
        task,
        [
            SlotCandidate(resource_id=closed.id, start=start),
            SlotCandidate(resource_id=open_room.id, start=start),
        ],
    )

    assert result.ok
    slot = repo.list(Slot, task_id=task.id)[0]
    assert slot.owner_id == open_room.id  # the closed room was never used

    blocked_entries = [e for e in audit.entries() if e.action == "BLOCKED:allocate_slot"]
    assert len(blocked_entries) == 1
    assert "unavailable" in blocked_entries[0].reasoning


def test_all_candidates_failing_returns_the_last_failure():
    repo, executor, _ = _build()
    closed = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(),
                                 is_available=False))
    task = _task(repo, estimated_duration_min=10)
    start = datetime(2026, 7, 18, 9, 0, tzinfo=UTC)

    result = allocate_task_slot(
        repo, executor, "care-plan-agent", task, [SlotCandidate(resource_id=closed.id, start=start)]
    )
    assert result.ok is False
    assert repo.list(Slot, task_id=task.id) == []


def test_cm5_empty_candidates_is_a_graceful_failure_not_a_crash():
    repo, executor, audit = _build()
    task = _task(repo, estimated_duration_min=10)
    before = len(audit.entries())

    result = allocate_task_slot(repo, executor, "care-plan-agent", task, [])

    assert result.ok is False
    assert "no slot candidates" in result.reason
    assert repo.list(Slot, task_id=task.id) == []
    # still audited, even though there was no Action to route through the executor (cM5)
    assert len(audit.entries()) == before + 1
    assert audit.entries()[-1].action == "FAILED:allocate_slot"

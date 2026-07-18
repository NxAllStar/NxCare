"""FR-08: slot allocation on doctor/room capacity, called by the Care Plan Agent (FR-04).

`allocate_slot` is named to match the constraint checker's existing `allocate_slot` rule
(`ConstraintChecker._check_allocate_slot`, BR-16: never a closed/unavailable resource) in
`src/vaic/tools/constraint_checker.py` (agent-core-dev's file - not edited here), so that hard gate
runs before this handler ever executes.

The checker does NOT check per-hour capacity or an owner clash - that enforcement lives INSIDE
this handler instead (per the task's scope decision, recorded in the TASK-008 task file): never
exceed `Resource.capacity_per_hour` for the requested time window, never double-book an owner past
that capacity (AC-08.1). On rejection (closed room from the checker, or capacity/clash from this
handler) `allocate_task_slot` tries the next candidate (AC-08.2) - it never edits
`constraint_checker.py` to do it.

Capacity semantics (cM1, TASK-008 fix round): `Resource.capacity_per_hour` is a THROUGHPUT cap, not
a concurrent-overlap cap. A candidate is counted against every other live booking on the same
resource whose `start` falls in the same clock hour (`09:00:00-09:59:59` and `10:00:00` are
different buckets), regardless of whether the two windows actually overlap in time - six
back-to-back 10-minute bookings inside one hour are six bookings against that hour's capacity, not
zero clashes.

Owner clash (cM3): the capacity/clash check above only ever looks at the CANDIDATE resource's own
bookings. When a candidate's resource differs from the task's actual owner (`Task.owner_id` - see
the ERD in docs/specs/08-data-model.md, "TASK owned by RESOURCE" and "SLOT occupies RESOURCE": a
task's slot is expected to occupy the same resource that owns the task), this handler additionally
refuses a candidate that would leave the task's owner double-booked - i.e. some OTHER task owned by
the same resource already holds a live, time-overlapping slot on a DIFFERENT resource. When the
candidate resource IS the task's owner, that case is already the throughput check above; this extra
check only fires for the "owner != resource" gap the review found.

Live-booking filter (m2): a `Slot` belonging to a `CANCELLED` or `DONE` `Task` is history, not a
live booking - it is excluded from both the capacity count and the owner-clash check, so a
completed or cancelled task can never wrongly block a new allocation.

Duration range guard (sec-m1, BR-14, NFR-SEC-20): `duration_min` is range-validated before it is
ever used to compute a slot's `end` - see `durations.validate_duration_minutes`, the same guard
`sequencing.py` applies at estimation time. Defense in depth: this handler is reachable directly
(bypassing `sequence_orders`) by any caller that builds an `Action` by hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel

from ...models import ExecutionStatus, Resource, Slot, Task
from ...state import Repository
from ...tools import Action, ActionResult, AuditLog, Tool, ToolError
from ..core.executor import ActionExecutor
from .durations import validate_duration_minutes

_FINISHED_STATUSES = (ExecutionStatus.CANCELLED, ExecutionStatus.DONE)


@dataclass(frozen=True)
class SlotCandidate:
    """One (resource, start time) option the Care Plan Agent may try for a task's slot."""

    resource_id: UUID
    start: datetime


class AllocateSlotIn(BaseModel):
    task_id: UUID
    resource_id: UUID
    start: datetime
    duration_min: int


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def _hour_bucket(dt: datetime) -> datetime:
    """The clock hour `dt` falls in - the unit `capacity_per_hour` is measured against (cM1)."""
    return dt.replace(minute=0, second=0, microsecond=0)


def _slot_is_live(repo: Repository, slot: Slot) -> bool:
    """False for a CANCELLED/DONE task's slot - history, never a capacity/clash blocker (m2)."""
    task = repo.get(Task, slot.task_id)
    return task is not None and task.execution_status not in _FINISHED_STATUSES


def _allocate_slot(params: AllocateSlotIn, repo: Repository) -> dict:
    resource = repo.get(Resource, params.resource_id)
    if resource is None:
        raise ToolError("unknown resource")
    if not resource.is_available:
        # Defense in depth only: the constraint checker's BR-16 rule already blocks this before
        # the handler runs when the write goes through ActionExecutor. Kept so a direct tool.run()
        # call (bypassing the executor) can never allocate into a closed room either.
        raise ToolError("resource is unavailable (closed room) - BR-16")

    try:
        validate_duration_minutes(params.duration_min)  # BR-14 / NFR-SEC-20
    except ValueError as exc:
        raise ToolError(str(exc)) from exc

    task = repo.get(Task, params.task_id)
    if task is None:
        raise ToolError("unknown task")

    end = params.start + timedelta(minutes=params.duration_min)

    capacity = resource.capacity_per_hour
    if capacity is not None:
        bucket = _hour_bucket(params.start)
        booked_this_hour = [
            slot
            for slot in repo.list(Slot, owner_id=params.resource_id)
            if _hour_bucket(slot.start) == bucket and _slot_is_live(repo, slot)
        ]
        if len(booked_this_hour) >= capacity:
            raise ToolError(
                f"resource {params.resource_id} is over capacity "
                f"({capacity}/hour) for {params.start.isoformat()}"
            )

    if task.owner_id != params.resource_id:
        # cM3: the resource being booked is not the task's own owner. Refuse if that owner already
        # holds a live, overlapping slot on some OTHER resource - the owner cannot be double-booked
        # just because this particular resource's own capacity happens to be free.
        for other_slot in repo.list(Slot):
            if other_slot.task_id == params.task_id:
                continue
            other_task = repo.get(Task, other_slot.task_id)
            if other_task is None or other_task.owner_id != task.owner_id:
                continue
            if not _slot_is_live(repo, other_slot):
                continue
            other_end = other_slot.end or (other_slot.start + timedelta(minutes=1))
            if _overlaps(params.start, end, other_slot.start, other_end):
                raise ToolError(
                    f"task owner {task.owner_id} already has an overlapping booking at "
                    f"{other_slot.start.isoformat()} on a different resource - cannot "
                    "double-book the owner"
                )

    slot = repo.save(Slot(task_id=params.task_id, owner_id=params.resource_id,
                           start=params.start, end=end))
    return {"slot_id": str(slot.id), "resource_id": str(params.resource_id)}


def build_allocate_slot_tool() -> Tool:
    return Tool("allocate_slot", AllocateSlotIn, _allocate_slot)


def allocate_task_slot(
    repo: Repository,
    executor: ActionExecutor,
    actor: str,
    task: Task,
    candidates: list[SlotCandidate],
    reasoning: str = "",
) -> ActionResult:
    """Try each candidate through the guarded spine until one succeeds (AC-08.1 / AC-08.2).

    A closed room (BR-16, caught by the constraint checker) or an over-capacity/clashing window
    (caught inside `_allocate_slot`) both fall through to the next candidate. Every attempt -
    blocked or failed or successful - is audited by the `ActionExecutor` (FR-13).

    Empty `candidates` (cM5): treated as a graceful failed allocation, exactly like every candidate
    failing - never a raised exception. `generate_care_plan` (care_plan.py) depends on this: a task
    it already created and persisted must come back as an ordinary failed `ActionResult`, not blow
    up mid-generation and leave the rest of the plan half-built. The failure is still audited here
    (there is no `Action` to route through the executor when there is nothing to try), under the
    same `"FAILED:allocate_slot"` action name the executor itself would have used.
    """
    if not candidates:
        entry = AuditLog(repo).record(
            actor,
            "FAILED:allocate_slot",
            "no slot candidates were offered for this task",
            target_id=task.id,
        )
        return ActionResult(
            allowed=True,
            ok=False,
            reason="no slot candidates were offered for this task",
            audit_id=entry.id,
        )

    result: ActionResult | None = None
    for candidate in candidates:
        result = executor.execute(
            Action(
                tool="allocate_slot",
                actor=actor,
                reasoning=reasoning,
                params={
                    "task_id": task.id,
                    "resource_id": candidate.resource_id,
                    "start": candidate.start,
                    "duration_min": task.estimated_duration_min,
                },
            )
        )
        if result.ok:
            return result
    return result  # every candidate failed; the last result carries the final reason

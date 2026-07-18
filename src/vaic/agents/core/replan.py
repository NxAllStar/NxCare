"""Re-plan around a failed resource: the blast-radius math and the `execute_replan` tool (FR-09).

`execute_replan` is the one action the Disruption agent takes. It is keyed to the constraint
checker's existing `execute_replan` rule (`ConstraintChecker._check_execute_replan`, FR-09 tiered
autonomy: a re-plan whose blast radius exceeds the threshold cannot run without a recorded human
approval), so that hard gate runs before this handler ever executes. The handler itself is
deterministic: it re-plates each affected task onto an available alternate resource of the same
type in the same department, moving that task's live slot with it. A task with no available
alternate stays put (it waits for the resource to return) rather than being dropped.

Blast radius counts DISTINCT patients, not tasks: two tasks for the same patient on the failed
resource are one affected patient, not two (FR-09 "how many patients are affected").
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from ...models import (
    CarePlan,
    DisruptionEvent,
    DisruptionStatus,
    Resource,
    Slot,
    Task,
)
from ...state import Repository, owner_queue
from ...tools import Tool

EXECUTE_REPLAN_TOOL = "execute_replan"


class ExecuteReplanIn(BaseModel):
    resource_id: UUID
    blast_radius: int = 0  # read by the constraint checker for the tiered-autonomy gate
    approved: bool = False  # a human's one-tap approval (only meaningful above the threshold)
    disruption_id: UUID | None = None


def affected_tasks(repo: Repository, resource_id: UUID) -> list[Task]:
    """The live (paid, not-finished) tasks a resource failure would disrupt - BR-10 applies."""
    return owner_queue(repo, resource_id)


def compute_blast_radius(repo: Repository, resource_id: UUID) -> int:
    """Distinct patients affected if `resource_id` fails now (FR-09 blast radius)."""
    patients: set[UUID] = set()
    for task in affected_tasks(repo, resource_id):
        care_plan = repo.get(CarePlan, task.care_plan_id)
        if care_plan is not None:
            patients.add(care_plan.patient_id)
    return len(patients)


def available_alternates(repo: Repository, resource_id: UUID) -> list[Resource]:
    """Other available resources of the same type and department the work can move to."""
    failed = repo.get(Resource, resource_id)
    if failed is None:
        return []
    return sorted(
        (
            r
            for r in repo.list(Resource, type=failed.type, department_id=failed.department_id)
            if r.id != resource_id and r.is_available
        ),
        key=lambda r: str(r.id),
    )


def _execute_replan(params: ExecuteReplanIn, repo: Repository) -> dict:
    tasks = affected_tasks(repo, params.resource_id)
    alternates = available_alternates(repo, params.resource_id)
    reassigned: list[str] = []

    if alternates:
        for index, task in enumerate(tasks):
            new_owner = alternates[index % len(alternates)]
            task.owner_id = new_owner.id
            repo.save(task)
            for slot in repo.list(Slot, task_id=task.id):
                slot.owner_id = new_owner.id
                repo.save(slot)
            reassigned.append(str(task.id))

    if params.disruption_id is not None:
        event = repo.get(DisruptionEvent, params.disruption_id)
        if event is not None:
            event.status = (
                DisruptionStatus.APPROVED if params.approved else DisruptionStatus.AUTO_RESOLVED
            )
            repo.save(event)

    return {"reassigned": reassigned, "affected": len(tasks)}


def build_execute_replan_tool() -> Tool:
    return Tool(EXECUTE_REPLAN_TOOL, ExecuteReplanIn, _execute_replan)

"""FR-04: the Care Plan Agent - turns the doctor's signed `ServiceOrder` list into a sequenced,
duration-estimated, slotted `CarePlan`, ready to hand off to the Journey Agent (FR-06, not
implemented in this task).

`generate_care_plan` never adds, drops, or re-targets a service (BR-07): it is a 1:1 map from the
input orders (via `sequence_orders`, BR-08) to `Task`s, each carrying a duration from the injected
`DurationEstimator` (BR-09) and a `Slot` from `allocate_task_slot` (FR-08). The plan is left
`ACTIVE` only once every task has been created AND every task got a successful slot (see the
failure/rollback contract below) - the "ready state" the Journey Agent (FR-06) is handed.

Audit spine (cM6 / sM1, TASK-008 fix round): `CarePlan` creation, each `Task` creation, and the
`DRAFT -> ACTIVE` transition are their own tools (`create_care_plan`, `create_task`,
`activate_care_plan`), each routed through the same `ActionExecutor` spine as `allocate_slot` -
closed action space plus an audited `AuditLogEntry` per write (FR-13), not a bare `repo.save()`.
None of the three needs a constraint-checker rule (no rule is added to `constraint_checker.py` -
an unregistered tool name is allowed by default); routing them through the executor is worthwhile
purely for the audit trail and the closed action space.

Failure/rollback contract (cM5): if any task fails to get a slot - whether every candidate was
rejected, or `candidates_for` returned none at all - the `CarePlan` is left `DRAFT`, never promoted
to `ACTIVE`. Nothing already written is deleted: there is no cross-entity transaction primitive in
this Redis-backed state layer (spec OI-15), so "rollback" here means "never promote", not "delete
what was written". The `Task`s that were created stay persisted and `LOCKED`/`UNPAID` (BR-10
already excludes them from every queue and load), so a coordinator can retry allocation later
without losing the sequencing/duration work already done. Every step - success or failure - is
already audited by its own `executor.execute()` call, so the failure is traceable without a
bespoke summary entry; `CarePlanResult.all_slotted` and `CarePlan.status` together tell the caller
whether the plan is ready to hand to FR-06.

FR-23 seam (queue-driven route generation, lands in TASK-027): `owner_resolver` and
`candidates_for` are the two extension points a queue-aware allocator needs. A future
implementation supplies different callables here; this function's signature, and the
`CarePlan`/`Task`/`Slot` shape it produces, do not need to change for that to land.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel

from ...models import (
    CAREPLAN_TRANSITIONS,
    CarePlan,
    CarePlanStatus,
    Diagnosis,
    ServiceOrder,
    ServiceType,
    Task,
    assert_transition,
)
from ...state import Repository
from ...tools import Action, ActionResult, Tool, ToolError
from ..core.executor import ActionExecutor
from .durations import DurationEstimator
from .sequencing import SequencedOrder, sequence_orders
from .slots import SlotCandidate, allocate_task_slot


class CreateCarePlanIn(BaseModel):
    patient_id: UUID
    diagnosis_id: UUID


def _create_care_plan(params: CreateCarePlanIn, repo: Repository) -> dict:
    plan = repo.save(CarePlan(patient_id=params.patient_id, diagnosis_id=params.diagnosis_id))
    return {"care_plan_id": str(plan.id)}


def build_create_care_plan_tool() -> Tool:
    return Tool("create_care_plan", CreateCarePlanIn, _create_care_plan)


class CreateTaskIn(BaseModel):
    care_plan_id: UUID
    service_order_id: UUID
    owner_id: UUID
    estimated_duration_min: int
    sequence_index: int


def _create_task(params: CreateTaskIn, repo: Repository) -> dict:
    task = repo.save(
        Task(
            care_plan_id=params.care_plan_id,
            service_order_id=params.service_order_id,
            owner_id=params.owner_id,
            estimated_duration_min=params.estimated_duration_min,
            sequence_index=params.sequence_index,
        )
    )
    return {"task_id": str(task.id)}


def build_create_task_tool() -> Tool:
    return Tool("create_task", CreateTaskIn, _create_task)


class ActivateCarePlanIn(BaseModel):
    care_plan_id: UUID


def _activate_care_plan(params: ActivateCarePlanIn, repo: Repository) -> dict:
    plan = repo.get(CarePlan, params.care_plan_id)
    if plan is None:
        raise ToolError("unknown care plan")
    assert_transition(CAREPLAN_TRANSITIONS, plan.status, CarePlanStatus.ACTIVE)
    plan.status = CarePlanStatus.ACTIVE
    plan = repo.save(plan)
    return {"care_plan_id": str(plan.id)}


def build_activate_care_plan_tool() -> Tool:
    return Tool("activate_care_plan", ActivateCarePlanIn, _activate_care_plan)


@dataclass(frozen=True)
class CarePlanResult:
    care_plan: CarePlan
    tasks: list[Task]
    sequenced: list[SequencedOrder]
    slot_results: list[ActionResult]

    @property
    def all_slotted(self) -> bool:
        return all(result.ok for result in self.slot_results)


def generate_care_plan(
    repo: Repository,
    executor: ActionExecutor,
    actor: str,
    patient_id: UUID,
    diagnosis: Diagnosis,
    orders_with_types: list[tuple[ServiceOrder, ServiceType]],
    estimate_duration: DurationEstimator,
    owner_resolver: Callable[[ServiceOrder, ServiceType], UUID],
    candidates_for: Callable[[Task, SequencedOrder], list[SlotCandidate]],
    reasoning: str = "",
) -> CarePlanResult:
    """Generate, sequence, and slot the care plan for one diagnosis's orders (AC-04.1 / AC-04.2).

    `orders_with_types` is exactly the doctor-signed order set (e.g. produced by
    `capture_diagnosis_and_orders`, FR-03) - never expanded or filtered here (BR-07).

    The registry behind `executor` must already carry `create_care_plan`, `create_task`,
    `allocate_slot`, and `activate_care_plan` (same pattern as `capture_diagnosis_and_orders` in
    orders.py: this function does not register tools, it only calls them).
    """
    sequenced = sequence_orders(orders_with_types, estimate_duration, owner_resolver)

    plan_result = executor.execute(
        Action(
            tool="create_care_plan",
            actor=actor,
            reasoning=reasoning,
            params={"patient_id": patient_id, "diagnosis_id": diagnosis.id},
        )
    )
    if not plan_result.ok or plan_result.output is None:
        raise ToolError(f"could not create the care plan: {plan_result.reason}")
    plan = repo.get(CarePlan, UUID(plan_result.output["care_plan_id"]))
    assert plan is not None  # just saved by the tool above; a missing read-back is a repo defect

    tasks: list[Task] = []
    for seq in sequenced:
        task_result = executor.execute(
            Action(
                tool="create_task",
                actor=actor,
                reasoning=reasoning,
                params={
                    "care_plan_id": plan.id,
                    "service_order_id": seq.order.id,
                    "owner_id": seq.owner_id,  # resolved once in sequence_orders (cM4) - not here
                    "estimated_duration_min": seq.duration_min,
                    "sequence_index": seq.sequence_index,
                },
            )
        )
        if not task_result.ok or task_result.output is None:
            raise ToolError(f"could not create a task: {task_result.reason}")
        task = repo.get(Task, UUID(task_result.output["task_id"]))
        assert task is not None
        tasks.append(task)

    slot_results: list[ActionResult] = [
        allocate_task_slot(repo, executor, actor, task, candidates_for(task, seq), reasoning)
        for task, seq in zip(tasks, sequenced, strict=True)
    ]

    if all(result.ok for result in slot_results):
        activation = executor.execute(
            Action(
                tool="activate_care_plan",
                actor=actor,
                reasoning=reasoning,
                params={"care_plan_id": plan.id},
            )
        )
        if activation.ok:
            plan = repo.get(CarePlan, plan.id) or plan
    # else: leave the plan DRAFT - see the failure/rollback contract in the module docstring (cM5).

    return CarePlanResult(
        care_plan=plan, tasks=tasks, sequenced=sequenced, slot_results=slot_results
    )

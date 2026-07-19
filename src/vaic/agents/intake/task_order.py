"""Suggest a sensible order for a patient's remaining services, grounded in live queue load.

A patient often has several ordered tests to do (blood test, X-ray, ECG...). Which to do first is a
real question: each service's station has its own queue right now, so the shortest total wait is
not the doctor's listed order. This module retrieves each remaining task's service-queue load
(`service_queue_overview`, the deterministic grounding), then lets an LLM propose an order and
explain it - the same retrieve -> reason -> validate shape as the arrival chat (ADR-001).

Grounding contract: the model only ever reorders the task ids it was given (the validator rejects
anything that is not a permutation of them) and reasons over queue counts it did not invent. When
no provider is configured, or the model returns an off-schema / non-permutation answer, the
deterministic fallback orders by shortest queue-clear time first - a safe, explainable default.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ...models import CarePlan, ExecutionStatus, ServiceOrder, ServiceType, Task
from ...state import Repository
from ..core import run_reason_flow
from .patient_status import service_queue_overview

# A task in one of these states is still to be done and worth ordering; DONE/CANCELLED are not.
_REMAINING_STATUSES = (
    ExecutionStatus.LOCKED,
    ExecutionStatus.PENDING,
    ExecutionStatus.IN_PROGRESS,
)


@dataclass(frozen=True)
class ServiceQueueInfo:
    """One remaining service the patient must do, with its live queue load - the grounding row."""

    task_id: UUID
    service_type_code: str
    service_type_label: str
    people_waiting: int
    eta_minutes: int


class OrderedService(BaseModel):
    """One entry in the suggested order: which task, and why it is placed here."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    service_type_code: str = ""
    reason: str = ""


class TaskOrderSuggestion(BaseModel):
    """The validated suggestion: a natural-language message plus the ordered task list."""

    model_config = ConfigDict(extra="forbid")

    message: str
    order: list[OrderedService] = Field(default_factory=list)


class TaskOrderLLM(Protocol):
    """A reasoning client shaped like the reason flow expects: `reply(message, context)`."""

    def reply(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        ...


class TaskOrderError(Exception):
    """Raised by a `TaskOrderLLM` on a provider/transport failure (timeout, outage, rate limit)."""


def _select_care_plan(repo: Repository, patient_id: UUID) -> CarePlan | None:
    """The patient's most recently created Care Plan (any status), or None."""
    plans = repo.list(CarePlan, patient_id=patient_id)
    return max(plans, key=lambda p: p.created_at) if plans else None


def collect_service_queues(repo: Repository, patient_id: UUID) -> list[ServiceQueueInfo]:
    """The patient's not-yet-finished tasks, each with its service type's live queue load."""
    plan = _select_care_plan(repo, patient_id)
    if plan is None:
        return []

    infos: list[ServiceQueueInfo] = []
    tasks = sorted(repo.list(Task, care_plan_id=plan.id), key=lambda t: t.sequence_index)
    for task in tasks:
        if task.execution_status not in _REMAINING_STATUSES:
            continue
        order = repo.get(ServiceOrder, task.service_order_id)
        service_type = repo.get(ServiceType, order.service_type_id) if order else None
        queue = service_queue_overview(repo, service_type.id) if service_type is not None else None
        infos.append(
            ServiceQueueInfo(
                task_id=task.id,
                service_type_code=service_type.code if service_type else "",
                service_type_label=service_type.display_label if service_type else "",
                people_waiting=queue.people_waiting if queue else 0,
                eta_minutes=queue.eta_minutes if queue else 0,
            )
        )
    return infos


def build_context(infos: list[ServiceQueueInfo]) -> dict[str, Any]:
    """Turn the retrieved service/queue rows into the CONTEXT dict the reasoner sees."""
    return {
        "services": [
            {
                "task_id": str(info.task_id),
                "service_type_code": info.service_type_code,
                "service_type_label": info.service_type_label,
                "people_waiting": info.people_waiting,
                "eta_minutes": info.eta_minutes,
            }
            for info in infos
        ]
    }


def _deterministic_order(context: dict[str, Any]) -> dict[str, Any]:
    """Fallback reasoner: shortest queue-clear time first, then fewest people (deterministic)."""
    services = list(context.get("services", []))
    ordered = sorted(services, key=lambda s: (s["eta_minutes"], s["people_waiting"]))
    if not ordered:
        return {"message": "There are no remaining services to order.", "order": []}
    spans = ", ".join(f"{s['service_type_code']} (~{s['eta_minutes']}min wait)" for s in ordered)
    return {
        "message": f"Suggested order by shortest current wait: {spans}.",
        "order": [
            {
                "task_id": s["task_id"],
                "service_type_code": s["service_type_code"],
                "reason": f"{s['people_waiting']} ahead, about {s['eta_minutes']} min to clear",
            }
            for s in ordered
        ],
    }


class RuleBasedTaskOrderLLM:
    """Deterministic reasoner for tests and the no-provider fallback (no network)."""

    def reply(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        return _deterministic_order(context)


class _NotAPermutation(ValueError):
    """The model's order was not a permutation of the given task ids - rejected, fall back."""


def _make_validator(expected_ids: set[str]):
    """Validate the raw suggestion AND that its order is a permutation of the given task ids."""

    def validate(raw: Any) -> TaskOrderSuggestion:
        suggestion = TaskOrderSuggestion.model_validate(raw)
        got = [entry.task_id for entry in suggestion.order]
        if sorted(got) != sorted(expected_ids):
            raise _NotAPermutation("suggested order is not a permutation of the patient's tasks")
        return suggestion

    return validate


def suggest_task_order(
    repo: Repository, patient_id: UUID, llm: TaskOrderLLM
) -> TaskOrderSuggestion:
    """Suggest an order for the patient's remaining services; return a validated suggestion.

    Runs reason -> validate on PocketFlow (ADR-001): the reasoner's output must parse AND be a
    permutation of the retrieved task ids; on a reasoner error or off-schema/non-permutation output
    it degrades to the deterministic shortest-wait-first order.
    """
    infos = collect_service_queues(repo, patient_id)
    context = build_context(infos)
    expected_ids = {str(info.task_id) for info in infos}

    def _on_error() -> TaskOrderSuggestion:
        return TaskOrderSuggestion.model_validate(_deterministic_order(context))

    if not expected_ids:  # nothing to order - skip the model entirely
        return _on_error()

    return run_reason_flow(
        llm,
        "",  # no free-text message; the context is the whole input
        context,
        validate=_make_validator(expected_ids),
        on_error=_on_error,
        reason_errors=(TaskOrderError,),
        validate_errors=(ValidationError, _NotAPermutation),
    )

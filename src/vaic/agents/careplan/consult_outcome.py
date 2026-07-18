"""What a finished consult produces: a diagnosis, its ordered tests, and the tasks for them.

This is the doctor-facing "record the outcome of the visit" step that FR-03 and FR-04 always
implied but nothing wired together yet: capturing a `Diagnosis` + `ServiceOrder`s (FR-03) and
turning them into a sequenced `CarePlan` + `Task`s (FR-04). Both already exist in this package as
`capture_diagnosis_and_orders` and `generate_care_plan`; this module only composes them behind one
call and one pre-built executor, so the API layer does not have to assemble the tool registry.

Lightweight by decision (this pass): tasks are created but NOT slotted. `candidates_for` returns
no slot candidates, so `generate_care_plan` leaves every task `LOCKED`/`UNPAID` and the plan
`DRAFT` (its documented cM5 rollback path) - exactly the "diagnosed, tasks listed, not yet queued"
state the patient's `/status` reports as `PLAN_NOT_QUEUED`. Real slot allocation (FR-08) and a real
per-task owner (a technician/room, resolved by capability) are deferred; until then each task's
`owner_id` is a placeholder - see `_default_owner_resolver`.

Duration comes from `ServiceType.default_duration_min` - the seeded reference figure, not an
invented constant (BR-09's spirit) and range-guarded by `validate_duration_minutes`. Swapping in
the real forecast-tool estimator (see `durations.py`) is a one-line change to `estimate_duration`.

`actor_role` is passed as `role_doctor` so the BR-05 doctor-only gate on `create_service_order`
passes. Until FR-18/TASK-031 binds it to an authenticated session, it is trusted exactly as the
caller supplies it (same standing precondition orders.py documents).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from ...models import Appointment, Diagnosis, ServiceOrder, ServiceType
from ...state import Repository
from ...tools import AuditLog, ConstraintChecker, ToolRegistry
from ..core.executor import ActionExecutor
from .care_plan import (
    build_activate_care_plan_tool,
    build_create_care_plan_tool,
    build_create_task_tool,
    generate_care_plan,
)
from .durations import validate_duration_minutes
from .orders import (
    build_create_diagnosis_tool,
    build_create_service_order_tool,
    capture_diagnosis_and_orders,
)
from .slots import build_allocate_slot_tool

DOCTOR_ROLE = "role_doctor"


class ConsultOutcomeError(Exception):
    """A precondition failed before any diagnosis was recorded (unknown appointment, unknown
    service type, or a guarded write refused). Distinct from a partial success."""


@dataclass(frozen=True)
class ConsultOutcome:
    """What was produced: the diagnosis, and the tasks (one per ordered service)."""

    diagnosis_id: UUID
    care_plan_id: UUID
    task_ids: list[UUID] = field(default_factory=list)


def build_consult_outcome_executor(repo: Repository) -> ActionExecutor:
    """Assemble the guarded spine with every tool the outcome flow drives (FR-03 + FR-04)."""
    registry = ToolRegistry()
    registry.register(build_create_diagnosis_tool())
    registry.register(build_create_service_order_tool())
    registry.register(build_create_care_plan_tool())
    registry.register(build_create_task_tool())
    registry.register(build_allocate_slot_tool())
    registry.register(build_activate_care_plan_tool())
    return ActionExecutor(repo, registry, ConstraintChecker(repo), AuditLog(repo))


def _default_owner_resolver(diagnosed_by: UUID):
    """Placeholder task owner: the consulting doctor. A real per-service owner (technician/room by
    capability) is FR-08/FR-23 work; until then every task is parked on the doctor who ordered it,
    which is enough for the LOCKED, not-yet-queued state this flow produces."""

    def resolve(order: ServiceOrder, service_type: ServiceType) -> UUID:
        return diagnosed_by

    return resolve


def _default_duration(service_type: ServiceType, owner_id: UUID) -> int:
    """Duration from the seeded `ServiceType.default_duration_min`, range-guarded (BR-14)."""
    return validate_duration_minutes(service_type.default_duration_min)


def record_consult_outcome(
    repo: Repository,
    executor: ActionExecutor,
    *,
    appointment_id: UUID,
    conditions: list[str],
    diagnosed_by: UUID,
    service_type_ids: list[UUID],
    actor: str = "doctor-console",
    actor_role: str = DOCTOR_ROLE,
    reasoning: str = "",
) -> ConsultOutcome:
    """Capture the diagnosis + orders (FR-03) and generate the (unslotted) care plan (FR-04).

    Raises `ConsultOutcomeError` if the appointment does not exist, a `service_type_id` is unknown,
    or a guarded write is refused (e.g. the actor is not a doctor) - nothing is half-committed past
    the failing step, and the caller should NOT then close the visit.
    """
    appointment = repo.get(Appointment, appointment_id)
    if appointment is None:
        raise ConsultOutcomeError(f"no appointment {appointment_id}")

    for service_type_id in service_type_ids:
        if repo.get(ServiceType, service_type_id) is None:
            raise ConsultOutcomeError(f"unknown service type {service_type_id}")

    capture = capture_diagnosis_and_orders(
        executor,
        actor=actor,
        appointment_id=appointment_id,
        conditions=conditions,
        diagnosed_by=diagnosed_by,
        actor_role=actor_role,
        service_type_ids=service_type_ids,
        reasoning=reasoning,
    )
    if not capture.ok or capture.diagnosis_id is None:
        reason = capture.diagnosis_result.reason or "a service order was refused"
        raise ConsultOutcomeError(f"could not record the consult outcome: {reason}")

    diagnosis = repo.get(Diagnosis, capture.diagnosis_id)
    assert diagnosis is not None  # just written through the executor above

    orders_with_types: list[tuple[ServiceOrder, ServiceType]] = []
    for order_result in capture.order_results:
        assert order_result.output is not None  # capture.ok means every order succeeded
        order = repo.get(ServiceOrder, UUID(order_result.output["service_order_id"]))
        assert order is not None
        service_type = repo.get(ServiceType, order.service_type_id)
        assert service_type is not None  # validated to exist before capture
        orders_with_types.append((order, service_type))

    plan_result = generate_care_plan(
        repo,
        executor,
        actor=actor,
        patient_id=appointment.patient_id,
        diagnosis=diagnosis,
        orders_with_types=orders_with_types,
        estimate_duration=_default_duration,
        owner_resolver=_default_owner_resolver(diagnosed_by),
        candidates_for=lambda task, seq: [],  # lightweight: no slots this pass (tasks stay LOCKED)
        reasoning=reasoning,
    )

    return ConsultOutcome(
        diagnosis_id=diagnosis.id,
        care_plan_id=plan_result.care_plan.id,
        task_ids=[task.id for task in plan_result.tasks],
    )

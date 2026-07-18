"""FR-03: diagnosis and service-order capture - the doctor-signed source of truth for FR-04.

Only `role_doctor` may create a `Diagnosis` or a `ServiceOrder` (BR-05, CO-02); AI never adds,
drops, or changes a service. `create_service_order` is named to match the constraint checker's
existing `BR-05` rule (`ConstraintChecker._check_create_service_order` in
`src/vaic/tools/constraint_checker.py`, agent-core-dev's file - not edited here), so every write
through the `ActionExecutor` is checked before it runs.

`create_diagnosis` has no constraint-checker rule of its own (same out-of-scope file), so the same
doctor-only gate is enforced INSIDE this handler instead - identical rule (BR-05's literal
`role_doctor` check, not open like OI-19), different enforcement point, same effect: a non-doctor
actor is refused and the refusal is audited by the executor either way (AC-03.2).

Precondition (TASK-031, agent-core/FR-18 - not this task's scope): `actor_role` on both input
schemas below is trusted here exactly as given. This module assumes it was already populated
server-side from the authenticated session before either tool is ever invoked - never taken
verbatim from an unauthenticated caller. Binding `actor_role` to the real authenticated principal
is TASK-031's job; until it lands, the BR-05 `role_doctor` check is only as trustworthy as whatever
sets `actor_role` upstream.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from pydantic import BaseModel

from ...models import Appointment, Diagnosis, ServiceOrder, ServiceType
from ...state import Repository
from ...tools import Action, ActionResult, Tool, ToolError
from ..core.executor import ActionExecutor

DOCTOR_ROLE = "role_doctor"  # BR-05 is settled (unlike OI-19's payment role) - literal by design


class CreateDiagnosisIn(BaseModel):
    appointment_id: UUID
    conditions: list[str] = []
    diagnosed_by: UUID
    actor_role: str


class CreateServiceOrderIn(BaseModel):
    diagnosis_id: UUID
    service_type_id: UUID
    ordered_by: UUID
    actor_role: str


def _create_diagnosis(params: CreateDiagnosisIn, repo: Repository) -> dict:
    if params.actor_role != DOCTOR_ROLE:  # BR-05 / CO-02
        raise ToolError(f"only {DOCTOR_ROLE} may create a diagnosis - BR-05")
    appointment = repo.get(Appointment, params.appointment_id)
    if appointment is None:
        raise ToolError("appointment_id does not reference a recorded Appointment")
    diagnosis = repo.save(
        Diagnosis(
            patient_id=appointment.patient_id,  # denormalized from Appointment (TASK-016)
            appointment_id=params.appointment_id,
            conditions=list(params.conditions),
            diagnosed_by=params.diagnosed_by,
        )
    )
    return {"diagnosis_id": str(diagnosis.id)}


def _create_service_order(params: CreateServiceOrderIn, repo: Repository) -> dict:
    # BR-05 doctor-only is enforced by the constraint checker's `create_service_order` rule before
    # this handler ever runs (ActionExecutor.execute step 2). This handler validates the clinical
    # reference: "each ServiceOrder references a valid ServiceType" (FR-03 input/output table).
    service_type = repo.get(ServiceType, params.service_type_id)
    if service_type is None:
        raise ToolError("service_type_id does not reference a valid ServiceType")
    diagnosis = repo.get(Diagnosis, params.diagnosis_id)
    if diagnosis is None:
        raise ToolError("diagnosis_id does not reference a recorded Diagnosis")
    order = repo.save(
        ServiceOrder(
            patient_id=diagnosis.patient_id,  # denormalized from Diagnosis (TASK-016)
            diagnosis_id=params.diagnosis_id,
            service_type_id=params.service_type_id,
            ordered_by=params.ordered_by,
        )
    )
    return {"service_order_id": str(order.id)}


def build_create_diagnosis_tool() -> Tool:
    return Tool("create_diagnosis", CreateDiagnosisIn, _create_diagnosis)


def build_create_service_order_tool() -> Tool:
    return Tool("create_service_order", CreateServiceOrderIn, _create_service_order)


@dataclass(frozen=True)
class CaptureResult:
    """The outcome of capturing one diagnosis plus its service orders (AC-03.1 / AC-03.2)."""

    diagnosis_result: ActionResult
    order_results: list[ActionResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.diagnosis_result.ok and all(r.ok for r in self.order_results)

    @property
    def diagnosis_id(self) -> UUID | None:
        if not self.diagnosis_result.ok or self.diagnosis_result.output is None:
            return None
        return UUID(self.diagnosis_result.output["diagnosis_id"])


def capture_diagnosis_and_orders(
    executor: ActionExecutor,
    actor: str,
    appointment_id: UUID,
    conditions: list[str],
    diagnosed_by: UUID,
    actor_role: str,
    service_type_ids: list[UUID],
    reasoning: str = "",
) -> CaptureResult:
    """Record a diagnosis and its service orders through the guarded spine (AC-03.1).

    Every write is routed through `ActionExecutor` so it is constraint-checked and audit-logged
    (BR-05). On success this is the trigger point for FR-04: the caller passes the resulting
    `Diagnosis` and `ServiceOrder`s into `generate_care_plan`.
    """
    diagnosis_result = executor.execute(
        Action(
            tool="create_diagnosis",
            actor=actor,
            reasoning=reasoning,
            params={
                "appointment_id": appointment_id,
                "conditions": conditions,
                "diagnosed_by": diagnosed_by,
                "actor_role": actor_role,
            },
        )
    )

    order_results: list[ActionResult] = []
    if diagnosis_result.ok and diagnosis_result.output is not None:
        diagnosis_id = UUID(diagnosis_result.output["diagnosis_id"])
        for service_type_id in service_type_ids:
            order_results.append(
                executor.execute(
                    Action(
                        tool="create_service_order",
                        actor=actor,
                        reasoning=reasoning,
                        params={
                            "diagnosis_id": diagnosis_id,
                            "service_type_id": service_type_id,
                            "ordered_by": diagnosed_by,
                            "actor_role": actor_role,
                        },
                    )
                )
            )

    return CaptureResult(diagnosis_result=diagnosis_result, order_results=order_results)

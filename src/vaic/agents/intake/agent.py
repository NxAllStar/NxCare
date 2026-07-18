"""The Intake Agent and its two tools: `book_appointment` and `escalate_emergency`.

Intake defines its own tools inside this package (D2) and never calls the constraint checker or
audit log directly - every consequential action routes through the injected `ActionExecutor`, which
is what makes it checked and audited (D1). The constraint checker has no intake-specific rule today
(D3), so capacity, staff-confirmation, and emergency-bypass guards live in the tool handlers below;
a guard violation raises `ToolError`, which the executor turns into an audited `FAILED:<tool>`
entry (D10) - a denial is never silent.

Intake NEVER transitions an `Appointment` to `BOOKED` on its own authority (D9, BR-02): booking
requires both `staff_confirmed=True` (set by a `role_coordinator` action, out of this lane's scope)
and `emergency_suspected=False`. Rejecting confirmation leaves the appointment unbooked; intake only
consumes the confirmation signal, it does not create the desk-confirmation UI.

No transcript text or PII ever crosses into an `Action.reasoning`, a tool param, or an audit entry
(D8): `escalate_emergency`'s input schema deliberately excludes a transcript field, and neither
handler below echoes anything beyond IDs and enum-like codes into its return value.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ...models import Appointment, AppointmentStatus, Resource
from ...models.transitions import APPOINTMENT_TRANSITIONS, assert_transition
from ...state import Repository, owner_queue
from ...tools import Action, ActionResult, Tool, ToolError, ToolRegistry
from ..core import ActionExecutor, Agent

# Deterministic UTC reference date the demo books hours against (FR-02 slot recommendation deals
# only in hour-of-day, 0-23 - see `RetrievedFeatures.hour` in `vaic.forecast.features`). Fixed and
# UTC so `slot_start` is reproducible and never timezone-ambiguous; a real deployment would derive
# the calendar day from the actual booking request instead of this placeholder.
_BOOKING_REFERENCE_DATE = datetime(2026, 1, 1, tzinfo=UTC)


class BookAppointmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: UUID
    specialty: str
    owner_id: UUID
    hour: int
    staff_confirmed: bool = False
    emergency_suspected: bool = False


class EscalateEmergencyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: UUID
    specialty: str


def _book_appointment(params: BookAppointmentInput, repo: Repository) -> dict[str, Any]:
    """Guard order (D9/D10): emergency bypass, then capacity/availability, then confirmation.

    Any violation raises `ToolError` so the executor audits it as `FAILED:book_appointment` with a
    reason - no Appointment is created or mutated on a failed guard.
    """
    if params.emergency_suspected:
        raise ToolError(
            "booking blocked: emergency suspected - route through escalate_emergency, not "
            "routine booking (AC-01.2)"
        )

    resource = repo.get(Resource, params.owner_id)
    if resource is None or not resource.is_available:
        raise ToolError("booking blocked: resource unavailable (BR-16)")
    if resource.capacity_per_hour is not None:
        # B1 (code-reviewer, Major - tracked as a cross-lane follow-up, not fixed here): this guard
        # counts the owner's Task queue (`owner_queue`), not booked Appointments. A confirmed
        # Appointment has no owner_id/slot link in the current entity shape (data-model gap, spec
        # 08-data-model.md), so it never enters `owner_queue` - N confirmed bookings can still pile
        # onto one owner/hour. This check enforces Task-driven capacity only, not full
        # per-owner-per-hour appointment capacity; closing it needs an Appointment<->owner/slot link
        # (data-modeler) before this booking path is relied on for real capacity control.
        queue_length = len(owner_queue(repo, params.owner_id))
        if queue_length >= resource.capacity_per_hour:
            raise ToolError("booking blocked: resource is at or over capacity (BR-04)")

    if not params.staff_confirmed:
        raise ToolError(
            "booking blocked: no staff confirmation on record - intake never self-books (BR-02, D9)"
        )

    # FR-02: a chosen slot creates a PROPOSED -> BOOKED Appointment, moved through the transition
    # validator - never born directly in BOOKED (spec 08-data-model.md state machine).
    appointment = repo.save(
        Appointment(
            patient_id=params.patient_id,
            specialty=params.specialty,
            status=AppointmentStatus.PROPOSED,
        )
    )
    assert_transition(APPOINTMENT_TRANSITIONS, appointment.status, AppointmentStatus.BOOKED)
    slot_start = _BOOKING_REFERENCE_DATE + timedelta(hours=params.hour)
    booked_update = {"status": AppointmentStatus.BOOKED, "slot_start": slot_start}
    appointment = repo.save(appointment.model_copy(update=booked_update))
    return {"appointment_id": str(appointment.id), "status": appointment.status.value}


def _escalate_emergency(params: EscalateEmergencyInput, repo: Repository) -> dict[str, Any]:
    """Record an emergency escalation and bypass normal booking entirely (BF-05).

    The input schema (`extra="forbid"`, no `transcript` field) structurally keeps transcript text
    out of this call - and therefore out of the audit trail (D8, NFR-SEC-11). This is the
    escalation MECHANISM only; the clinical red-flag content that triggers it is OI-09-pending
    (owner SH-02), not this lane's authority. A human confirms the candidate red flag (BF-05).
    """
    # No state mutation: the escalation itself is what the executor's audit entry records. `repo`
    # is accepted only to match the `Tool` handler signature shared by every tool.
    return {
        "patient_id": str(params.patient_id),
        "specialty": params.specialty,
        "status": "ESCALATED",
    }


def build_intake_registry(repo: Repository) -> ToolRegistry:
    """Build the closed action space for the Intake Agent: `book_appointment`, `escalate_emergency`.

    `repo` is accepted to match the shape every other lane's registry factory uses and so a future
    intake-owned lookup tool can be added here without changing the call site; the two tools above
    receive their repository from `Tool.run` on every call regardless.
    """
    registry = ToolRegistry()
    registry.register(Tool("book_appointment", BookAppointmentInput, _book_appointment))
    registry.register(Tool("escalate_emergency", EscalateEmergencyInput, _escalate_emergency))
    return registry


class IntakeAgent(Agent):
    """Conversational triage agent (FR-01/FR-02/BF-05) wired to an injected `ActionExecutor`.

    `perceive`/`reason` are the framework hooks (D1); this lane's conversational reasoning over a
    triage transcript happens through `extract_triage`/`recommend_slots` ahead of producing an
    `Action`, so both hooks here stay intentionally minimal - callers construct `Action`s directly
    (see `tests/test_intake.py`) and drive them through `agent.act`.
    """

    def __init__(self, name: str, executor: ActionExecutor) -> None:
        super().__init__(name=name, executor=executor)

    def perceive(self, event: Any) -> Any:
        return event

    def reason(self, perception: Any) -> list[Action]:
        return []

    def act(self, action: Action) -> ActionResult:
        return super().act(action)

"""State machines from docs/specs/08-data-model.md, plus a validator.

A state machine drawn here is one QA can test; illegal transitions raise rather than silently
corrupting state.
"""

from __future__ import annotations

from .enums import (
    AppointmentStatus,
    CarePlanStatus,
    DisruptionStatus,
    ExecutionStatus,
    QueueTicketStatus,
)


class InvalidTransition(ValueError):
    """Raised when a state change is not allowed by the machine."""


TASK_TRANSITIONS: dict[ExecutionStatus, set[ExecutionStatus]] = {
    ExecutionStatus.LOCKED: {ExecutionStatus.PENDING, ExecutionStatus.CANCELLED},
    ExecutionStatus.PENDING: {ExecutionStatus.IN_PROGRESS, ExecutionStatus.CANCELLED},
    ExecutionStatus.IN_PROGRESS: {ExecutionStatus.DONE, ExecutionStatus.CANCELLED},
    ExecutionStatus.DONE: set(),
    ExecutionStatus.CANCELLED: set(),
}

APPOINTMENT_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.PROPOSED: {AppointmentStatus.BOOKED, AppointmentStatus.CANCELLED},
    AppointmentStatus.BOOKED: {
        AppointmentStatus.CHECKED_IN,
        AppointmentStatus.NO_SHOW,
        AppointmentStatus.CANCELLED,
    },
    AppointmentStatus.CHECKED_IN: {AppointmentStatus.IN_CONSULT, AppointmentStatus.CANCELLED},
    AppointmentStatus.IN_CONSULT: {AppointmentStatus.DONE},
    AppointmentStatus.DONE: set(),
    AppointmentStatus.NO_SHOW: set(),
    AppointmentStatus.CANCELLED: set(),
}

QUEUE_TICKET_TRANSITIONS: dict[QueueTicketStatus, set[QueueTicketStatus]] = {
    # ADR-003. WAITING -> CALLED when a free room calls the next number; CALLED -> IN_SERVICE
    # when the patient presents (FR-17 scan). SKIPPED is a called-but-absent patient, who may be
    # re-called (back to WAITING) once they turn up.
    QueueTicketStatus.WAITING: {QueueTicketStatus.CALLED, QueueTicketStatus.SKIPPED},
    QueueTicketStatus.CALLED: {
        QueueTicketStatus.IN_SERVICE,
        QueueTicketStatus.SKIPPED,
        QueueTicketStatus.WAITING,
    },
    QueueTicketStatus.IN_SERVICE: {QueueTicketStatus.DONE},
    QueueTicketStatus.SKIPPED: {QueueTicketStatus.WAITING},
    QueueTicketStatus.DONE: set(),
}

CAREPLAN_TRANSITIONS: dict[CarePlanStatus, set[CarePlanStatus]] = {
    CarePlanStatus.DRAFT: {CarePlanStatus.ACTIVE},
    CarePlanStatus.ACTIVE: {CarePlanStatus.COMPLETED},
    CarePlanStatus.COMPLETED: set(),
}

DISRUPTION_TRANSITIONS: dict[DisruptionStatus, set[DisruptionStatus]] = {
    DisruptionStatus.DETECTED: {DisruptionStatus.ASSESSED},
    DisruptionStatus.ASSESSED: {
        DisruptionStatus.AUTO_RESOLVED,
        DisruptionStatus.PENDING_APPROVAL,
    },
    DisruptionStatus.PENDING_APPROVAL: {DisruptionStatus.APPROVED, DisruptionStatus.REJECTED},
    DisruptionStatus.AUTO_RESOLVED: set(),
    DisruptionStatus.APPROVED: set(),
    DisruptionStatus.REJECTED: set(),
}


def can_transition(machine: dict, frm, to) -> bool:
    return to in machine.get(frm, set())


def assert_transition(machine: dict, frm, to) -> None:
    """Raise InvalidTransition if `frm -> to` is not allowed by `machine`."""
    if not can_transition(machine, frm, to):
        raise InvalidTransition(f"illegal transition {frm.value} -> {to.value}")

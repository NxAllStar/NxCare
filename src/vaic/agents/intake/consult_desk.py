"""Staff/front-desk actions on the consult queue: call the next patient, finish a visit, or put a
called-but-absent patient back in the queue - the write side of `patient_status.py`'s read side.

Both state machines - `APPOINTMENT_TRANSITIONS` and `QUEUE_TICKET_TRANSITIONS`
(docs/specs/08-data-model.md) - are walked through `assert_transition`, never bypassed: a hop this
module does not explicitly allow raises `InvalidTransition` rather than silently corrupting state.

- `call_next_patient`    - the next WAITING ticket (ADR-003 serving order) becomes CALLED, and its
                           Appointment walks forward to CHECKED_IN, binding `owner_id` to the
                           calling doctor for the first time (call-time binding, ADR-003).
- `complete_appointment` - the ticket finishes CALLED -> IN_SERVICE -> DONE; the Appointment walks
                           its remaining hops (CHECKED_IN -> IN_CONSULT -> DONE, or fewer if some
                           already happened) to DONE.
- `requeue_no_show`      - the patient did not appear when called: the SAME ticket goes straight
                           back CALLED -> WAITING (a legal single hop already in
                           `QUEUE_TICKET_TRANSITIONS`) with a fresh `issued_at` - product decision
                           is "push to the back of the line", not "keep their old spot". The
                           Appointment is left exactly as it is: `CHECKED_IN` has no legal path to
                           `NO_SHOW` in the state machine, and the ticket alone - not the
                           Appointment status - is what "in queue right now" actually means here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from ...models import (
    APPOINTMENT_TRANSITIONS,
    QUEUE_TICKET_TRANSITIONS,
    Appointment,
    AppointmentStatus,
    InvalidTransition,
    QueueSubjectType,
    QueueTicket,
    QueueTicketStatus,
    assert_transition,
)
from ...state import Repository
from .patient_status import ACTIVE_TICKET_STATUSES, ticket_sort_key


class ConsultDeskError(Exception):
    """Raised when a staff action cannot proceed: nothing waiting, or a ticket/appointment id that
    does not resolve to a real entity. Distinct from `InvalidTransition` (a real entity in a state
    that cannot legally reach the requested one)."""


@dataclass(frozen=True)
class CalledPatient:
    """Who just got called, and which doctor is now bound to their appointment."""

    ticket_id: UUID
    ticket_label: str
    patient_id: UUID
    appointment_id: UUID
    owner_id: UUID


# Each state machine here is strictly linear (no branching) along its "happy path" - CANCELLED and
# NO_SHOW are terminal side-branches this module never takes. `_advance` walks every hop between
# two points on one of these tuples, so "jump three tickets to DONE" is checked one legal hop at a
# time, not assumed.
_APPOINTMENT_HAPPY_PATH = (
    AppointmentStatus.PROPOSED,
    AppointmentStatus.BOOKED,
    AppointmentStatus.CHECKED_IN,
    AppointmentStatus.IN_CONSULT,
    AppointmentStatus.DONE,
)

_TICKET_SERVICE_PATH = (
    QueueTicketStatus.WAITING,
    QueueTicketStatus.CALLED,
    QueueTicketStatus.IN_SERVICE,
    QueueTicketStatus.DONE,
)


def _advance(machine: dict, happy_path: tuple, current, target) -> None:
    """Raise `InvalidTransition` unless every hop from `current` to `target` on `happy_path` is
    legal in `machine`. A no-op when `current == target` (already there).

    `current` not being on `happy_path` at all (a terminal side-branch like CANCELLED) or being
    past `target` already both raise - `happy_path.index` alone would either raise a raw
    `ValueError` or silently walk backward, neither of which is the "handled outcome" this module
    aims for (code-quality.md "no silent failures").
    """
    if current not in happy_path:
        raise InvalidTransition(f"{current} is not on the path toward {target}")
    start, end = happy_path.index(current), happy_path.index(target)
    if start > end:
        raise InvalidTransition(f"cannot advance backward from {current} to {target}")
    for frm, to in zip(happy_path[start:end], happy_path[start + 1 : end + 1], strict=True):
        assert_transition(machine, frm, to)


def call_next_patient(
    repo: Repository, department_id: UUID, owner_id: UUID
) -> CalledPatient | None:
    """Call the next WAITING consult ticket in `department_id` (ADR-003 order: priority, then FIFO).

    Returns `None` when nobody is waiting - not an error, just an empty queue. Idempotent-safe to
    call again for an already-CHECKED_IN appointment (e.g. re-calling a requeued ticket): `owner_id`
    is simply overwritten to whichever doctor calls this time.
    """
    waiting = [
        t
        for t in repo.list(
            QueueTicket, department_id=department_id, subject_type=QueueSubjectType.CONSULT
        )
        if t.status is QueueTicketStatus.WAITING
    ]
    if not waiting:
        return None
    ticket = min(waiting, key=ticket_sort_key)

    assert_transition(QUEUE_TICKET_TRANSITIONS, ticket.status, QueueTicketStatus.CALLED)
    ticket = repo.save(
        ticket.model_copy(
            update={
                "status": QueueTicketStatus.CALLED,
                "called_by_owner_id": owner_id,
                "called_at": datetime.now(UTC),
            }
        )
    )

    appointment = repo.get(Appointment, ticket.subject_id)
    if appointment is None:
        raise ConsultDeskError(f"ticket {ticket.id} has no matching appointment")
    _advance(
        APPOINTMENT_TRANSITIONS,
        _APPOINTMENT_HAPPY_PATH,
        appointment.status,
        AppointmentStatus.CHECKED_IN,
    )
    appointment = repo.save(
        appointment.model_copy(
            update={"status": AppointmentStatus.CHECKED_IN, "owner_id": owner_id}
        )
    )

    return CalledPatient(
        ticket_id=ticket.id,
        ticket_label=ticket.ticket_label,
        patient_id=ticket.patient_id,
        appointment_id=appointment.id,
        owner_id=owner_id,
    )


_CALLED_IN_STATUSES = (AppointmentStatus.CHECKED_IN, AppointmentStatus.IN_CONSULT)


def complete_appointment(repo: Repository, appointment_id: UUID) -> Appointment:
    """Finish the visit: the Appointment reaches DONE, and its live ticket (if any) reaches DONE.

    Raises `ConsultDeskError` if the appointment has not been called in yet (still PROPOSED or
    BOOKED): the state machine alone does not forbid a PROPOSED -> ... -> DONE walk (every hop on
    it is individually legal), so this precondition is an explicit business-rule check, not a
    transition-legality one - there is no such thing as completing a visit nobody started.
    """
    appointment = repo.get(Appointment, appointment_id)
    if appointment is None:
        raise ConsultDeskError(f"no appointment {appointment_id}")
    if appointment.status not in _CALLED_IN_STATUSES:
        raise ConsultDeskError(
            f"appointment {appointment_id} was never called in (status={appointment.status.value})"
        )

    _advance(
        APPOINTMENT_TRANSITIONS, _APPOINTMENT_HAPPY_PATH, appointment.status, AppointmentStatus.DONE
    )
    appointment = repo.save(appointment.model_copy(update={"status": AppointmentStatus.DONE}))

    tickets = repo.list(
        QueueTicket, subject_type=QueueSubjectType.CONSULT, subject_id=appointment_id
    )
    ticket = next((t for t in tickets if t.status in ACTIVE_TICKET_STATUSES), None)
    if ticket is not None:
        _advance(
            QUEUE_TICKET_TRANSITIONS, _TICKET_SERVICE_PATH, ticket.status, QueueTicketStatus.DONE
        )
        repo.save(ticket.model_copy(update={"status": QueueTicketStatus.DONE}))

    return appointment


def requeue_no_show(repo: Repository, ticket_id: UUID) -> QueueTicket:
    """The called patient did not show: put the SAME ticket back to WAITING with a fresh number.

    See the module docstring for why the Appointment is left untouched.
    """
    ticket = repo.get(QueueTicket, ticket_id)
    if ticket is None:
        raise ConsultDeskError(f"no ticket {ticket_id}")

    assert_transition(QUEUE_TICKET_TRANSITIONS, ticket.status, QueueTicketStatus.WAITING)
    return repo.save(
        ticket.model_copy(
            update={
                "status": QueueTicketStatus.WAITING,
                "issued_at": datetime.now(UTC),
                "called_by_owner_id": None,
                "called_at": None,
            }
        )
    )

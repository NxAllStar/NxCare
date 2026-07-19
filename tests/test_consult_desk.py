"""Tests for staff/front-desk consult-queue actions: call next, complete, requeue no-show.

Covers both state machines moving together (Appointment + QueueTicket) and the illegal-transition
guards - all against `InMemoryRepository`, no network involved.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from vaic.agents.intake.consult_desk import (
    ConsultDeskError,
    call_next_patient,
    complete_appointment,
    requeue_no_show,
)
from vaic.agents.intake.patient_status import issue_consult_ticket
from vaic.models import (
    Appointment,
    AppointmentStatus,
    Department,
    InvalidTransition,
    PriorityLevel,
    QueueTicketStatus,
)
from vaic.state import InMemoryRepository

ANCHOR = datetime(2026, 7, 20, 8, 0, tzinfo=UTC)


def _department(repo: InMemoryRepository) -> Department:
    return repo.save(Department(code="DepA", display_label="General Medicine"))


def _booked_appointment(repo: InMemoryRepository, patient_id) -> Appointment:
    return repo.save(
        Appointment(
            patient_id=patient_id, specialty="NOI_TONG_QUAT", status=AppointmentStatus.PROPOSED
        )
    )


def _waiting_ticket(repo, dept, patient_id, *, issued_at=ANCHOR):
    appointment = _booked_appointment(repo, patient_id)
    return issue_consult_ticket(
        repo, dept, appointment.id, patient_id, PriorityLevel.ROUTINE, issued_at=issued_at
    ), appointment


# ---- call_next_patient -----------------------------------------------------------------------


def test_call_next_patient_returns_none_when_nobody_waiting():
    repo = InMemoryRepository()
    dept = _department(repo)

    result = call_next_patient(repo, dept.id, uuid4())

    assert result is None


def test_call_next_patient_picks_earliest_and_binds_owner():
    repo = InMemoryRepository()
    dept = _department(repo)
    owner_id = uuid4()
    _first_ticket, first_appt = _waiting_ticket(repo, dept, uuid4(), issued_at=ANCHOR)
    _waiting_ticket(repo, dept, uuid4(), issued_at=ANCHOR + timedelta(minutes=5))

    called = call_next_patient(repo, dept.id, owner_id)

    assert called is not None
    assert called.appointment_id == first_appt.id
    assert called.owner_id == owner_id

    ticket = repo.get(type(_first_ticket), called.ticket_id)
    assert ticket.status is QueueTicketStatus.CALLED
    assert ticket.called_by_owner_id == owner_id

    appointment = repo.get(Appointment, first_appt.id)
    assert appointment.status is AppointmentStatus.CHECKED_IN
    assert appointment.owner_id == owner_id


def test_call_next_patient_ignores_already_called_tickets():
    repo = InMemoryRepository()
    dept = _department(repo)
    ticket, _appt = _waiting_ticket(repo, dept, uuid4())
    call_next_patient(repo, dept.id, uuid4())  # calls the only ticket, now CALLED

    result = call_next_patient(repo, dept.id, uuid4())

    assert result is None


# ---- complete_appointment --------------------------------------------------------------------


def test_complete_appointment_marks_appointment_and_ticket_done():
    repo = InMemoryRepository()
    dept = _department(repo)
    _ticket, appt = _waiting_ticket(repo, dept, uuid4())
    called = call_next_patient(repo, dept.id, uuid4())

    result = complete_appointment(repo, appt.id)

    assert result.status is AppointmentStatus.DONE
    saved_ticket = repo.get(type(_ticket), called.ticket_id)
    assert saved_ticket.status is QueueTicketStatus.DONE


def test_complete_appointment_raises_when_never_called():
    repo = InMemoryRepository()
    appointment = _booked_appointment(repo, uuid4())  # still PROPOSED, never called

    with pytest.raises(ConsultDeskError):
        complete_appointment(repo, appointment.id)


def test_complete_appointment_raises_for_unknown_id():
    repo = InMemoryRepository()

    with pytest.raises(ConsultDeskError):
        complete_appointment(repo, uuid4())


# ---- requeue_no_show --------------------------------------------------------------------------


def test_requeue_no_show_returns_same_ticket_to_waiting_with_fresh_issued_at():
    repo = InMemoryRepository()
    dept = _department(repo)
    ticket, appt = _waiting_ticket(repo, dept, uuid4(), issued_at=ANCHOR)
    called = call_next_patient(repo, dept.id, uuid4())
    original_label = called.ticket_label

    requeued = requeue_no_show(repo, called.ticket_id)

    assert requeued.id == called.ticket_id  # same ticket, not a new one
    assert requeued.ticket_label == original_label  # same number
    assert requeued.status is QueueTicketStatus.WAITING
    assert requeued.issued_at != ANCHOR  # pushed to a fresh spot, not kept at the original one
    assert requeued.called_by_owner_id is None
    assert requeued.called_at is None

    # the Appointment is left untouched (still CHECKED_IN from the call)
    appointment = repo.get(Appointment, appt.id)
    assert appointment.status is AppointmentStatus.CHECKED_IN


def test_requeue_no_show_can_be_called_again_later():
    repo = InMemoryRepository()
    dept = _department(repo)
    _waiting_ticket(repo, dept, uuid4(), issued_at=ANCHOR)
    first_owner = uuid4()
    called = call_next_patient(repo, dept.id, first_owner)
    requeue_no_show(repo, called.ticket_id)

    second_owner = uuid4()
    recalled = call_next_patient(repo, dept.id, second_owner)

    assert recalled is not None
    assert recalled.ticket_id == called.ticket_id
    assert recalled.owner_id == second_owner


def test_requeue_no_show_raises_for_unknown_ticket():
    repo = InMemoryRepository()

    with pytest.raises(ConsultDeskError):
        requeue_no_show(repo, uuid4())


def test_requeue_no_show_raises_when_ticket_not_called():
    repo = InMemoryRepository()
    dept = _department(repo)
    ticket, _appt = _waiting_ticket(repo, dept, uuid4())  # still WAITING, never called

    with pytest.raises(InvalidTransition):
        requeue_no_show(repo, ticket.id)

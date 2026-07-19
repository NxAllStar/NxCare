"""Tests for the consult-queue demo seed (dev-only synthetic data, AS-03).

`seed_consult_queue_demo` is what makes `/queue` and `/status` show non-zero numbers on a fresh
app start without confirming several appointments by hand first.
"""

from __future__ import annotations

from vaic.api.demo_state import (
    _CONSULT_QUEUE_SEED,
    ARRIVAL_DEPARTMENT_ID,
    seed_arrival_demo,
    seed_consult_queue_demo,
)
from vaic.models import Appointment, QueueSubjectType, QueueTicket, QueueTicketStatus
from vaic.state import InMemoryRepository


def test_seed_consult_queue_demo_creates_one_ticket_per_seed_entry():
    repo = InMemoryRepository()
    seed_arrival_demo(repo)

    seed_consult_queue_demo(repo)

    tickets = repo.list(
        QueueTicket, department_id=ARRIVAL_DEPARTMENT_ID, subject_type=QueueSubjectType.CONSULT
    )
    assert len(tickets) == len(_CONSULT_QUEUE_SEED)
    assert all(t.status is QueueTicketStatus.WAITING for t in tickets)


def test_seed_consult_queue_demo_is_idempotent():
    repo = InMemoryRepository()
    seed_arrival_demo(repo)
    seed_consult_queue_demo(repo)

    seed_consult_queue_demo(repo)  # simulate a second app start against the same store

    tickets = repo.list(
        QueueTicket, department_id=ARRIVAL_DEPARTMENT_ID, subject_type=QueueSubjectType.CONSULT
    )
    assert len(tickets) == len(_CONSULT_QUEUE_SEED)


def test_seed_consult_queue_demo_noop_before_department_exists():
    repo = InMemoryRepository()

    seed_consult_queue_demo(repo)  # seed_arrival_demo was never called

    tickets = repo.list(QueueTicket, subject_type=QueueSubjectType.CONSULT)
    assert tickets == []


def test_seed_consult_queue_demo_tickets_resolve_to_a_real_appointment():
    """Regression guard: call_next_patient dereferences ticket.subject_id, so every seeded ticket
    needs a real Appointment behind it, not just a random id."""
    repo = InMemoryRepository()
    seed_arrival_demo(repo)

    seed_consult_queue_demo(repo)

    tickets = repo.list(
        QueueTicket, department_id=ARRIVAL_DEPARTMENT_ID, subject_type=QueueSubjectType.CONSULT
    )
    for ticket in tickets:
        appointment = repo.get(Appointment, ticket.subject_id)
        assert appointment is not None
        assert appointment.patient_id == ticket.patient_id

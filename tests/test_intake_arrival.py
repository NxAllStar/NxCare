"""Tests for the pre-arrival "best time to come" recommendation and confirmation (extends FR-02).

Proves the acceptance the feature promises: rank suggested arrival times least-crowded-then-soonest
(AC-02.1), cap at the top 3, never suggest an unavailable owner (BR-16) or a full slot (BR-04),
return an empty list rather than error when nothing fits (AC-02.2), and persist an accepted slot as
a PROPOSED Appointment (the "log into DB for later use" step). The forecast provider is stubbed to
raise, so every ETA comes from the tested BASELINE fallback - no network call (a real call would be
a defect, testing.md).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from vaic.agents.intake.arrival import (
    confirm_arrival_slot,
    recommend_arrival_slots,
)
from vaic.forecast import ForecastLLMError
from vaic.models import Appointment, AppointmentStatus, Resource, ResourceType
from vaic.state import InMemoryRepository

ANCHOR = datetime(2026, 7, 20, 0, 0, tzinfo=UTC)  # a fixed midnight, for deterministic slot grids
HOURS = [8, 9, 10]


class _StubForecastLLM:
    """Always fails, so estimate_wait falls back to the deterministic BASELINE path (BR-03)."""

    def estimate_wait(self, features: dict) -> dict:
        del features
        raise ForecastLLMError("no forecast provider in test")


def _doctor(repo: InMemoryRepository, *, capacity: int | None = 6, available: bool = True) -> UUID:
    resource = repo.save(
        Resource(
            type=ResourceType.DOCTOR,
            department_id=uuid4(),
            is_available=available,
            capacity_per_hour=capacity,
        )
    )
    return resource.id


def _appt(
    repo: InMemoryRepository,
    owner_id: UUID,
    start: datetime,
    status: AppointmentStatus = AppointmentStatus.PROPOSED,
) -> None:
    repo.save(
        Appointment(
            patient_id=uuid4(),
            specialty="NOI_TONG_QUAT",
            owner_id=owner_id,
            slot_start=start,
            status=status,
        )
    )


def _recommend(repo: InMemoryRepository, owners: list[UUID], **kw):
    return recommend_arrival_slots(
        repo,
        "NOI_TONG_QUAT",
        owners,
        ANCHOR,
        days=kw.get("days", 1),
        hours=kw.get("hours", HOURS),
        llm=_StubForecastLLM(),
        top_n=kw.get("top_n", 3),
    )


def test_returns_at_most_top_n():
    repo = InMemoryRepository()
    owners = [_doctor(repo), _doctor(repo)]  # 2 owners x 3 hours x 1 day = 6 candidate slots

    result = _recommend(repo, owners, top_n=3)

    assert len(result) == 3


def test_least_crowded_slot_ranked_first():
    repo = InMemoryRepository()
    owner = _doctor(repo)
    # 8:00 already has three people; 9:00 and 10:00 are empty.
    for _ in range(3):
        _appt(repo, owner, ANCHOR + timedelta(hours=8))

    result = _recommend(repo, [owner])

    assert result[0].participants == 0
    assert result[0].start == ANCHOR + timedelta(hours=9)  # emptiest, and the soonest empty one
    assert result[-1].start == ANCHOR + timedelta(hours=8)  # the crowded slot sinks to the bottom


def test_ties_break_by_soonest():
    repo = InMemoryRepository()
    owner = _doctor(repo)  # every slot empty -> all tie on participants

    result = _recommend(repo, [owner])

    starts = [slot.start for slot in result]
    assert starts == sorted(starts)  # equal crowding -> ascending by time (nearest first)


def test_skips_unavailable_owner():
    repo = InMemoryRepository()
    up = _doctor(repo, available=True)
    down = _doctor(repo, available=False)

    result = _recommend(repo, [up, down], top_n=10)

    assert result  # the available owner still yields slots
    assert all(slot.owner_id == up for slot in result)


def test_skips_full_slot():
    repo = InMemoryRepository()
    owner = _doctor(repo, capacity=2)
    for _ in range(2):  # 8:00 is now at capacity
        _appt(repo, owner, ANCHOR + timedelta(hours=8))

    result = _recommend(repo, [owner], hours=[8, 9])

    assert all(slot.start != ANCHOR + timedelta(hours=8) for slot in result)


def test_cancelled_appointment_does_not_count_as_participant():
    repo = InMemoryRepository()
    owner = _doctor(repo)
    _appt(repo, owner, ANCHOR + timedelta(hours=8), status=AppointmentStatus.CANCELLED)

    result = _recommend(repo, [owner], hours=[8])

    assert result[0].participants == 0  # a cancelled appointment frees the slot


def test_empty_when_no_candidates():
    repo = InMemoryRepository()

    assert _recommend(repo, []) == []


def test_confirm_persists_proposed_appointment():
    repo = InMemoryRepository()
    owner = _doctor(repo)
    patient = uuid4()
    start = ANCHOR + timedelta(hours=9)

    appointment = confirm_arrival_slot(repo, patient, "NOI_TONG_QUAT", owner, start)

    assert appointment.owner_id == owner
    assert appointment.slot_start == start
    assert appointment.status == AppointmentStatus.PROPOSED
    stored = repo.get(Appointment, appointment.id)
    assert stored is not None and stored.patient_id == patient


def test_confirmed_slot_then_counts_as_a_participant():
    repo = InMemoryRepository()
    owner = _doctor(repo)
    start = ANCHOR + timedelta(hours=9)

    confirm_arrival_slot(repo, uuid4(), "NOI_TONG_QUAT", owner, start)
    result = _recommend(repo, [owner], hours=[9])

    assert result[0].participants == 1  # the just-confirmed arrival is now on record for later use

"""Pre-arrival "best time to come" recommendation and confirmation (extends FR-02).

The patient chats before coming to the hospital; the agent suggests when to arrive to wait the
least. Two pure-ish operations:

- `recommend_arrival_slots` - a read-only query. Over a window of the next `days` x `hours`, it
  counts how many appointments are already scheduled with each candidate owner at each slot (the
  "participants"), ranks least-crowded-then-soonest, and returns the top N. This is the concrete
  form of FR-02's least-crowded goal, and it counts booked `Appointment`s directly - which only
  became possible once ADR-003 gave `Appointment` an `owner_id` (closing the B1 data-model gap that
  `recommend_slots`/`_book_appointment` both flag). Every ETA still comes from the forecast tool's
  `estimate_wait` (BR-03); this module never invents a wait number, it only counts and ranks.

- `confirm_arrival_slot` - the one write. When the patient accepts a suggestion, it persists an
  `Appointment` with the chosen `slot_start` (a recommended arrival window per ADR-003, not a hard
  reservation) so the choice is on record for later use. It does NOT book the consult (`BOOKED`
  needs staff confirmation, BR-02): the appointment is created `PROPOSED`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from ...forecast import ForecastLLM, estimate_wait
from ...models import Appointment, AppointmentStatus, Resource
from ...state import Repository

# An appointment in one of these states no longer occupies its slot, so it is not a "participant"
# the arriving patient would wait behind.
_INACTIVE_STATUSES = (AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW)


@dataclass(frozen=True)
class ArrivalSlot:
    """A suggested arrival time for an owner: how crowded it already is, plus a grounded ETA."""

    owner_id: UUID
    start: datetime
    participants: int  # appointments already scheduled with this owner at this slot
    eta_minutes: float  # from the forecast tool only (BR-03)
    eta_source: str


def _participants_at(repo: Repository, owner_id: UUID, start: datetime) -> int:
    """How many active appointments are already scheduled with `owner_id` at exactly `start`."""
    return sum(
        1
        for appointment in repo.list(Appointment, owner_id=owner_id)
        if appointment.slot_start == start and appointment.status not in _INACTIVE_STATUSES
    )


def recommend_arrival_slots(
    repo: Repository,
    specialty: str,
    candidate_owner_ids: list[UUID],
    start_from: datetime,
    *,
    days: int,
    hours: list[int],
    llm: ForecastLLM,
    top_n: int = 3,
) -> list[ArrivalSlot]:
    """Rank candidate arrival slots least-crowded-then-soonest and return the top `top_n` (AC-02.1).

    `specialty` is carried for traceability only - the caller has already mapped specialty ->
    `candidate_owner_ids`, exactly as `recommend_slots` documents. Slots are generated on a grid of
    the next `days` calendar days (from the midnight of `start_from`) x each hour in `hours`.

    A candidate owner that is unavailable is skipped (BR-16); a slot already at/over the owner's
    hourly capacity is skipped as full (BR-04) so a suggestion is always actually takeable. Ordering
    is `(participants, start)`: fewest people already waiting first, the soonest such slot as the
    tiebreaker. Returns `[]` when nothing qualifies (AC-02.2) - a normal empty result, not an error.
    """
    del specialty  # reserved for the caller-side specialty -> owner mapping; unused here
    midnight = start_from.replace(hour=0, minute=0, second=0, microsecond=0)
    slots: list[ArrivalSlot] = []
    for owner_id in candidate_owner_ids:
        resource = repo.get(Resource, owner_id)
        if resource is None or not resource.is_available:
            continue
        for day in range(days):
            for hour in hours:
                start = midnight + timedelta(days=day, hours=hour)
                participants = _participants_at(repo, owner_id, start)
                capacity = resource.capacity_per_hour
                if capacity is not None and participants >= capacity:
                    continue  # slot is full - never suggest a time the patient cannot take
                forecast = estimate_wait(repo, owner_id, hour, llm)  # BR-03: only source of an ETA
                slots.append(
                    ArrivalSlot(
                        owner_id=owner_id,
                        start=start,
                        participants=participants,
                        eta_minutes=forecast.value,
                        eta_source=forecast.source,
                    )
                )

    slots.sort(key=lambda slot: (slot.participants, slot.start))
    return slots[:top_n]


def confirm_arrival_slot(
    repo: Repository,
    patient_id: UUID,
    specialty: str,
    owner_id: UUID,
    start: datetime,
) -> Appointment:
    """Persist the patient's accepted arrival time as a `PROPOSED` `Appointment` (logged for later).

    This is the "log into DB for later use" step: the chosen `slot_start` and `owner_id` are stored
    so the visit is on record. It is deliberately NOT a booking - `Appointment` starts `PROPOSED`;
    moving to `BOOKED` needs staff confirmation (BR-02), which is out of this pre-arrival flow.
    """
    appointment = Appointment(
        patient_id=patient_id,
        specialty=specialty,
        owner_id=owner_id,
        slot_start=start,
        status=AppointmentStatus.PROPOSED,
    )
    return repo.save(appointment)

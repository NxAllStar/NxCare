"""Grounding + persistence for the arrival-time agent (extends FR-02).

The agent that recommends *when to come* reasons over real data, not guesses: this module does the
deterministic half - it searches the DB for every reservation and buckets it against hospital
working hours - and the LLM (see `arrival_chat.py`) reasons over that retrieved summary. Keeping the
retrieval in code is the grounding contract (NFR-SEC-20, mirrors `forecast/`): the model never
invents a reservation count, it only interprets the ones we hand it.

A "reservation" is an `Appointment` with a `slot_start` (no new entity needed - see the ADR-003 data
model). `confirm_arrival_slot` logs the patient's accepted time back as a `PROPOSED` appointment;
`owner_id` is optional because a time-block arrival is not yet bound to a specific doctor (the desk
assigns one on arrival, ADR-003 call-time binding).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import UUID

from ...models import Appointment, AppointmentStatus
from ...state import Repository

# Hospital working hours [OPEN_HOUR, CLOSE_HOUR): open 06:00, last hour-block starts 19:00, closes
# 20:00 (8pm). A single config constant today; promote to an OperatingHours table only if hours ever
# vary by day/department/holiday (data-model note).
OPEN_HOUR = 6
CLOSE_HOUR = 20

# An appointment in one of these states no longer holds its slot, so it is not counted.
_INACTIVE_STATUSES = (AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW)


@dataclass(frozen=True)
class HourLoad:
    """How many reservations already fall inside one working hour (e.g. 08:00-09:00)."""

    hour: int
    reservations: int


@dataclass(frozen=True)
class DayLoad:
    """One upcoming day's reservation load across every working hour."""

    day: date
    weekday: str
    hours: tuple[HourLoad, ...]


def summarize_reservations(
    repo: Repository,
    start_from: datetime,
    days: int,
    *,
    open_hour: int = OPEN_HOUR,
    close_hour: int = CLOSE_HOUR,
) -> list[DayLoad]:
    """Search every reservation and bucket it per (day, working hour) - the agent's grounding.

    Counts each active `Appointment` whose `slot_start` falls inside the hour, hospital-wide, for
    `days` days starting from the midnight of `start_from`, across `[open_hour, close_hour)`. A
    reservation outside working hours (there should be none) is simply never bucketed. This is a
    read-only query - it invents nothing and never writes.
    """
    midnight = start_from.replace(hour=0, minute=0, second=0, microsecond=0)
    reservations = [
        appointment
        for appointment in repo.list(Appointment)
        if appointment.slot_start is not None and appointment.status not in _INACTIVE_STATUSES
    ]

    summary: list[DayLoad] = []
    for day_offset in range(days):
        day_start = midnight + timedelta(days=day_offset)
        hours: list[HourLoad] = []
        for hour in range(open_hour, close_hour):
            block_start = day_start + timedelta(hours=hour)
            block_end = block_start + timedelta(hours=1)
            count = sum(
                1 for r in reservations if block_start <= r.slot_start < block_end  # type: ignore[operator]
            )
            hours.append(HourLoad(hour=hour, reservations=count))
        summary.append(
            DayLoad(day=day_start.date(), weekday=day_start.strftime("%A"), hours=tuple(hours))
        )
    return summary


def confirm_arrival_slot(
    repo: Repository,
    patient_id: UUID,
    specialty: str,
    start: datetime,
    owner_id: UUID | None = None,
) -> Appointment:
    """Persist the patient's accepted arrival time as a `PROPOSED` `Appointment` (log for later).

    This is the "log which time" step. It is deliberately NOT a booking: `Appointment` starts
    `PROPOSED`; the move to `BOOKED` needs staff confirmation (BR-02). `owner_id` is optional - a
    time-block arrival has no assigned doctor yet; the desk binds one at arrival (ADR-003).
    """
    appointment = Appointment(
        patient_id=patient_id,
        specialty=specialty,
        owner_id=owner_id,
        slot_start=start,
        status=AppointmentStatus.PROPOSED,
    )
    return repo.save(appointment)

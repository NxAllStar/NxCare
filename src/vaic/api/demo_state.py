"""Process-wide demo state for the API (local/dev only - no real patient data, agent-guardrails.md).

Picks the Repository backend from `VAIC_STATE_BACKEND` (`memory` default, `redis` when running
under docker-compose) and seeds a couple of synthetic `Resource`s so `recommend_slots` (FR-02) has
candidates to rank. This mirrors what a dedicated seed script would do, kept minimal here since the
demo has no persistent seed step yet.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from ..models import (
    Appointment,
    AppointmentStatus,
    Department,
    Resource,
    ResourceType,
)
from ..state import InMemoryRepository, Repository
from ..state.redis_store import RedisRepository

# Fixed, synthetic demo owner ids so repeated app starts against Redis are idempotent instead of
# accumulating a new pair of Resources on every restart.
DEMO_OWNER_LIGHT = UUID("00000000-0000-0000-0000-000000000001")
DEMO_OWNER_BUSY = UUID("00000000-0000-0000-0000-000000000002")

# ---- Arrival-time-recommendation demo (extends FR-02) -------------------------------------------
# Synthetic, dev-only fixtures (AS-03, agent-guardrails.md) for the "best time to come" feature: one
# department, three interchangeable general doctors, and a spread of already-booked appointments so
# some slots are crowded and some are empty. All ids are fixed so re-seeding is idempotent.
ARRIVAL_DEPARTMENT_ID = UUID("00000000-0000-0000-0000-0000000000a0")
ARRIVAL_DOCTOR_A = UUID("00000000-0000-0000-0000-0000000000a1")
ARRIVAL_DOCTOR_B = UUID("00000000-0000-0000-0000-0000000000a2")
ARRIVAL_DOCTOR_C = UUID("00000000-0000-0000-0000-0000000000a3")
ARRIVAL_DOCTORS = (ARRIVAL_DOCTOR_A, ARRIVAL_DOCTOR_B, ARRIVAL_DOCTOR_C)

# Fixed midnight the demo grid is anchored to, so suggestions are reproducible regardless of the
# wall clock (mirrors agent.py's _BOOKING_REFERENCE_DATE). Production would anchor on "now" instead.
ARRIVAL_DEMO_ANCHOR = datetime(2026, 7, 20, 0, 0, tzinfo=UTC)
ARRIVAL_DEMO_HOURS = [8, 9, 10, 11]
ARRIVAL_DEMO_DAYS = 3
_ARRIVAL_DOCTOR_CAPACITY = 4

# (owner, day offset, hour, how many people already booked) - hand-tuned so the least-crowded-first
# ranking has something to sort. Doctor A's 9:00 today is deliberately at capacity (4) to exercise
# the "skip full slot" path; Doctor B is the light option; Doctor C is middling.
_ARRIVAL_DEMO_BOOKINGS: tuple[tuple[UUID, int, int, int], ...] = (
    (ARRIVAL_DOCTOR_A, 0, 8, 3),
    (ARRIVAL_DOCTOR_A, 0, 9, _ARRIVAL_DOCTOR_CAPACITY),
    (ARRIVAL_DOCTOR_A, 0, 10, 1),
    (ARRIVAL_DOCTOR_B, 0, 9, 1),
    (ARRIVAL_DOCTOR_C, 0, 8, 2),
    (ARRIVAL_DOCTOR_C, 0, 9, 2),
    (ARRIVAL_DOCTOR_C, 1, 8, 1),
)


def build_repository() -> Repository:
    backend = os.environ.get("VAIC_STATE_BACKEND", "memory")
    if backend == "redis":
        url = os.environ.get("VAIC_REDIS_URL", "redis://localhost:6379/0")
        return RedisRepository(url)
    return InMemoryRepository()


def seed_demo_resources(repo: Repository) -> None:
    """Idempotent: re-saving the same fixed ids just overwrites with the same values."""
    for owner_id in (DEMO_OWNER_LIGHT, DEMO_OWNER_BUSY):
        existing = repo.get(Resource, owner_id)
        if existing is not None:
            continue
        resource = Resource(
            id=owner_id,
            type=ResourceType.DOCTOR,
            department_id=owner_id,  # synthetic, demo-only - no real department mapping yet
            is_available=True,
            capacity_per_hour=6,
        )
        repo.save(resource)


def seed_arrival_demo(repo: Repository) -> None:
    """Seed the department, doctors, and pre-booked appointments for the arrival-time feature.

    Idempotent on the fixed ids: the department and doctors are keyed by constant ids, so re-running
    overwrites in place. The appointments use random ids (there is no natural fixed id for them), so
    they are seeded only once - guarded on the department already existing - to avoid piling up new
    bookings on every app restart when running against Redis.
    """
    already_seeded = repo.get(Department, ARRIVAL_DEPARTMENT_ID) is not None

    repo.save(
        Department(
            id=ARRIVAL_DEPARTMENT_ID,
            code="DepA",
            display_label="General Medicine",
        )
    )
    for doctor_id in ARRIVAL_DOCTORS:
        repo.save(
            Resource(
                id=doctor_id,
                type=ResourceType.DOCTOR,
                department_id=ARRIVAL_DEPARTMENT_ID,
                is_available=True,
                capacity_per_hour=_ARRIVAL_DOCTOR_CAPACITY,
            )
        )

    if already_seeded:
        return  # appointments already placed on a previous start - do not double-book
    for owner_id, day, hour, count in _ARRIVAL_DEMO_BOOKINGS:
        start = ARRIVAL_DEMO_ANCHOR + timedelta(days=day, hours=hour)
        for _ in range(count):
            repo.save(
                Appointment(
                    patient_id=uuid4(),
                    specialty="NOI_TONG_QUAT",
                    owner_id=owner_id,
                    slot_start=start,
                    status=AppointmentStatus.PROPOSED,
                )
            )

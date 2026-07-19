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

from ..agents.intake.arrival import CLOSE_HOUR, OPEN_HOUR
from ..agents.intake.patient_status import issue_consult_ticket
from ..models import (
    Appointment,
    AppointmentStatus,
    Department,
    PriorityLevel,
    QueueSubjectType,
    QueueTicket,
    Resource,
    ResourceType,
    ServiceType,
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

# Orderable services a doctor can put on a diagnosis at consult time (FR-03). Fixed ids so a demo
# client / the console can reference them directly. Synthetic reference data (dev-only).
ARRIVAL_SERVICE_TYPES: tuple[tuple[UUID, str, str, int], ...] = (
    # (id, code, display_label, default_duration_min)
    (UUID("00000000-0000-0000-0000-0000000000b1"), "BLOOD_TEST", "Blood Test", 15),
    (UUID("00000000-0000-0000-0000-0000000000b2"), "XRAY", "X-Ray", 20),
    (UUID("00000000-0000-0000-0000-0000000000b3"), "ULTRASOUND", "Ultrasound", 30),
    (UUID("00000000-0000-0000-0000-0000000000b4"), "ECG", "Electrocardiogram", 10),
)

# Fixed midnight the demo grid is anchored to, so suggestions are reproducible regardless of the
# wall clock (mirrors agent.py's _BOOKING_REFERENCE_DATE). Production would anchor on "now" instead.
ARRIVAL_DEMO_ANCHOR = datetime(2026, 7, 20, 0, 0, tzinfo=UTC)
ARRIVAL_DEMO_DAYS = 3

# Hospital-wide reservation load per working hour on day 0: a realistic distribution the arrival
# agent reasons over - busy mid-morning (9:00) and mid-afternoon (15:00), quiet early morning,
# lunch, and late evening. Day 1 is roughly half as busy; day 2 is empty (so the agent can also
# suggest a wide-open later day). Hours span the working window [06:00, 20:00).
_DAY0_HOUR_LOAD: dict[int, int] = {
    6: 0, 7: 1, 8: 4, 9: 6, 10: 5, 11: 3, 12: 1,
    13: 2, 14: 5, 15: 6, 16: 4, 17: 2, 18: 1, 19: 0,
}


def _reservation_load(day_offset: int, hour: int) -> int:
    """How many reservations to seed at (day, hour): full on day 0, half on day 1, none after."""
    base = _DAY0_HOUR_LOAD.get(hour, 0)
    if day_offset == 0:
        return base
    if day_offset == 1:
        return base // 2
    return 0


# ---- Consult-queue demo (extends /queue and /status) ---------------------------------------------
# A handful of synthetic patients already waiting for a general checkup, so /queue and /status show
# realistic non-zero numbers without confirming several appointments by hand first. Issued relative
# to wall-clock "now" (not ARRIVAL_DEMO_ANCHOR) since ticket_seq/ETA are a live-queue concept, not
# the crowding-forecast grid.
_CONSULT_QUEUE_SEED: tuple[tuple[PriorityLevel, int], ...] = (
    # (priority band, minutes ago issued) - spread out so ticket_seq/issued_at order is visible.
    (PriorityLevel.ROUTINE, 45),
    (PriorityLevel.ROUTINE, 30),
    (PriorityLevel.URGENT, 20),  # jumps ahead of the earlier ROUTINE tickets (ADR-003 ordering)
    (PriorityLevel.ROUTINE, 10),
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
                capacity_per_hour=6,
            )
        )

    if already_seeded:
        return  # reservations already placed on a previous start - do not double-book
    # Spread reservations across the working-hours window per the load pattern, round-robining the
    # owner across the three doctors so the data looks realistic (counting is hospital-wide anyway).
    seq = 0
    for day in range(ARRIVAL_DEMO_DAYS):
        for hour in range(OPEN_HOUR, CLOSE_HOUR):
            start = ARRIVAL_DEMO_ANCHOR + timedelta(days=day, hours=hour)
            for _ in range(_reservation_load(day, hour)):
                repo.save(
                    Appointment(
                        patient_id=uuid4(),
                        specialty="NOI_TONG_QUAT",
                        owner_id=ARRIVAL_DOCTORS[seq % len(ARRIVAL_DOCTORS)],
                        slot_start=start,
                        status=AppointmentStatus.PROPOSED,
                    )
                )
                seq += 1


def seed_consult_queue_demo(repo: Repository) -> None:
    """Seed a few already-waiting consult tickets (dev-only) for the general-checkup queue.

    Guarded on any consult ticket already existing for the demo department - seeded once, not
    piled onto again on every app restart against Redis. Requires `seed_arrival_demo` to have run
    first (the department it attaches tickets to).
    """
    already_seeded = bool(
        repo.list(
            QueueTicket, department_id=ARRIVAL_DEPARTMENT_ID, subject_type=QueueSubjectType.CONSULT
        )
    )
    if already_seeded:
        return

    department = repo.get(Department, ARRIVAL_DEPARTMENT_ID)
    if department is None:
        return  # seed_arrival_demo has not run yet - nothing to attach tickets to

    now = datetime.now(UTC)
    for priority, minutes_ago in _CONSULT_QUEUE_SEED:
        patient_id = uuid4()
        appointment = repo.save(
            Appointment(
                patient_id=patient_id,
                specialty="NOI_TONG_QUAT",
                status=AppointmentStatus.PROPOSED,
            )
        )
        issue_consult_ticket(
            repo,
            department,
            appointment.id,  # a real Appointment - call_next_patient dereferences this
            patient_id,
            priority,
            issued_at=now - timedelta(minutes=minutes_ago),
        )


def seed_service_types_demo(repo: Repository) -> None:
    """Seed the orderable `ServiceType`s a doctor can put on a diagnosis (idempotent, fixed ids)."""
    for type_id, code, label, duration in ARRIVAL_SERVICE_TYPES:
        repo.save(
            ServiceType(
                id=type_id,
                code=code,
                display_label=label,
                default_duration_min=duration,
            )
        )

"""Process-wide demo state for the API (local/dev only - no real patient data, agent-guardrails.md).

Picks the Repository backend from `VAIC_STATE_BACKEND` (`memory` default, `redis` when running
under docker-compose) and seeds a couple of synthetic `Resource`s so `recommend_slots` (FR-02) has
candidates to rank. This mirrors what a dedicated seed script would do, kept minimal here since the
demo has no persistent seed step yet.

`sync_service_types_from_postgres` additionally pulls `ServiceType` config rows from the durable
Postgres store (OI-15, already seeded there by db-seeder - `service_types` is config-managed, not
demo-only) into whichever runtime `Repository` the app is using. Postgres is the source of truth for
this config table; Redis/in-memory is the operational store the rest of the app reads from, so the
care-plan pipeline (`agents/careplan/routing.py`) can find `ServiceType`s via the same `Repository`
interface it already uses, without an async dependency leaking into synchronous domain code.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from ..agents.intake.arrival import CLOSE_HOUR, OPEN_HOUR
from ..agents.intake.patient_status import issue_consult_ticket
from ..config import get_settings
from ..models import (
    Appointment,
    AppointmentStatus,
    Department,
    Patient,
    PriorityLevel,
    QueueSubjectType,
    QueueTicket,
    Resource,
    ResourceType,
    ServiceType,
)
from ..state import InMemoryRepository, Repository
from ..state.redis_store import RedisRepository

logger = logging.getLogger(__name__)

# Fixed, synthetic demo owner ids so repeated app starts against Redis are idempotent instead of
# accumulating a new pair of Resources on every restart.
DEMO_OWNER_LIGHT = UUID("00000000-0000-0000-0000-000000000001")
DEMO_OWNER_BUSY = UUID("00000000-0000-0000-0000-000000000002")

# Distinct fixed ids for the care-plan test-execution stations (technicians/rooms) FR-04/FR-23
# route doctor-ordered tests through - kept separate from DEMO_OWNER_LIGHT/BUSY above, which are
# consult doctors for intake booking (FR-02), a different clinical role.
DEMO_CAREPLAN_STATIONS = (
    UUID("00000000-0000-0000-0000-000000000011"),
    UUID("00000000-0000-0000-0000-000000000012"),
    UUID("00000000-0000-0000-0000-000000000013"),
)

# Fixed demo patients keyed by the scannable `patient_code` that BOTH the staff console and the
# patient app address a person by (TASK-038). Stable Patient/Appointment UUIDs keep the seed
# idempotent across restarts (Redis) and let the two surfaces resolve to the SAME id, which is the
# whole point: a doctor's order on the console and the patient's own screen must be one patient.
# Synthetic personas only - no real patient data (agent-guardrails.md). These mirror the console's
# seed (`frontend/src/console/dashboard/clinicalStore.ts`).
# (patient_code, full_name, patient_id, appointment_id)
DEMO_PATIENTS = (
    ("BN-941207", "Nguyen Thi Lan", UUID("00000000-0000-0000-0000-0000000000a1"),
     UUID("00000000-0000-0000-0000-0000000000b1")),
    ("BN-880214", "Le Hoang Nam", UUID("00000000-0000-0000-0000-0000000000a2"),
     UUID("00000000-0000-0000-0000-0000000000b2")),
    ("BN-921105", "Tran Minh Quan", UUID("00000000-0000-0000-0000-0000000000a3"),
     UUID("00000000-0000-0000-0000-0000000000b3")),
)

# Fallback ServiceType catalog for a self-contained run with NO Postgres attached, so
# `/api/careplan/generate` can resolve the console's test names (`resolve_service_types` matches on
# code or display_label). Postgres stays the source of truth when configured
# (`sync_service_types_from_postgres`); this only fills codes Postgres did not already provide.
# Labels match the console's SERVICE_CATALOG (`ConsultOrdersScreen.tsx`) exactly, with diacritics.
# (code, display_label, requires_fasting, turnaround_minutes, default_duration_min)
DEMO_SERVICE_CATALOG = (
    ("BLOOD_TEST", "Xét nghiệm máu", True, 45, 10),
    ("XRAY_CHEST", "X-quang ngực", False, 15, 15),
    ("CT_CHEST", "CT ngực", False, 30, 20),
    ("ULTRASOUND_ABDOMEN", "Siêu âm bụng", True, 0, 20),
    ("XRAY_ABDOMEN", "Chụp X-quang bụng", False, 15, 15),
    ("ENDOSCOPY_GASTRIC", "Nội soi dạ dày", True, 60, 30),
)

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
        # VAIC_REDIS_URL takes precedence; REDIS_URL is the name .env.example documents for the
        # hosted Redis/Valkey instance - accept either so a real deployment's .env is not silently
        # ignored in favor of the localhost default.
        url = os.environ.get("VAIC_REDIS_URL") or os.environ.get(
            "REDIS_URL", "redis://localhost:6379/0"
        )
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


def seed_demo_careplan_stations(repo: Repository) -> None:
    """Idempotent, same pattern as `seed_demo_resources`: fixed ids never duplicate on restart."""
    for owner_id in DEMO_CAREPLAN_STATIONS:
        existing = repo.get(Resource, owner_id)
        if existing is not None:
            continue
        resource = Resource(
            id=owner_id,
            type=ResourceType.TECHNICIAN,
            department_id=owner_id,  # synthetic, demo-only - no real department mapping yet
            is_available=True,
            capacity_per_hour=4,
        )
        repo.save(resource)


def seed_demo_patients(repo: Repository) -> None:
    """Idempotent, same pattern as `seed_demo_resources`: fixed ids never duplicate on restart.

    Each patient gets one demo `Appointment`, since `/api/careplan/generate` requires an
    `appointment_id` before it will accept a doctor's orders. `/api/patients/resolve` mints these
    on demand too, for any patient_code not seeded here; seeding the known personas just keeps their
    ids stable across restarts so the console and the patient app agree without a first round-trip.
    """
    for code, full_name, patient_id, appointment_id in DEMO_PATIENTS:
        if repo.get(Patient, patient_id) is None:
            repo.save(Patient(id=patient_id, full_name=full_name, patient_code=code))
        if repo.get(Appointment, appointment_id) is None:
            repo.save(Appointment(id=appointment_id, patient_id=patient_id, specialty="general"))


def seed_demo_service_catalog(repo: Repository) -> None:
    """Fill any ServiceType `code` Postgres did not already supply (idempotent by code).

    Skips a code that already resolves - so when `sync_service_types_from_postgres` ran first and
    provided the real config rows, this adds nothing and Postgres stays the source of truth. On a
    plain local run with no database, this is the only catalog, and it is what lets a doctor's test
    list resolve at all.
    """
    for code, display_label, requires_fasting, turnaround, duration in DEMO_SERVICE_CATALOG:
        if repo.list(ServiceType, code=code):
            continue
        repo.save(
            ServiceType(
                code=code,
                display_label=display_label,
                requires_fasting=requires_fasting,
                turnaround_minutes=turnaround,
                default_duration_min=duration,
            )
        )


def sync_service_types_from_postgres(repo: Repository) -> int:
    """Copy `ServiceType` config rows from Postgres into `repo` (Redis or in-memory) once at
    startup, so `resolve_service_types` (routing.py) can look them up through the same synchronous
    `Repository` the rest of the care-plan pipeline already uses.

    Deliberately bypasses `AsyncPostgresRepository`/`vaic.state.postgres`'s pooled, process-wide
    engine and talks to `asyncpg` directly with one short-lived connection: that shared engine is
    tuned for a long-running async app (connection pooling, `pool_pre_ping`) and, on Windows,
    asyncpg's pooled ping does not survive being driven from a one-off `asyncio.run()` inside an
    otherwise synchronous process (event-loop-affinity errors). A single direct connect/fetch/close
    has none of that state to get wedged, and this function runs exactly once at process startup.

    Never raises: an unreachable Postgres or the `sql` extra not being installed both degrade to
    "0 rows synced" with a logged warning, same posture as the forecast/triage fallbacks elsewhere
    in this API layer - a missing config sync is a handled outcome, not a startup crash. Skipped
    entirely when `postgres_password` is unset (no Postgres configured for this run, e.g. plain
    local/test runs), mirroring `Settings.chat_configured`'s gating pattern.
    """
    settings = get_settings()
    if not settings.postgres_password:
        return 0

    try:
        import asyncio

        import asyncpg

        async def _fetch() -> list[ServiceType]:
            conn = await asyncpg.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_name,
                user=settings.postgres_user,
                password=settings.postgres_password,
            )
            try:
                rows = await conn.fetch(
                    "SELECT id, code, display_label, requires_fasting, turnaround_minutes, "
                    "default_duration_min FROM service_types"
                )
            finally:
                await conn.close()
            return [ServiceType(**dict(row)) for row in rows]

        service_types = asyncio.run(_fetch())
    except Exception:
        logger.warning(
            "service_type sync from Postgres failed - continuing without it", exc_info=True
        )
        return 0

    for service_type in service_types:
        repo.save(service_type)
    return len(service_types)


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

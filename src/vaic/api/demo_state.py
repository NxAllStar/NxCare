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
from uuid import UUID

from ..config import get_settings
from ..models import Appointment, Patient, Resource, ResourceType, ServiceType
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

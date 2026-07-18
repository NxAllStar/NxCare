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
from ..models import Resource, ResourceType, ServiceType
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

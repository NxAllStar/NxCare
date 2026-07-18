"""Process-wide demo state for the API (local/dev only - no real patient data, agent-guardrails.md).

Picks the Repository backend from `VAIC_STATE_BACKEND` (`memory` default, `redis` when running
under docker-compose) and seeds a couple of synthetic `Resource`s so `recommend_slots` (FR-02) has
candidates to rank. This mirrors what a dedicated seed script would do, kept minimal here since the
demo has no persistent seed step yet.
"""

from __future__ import annotations

import os
from uuid import UUID

from ..models import Resource, ResourceType
from ..state import InMemoryRepository, Repository
from ..state.redis_store import RedisRepository

# Fixed, synthetic demo owner ids so repeated app starts against Redis are idempotent instead of
# accumulating a new pair of Resources on every restart.
DEMO_OWNER_LIGHT = UUID("00000000-0000-0000-0000-000000000001")
DEMO_OWNER_BUSY = UUID("00000000-0000-0000-0000-000000000002")


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

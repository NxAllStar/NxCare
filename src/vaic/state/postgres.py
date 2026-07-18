"""Process-wide async PostgreSQL engine/session singleton (OI-15 durable store).

Mirrors the `get_settings()` pattern in `config.py`: built once per process via `lru_cache`, never
constructed ad hoc by a caller. `sqlalchemy` is imported lazily so the in-memory/Redis paths never
require the optional `sql` extra (`uv sync --extra sql`).
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import TYPE_CHECKING

from ..config import get_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


def _json_serializer(value: object) -> str:
    """`default=str` covers the UUID/datetime/Decimal values nested inside JSONB list/dict fields
    (`Task.depends_on`, `CarePlan.assigned_staff`, ...) - the typed columns (UUID, TIMESTAMP,
    NUMERIC) never go through this path, only JSON/JSONB ones do."""
    return json.dumps(value, default=str)


@lru_cache
def get_engine() -> AsyncEngine:
    """Return the process-wide async engine, built once from `Settings.postgres_url`."""
    from sqlalchemy.ext.asyncio import create_async_engine

    return create_async_engine(
        get_settings().postgres_url, pool_pre_ping=True, json_serializer=_json_serializer
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the process-wide session factory, bound to `get_engine()`."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    return async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)


async def dispose_engine() -> None:
    """Close the pooled connections and drop the cached singletons (tests, graceful shutdown)."""
    if get_engine.cache_info().currsize:
        await get_engine().dispose()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()

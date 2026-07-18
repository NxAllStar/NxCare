"""Optional SQLAlchemy/PostgreSQL durable-store schema (TASK-032, resolves OI-15).

Not imported by `vaic.state`'s default `__init__` - `sqlalchemy`/`pg8000` are an optional `sql`
extra, and the app's default store is still Redis (`vaic.state.redis_store`). Import from here
explicitly: `from vaic.state.sql import get_engine, create_schema`.
"""

from __future__ import annotations

from .engine import build_url, create_schema, get_engine

__all__ = ["build_url", "create_schema", "get_engine"]

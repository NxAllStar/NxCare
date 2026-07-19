"""The PostgreSQL durable-store option (OI-15): ORM models plus an async CRUD repository.

Optional - requires `uv sync --extra sql`. Never imported by the default (Redis/in-memory) path in
`api/demo_state.py`.
"""

from __future__ import annotations

from .models import Base
from .repository import AsyncPostgresRepository
from .sync_adapter import PostgresRepositorySyncAdapter

__all__ = ["AsyncPostgresRepository", "Base", "PostgresRepositorySyncAdapter"]

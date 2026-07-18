"""Sync `Repository` bridge over `AsyncPostgresRepository`, for the tested `agents/*` code.

`agents/{intake,careplan,journey}/*` call `repo.save/get/list/delete` synchronously inside
already-tested business logic (sequencing, slot allocation, resequencing, notifications). Rather
than rewrite that logic to await an async repo, `PostgresRepositorySyncAdapter` implements the sync
`Repository` ABC by dispatching each call onto one persistent background event loop and blocking
the calling thread for the result.

Two things make this safe rather than a silent corruption risk:

1. The persistent loop: `asyncpg`'s connection pool is bound to the event loop it was created on,
   so calling `asyncio.run(...)` per method (a fresh loop every time) would make every pooled
   connection unusable after its first loop closes. One long-lived loop, started once and reused
   for every adapter call across the process, keeps the pool valid.
2. A DEDICATED engine, never `state/postgres.py`'s `get_engine()`/`get_sessionmaker()`: those are
   singletons that bind to whichever loop happens to call them first, which is fine for native
   `async def` FastAPI routes (uvicorn runs them all on one loop) but breaks the moment this
   module's separate background loop also touches that same engine - asyncpg then raises
   `RuntimeError: ... attached to a different loop` the first time the two loops' requests
   interleave. `build_engine()`/`build_sessionmaker()` (uncached factories in `postgres.py`) give
   this module its own engine, isolated to its own loop, at the cost of a second connection pool.

API routes construct this adapter per request and call it (and the agent functions that take it)
via `starlette.concurrency.run_in_threadpool`, so the FastAPI handler itself stays `async def` while
this is the one deliberate sync bridge in the design (see the API design plan).
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from ...models.entities import _Base
from ..postgres import build_engine, build_sessionmaker
from ..repository import Repository
from .repository import AsyncPostgresRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

T = TypeVar("T", bound=_Base)
R = TypeVar("R")

_loop: asyncio.AbstractEventLoop | None = None
_loop_lock = threading.Lock()
_bridge_engine: AsyncEngine | None = None
_bridge_engine_lock = threading.Lock()
_bridge_repo: AsyncPostgresRepository | None = None
_bridge_repo_lock = threading.Lock()


def _get_loop() -> asyncio.AbstractEventLoop:
    """The process-wide background loop, started once on a dedicated daemon thread."""
    global _loop
    with _loop_lock:
        if _loop is None:
            loop = asyncio.new_event_loop()
            threading.Thread(target=loop.run_forever, daemon=True, name="pg-sync-bridge").start()
            _loop = loop
        return _loop


def get_bridge_engine() -> AsyncEngine:
    """The process-wide engine isolated to the bridge loop (see module docstring point 2) - for
    any OTHER Postgres access (e.g. `auth/credential_store.py`'s seeding) that must run from a
    sync context alongside `PostgresRepositorySyncAdapter`, so it shares one loop/pool instead of
    creating yet another separate engine."""
    global _bridge_engine
    with _bridge_engine_lock:
        if _bridge_engine is None:
            _bridge_engine = build_engine()
        return _bridge_engine


def _get_bridge_repo() -> AsyncPostgresRepository:
    """The process-wide bridge repository, backed by `get_bridge_engine()` - never
    `state/postgres.py`'s singleton, which belongs to the native-async request path."""
    global _bridge_repo
    with _bridge_repo_lock:
        if _bridge_repo is None:
            _bridge_repo = AsyncPostgresRepository(build_sessionmaker(get_bridge_engine()))
        return _bridge_repo


def run_coro(coro: Coroutine[Any, Any, R]) -> R:
    """Run `coro` on the bridge loop and block the calling thread for the result - the same
    dispatch `PostgresRepositorySyncAdapter` uses internally, exposed for other sync-context
    callers that need the bridge loop (e.g. one-time credential-table seeding at startup)."""
    return asyncio.run_coroutine_threadsafe(coro, _get_loop()).result()


_run = run_coro  # internal alias, kept so the methods below read as "this class's own helper"


class PostgresRepositorySyncAdapter(Repository):
    """Sync `Repository` facade over the process-wide bridge `AsyncPostgresRepository` - see
    module docstring. The constructor's `async_repo` parameter exists for tests that want to
    inject a fake; every real caller uses the parameterless form and gets the shared bridge repo."""

    def __init__(self, async_repo: AsyncPostgresRepository | None = None) -> None:
        self._async_repo = async_repo or _get_bridge_repo()

    def save(self, entity: T) -> T:
        return _run(self._async_repo.save(entity))

    def get(self, model_cls: type[T], entity_id: UUID) -> T | None:
        return _run(self._async_repo.get(model_cls, entity_id))

    def list(self, model_cls: type[T], **filters: Any) -> list[T]:
        return _run(self._async_repo.list(model_cls, **filters))

    def delete(self, model_cls: type[T], entity_id: UUID) -> bool:
        return _run(self._async_repo.delete(model_cls, entity_id))

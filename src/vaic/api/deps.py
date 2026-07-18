"""Shared FastAPI dependencies for the new routers: store access, pagination, and auth.

Auth is JWT-based (FR-18): `POST /auth/login` verifies a username/password against the real
`account_credentials` table (`auth/credential_store.py`, bcrypt-hashed) and issues a short-lived
signed token (`auth/jwt_tokens.py`); `get_current_account` decodes it and re-reads the account by
id, natively async - no server-side session record, no sync bridge needed for auth at all.

Domain data goes through the new `AsyncPostgresRepository` (native `await`, no bridge) for
direct-CRUD routes, or through `PostgresRepositorySyncAdapter` (see `state/sql/sync_adapter.py`)
for routes that call into the existing sync `agents/*` business logic.

The bearer token is read via `fastapi.security.HTTPBearer` - the standard FastAPI security scheme
class - rather than a bare `Header(default=None)` param. This form registers as an OpenAPI
`securitySchemes` entry, which is what turns on the padlock icons and the "Authorize" button in
`/docs` (a plain `Header` param never does, regardless of what the handler does with it).
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.concurrency import run_in_threadpool

from ..auth import Account, Unauthorized
from ..auth.credential_store import get_account_by_id
from ..auth.jwt_tokens import decode_access_token
from ..state.sql.repository import AsyncPostgresRepository
from ..state.sql.sync_adapter import PostgresRepositorySyncAdapter
from .demo_seed import ensure_demo_seed

bearer_scheme = HTTPBearer(auto_error=False, description="Token from POST /auth/login")

DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 100


class PageParams:
    """Shared pagination for every list endpoint - never an unbounded `repo.list(...)`."""

    def __init__(
        self,
        limit: int = Query(default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT),
        offset: int = Query(default=0, ge=0),
    ) -> None:
        self.limit = limit
        self.offset = offset

    def slice(self, records: list) -> list:
        return records[self.offset : self.offset + self.limit]


def get_async_repo() -> AsyncPostgresRepository:
    """One `AsyncPostgresRepository` per request; the underlying engine/sessionmaker is the
    process-wide singleton in `state/postgres.py`."""
    return AsyncPostgresRepository()


def get_sync_adapter() -> PostgresRepositorySyncAdapter:
    """The bridge for routes that must call existing sync `agents/*` code (see module docstring).
    Takes no dependency on `get_async_repo()` - the adapter deliberately uses its OWN,
    loop-isolated engine (see `sync_adapter.py`'s docstring), never the native-async singleton."""
    return PostgresRepositorySyncAdapter()


def bearer_token(creds: HTTPAuthorizationCredentials | None) -> str:
    if creds is None:
        raise HTTPException(status_code=401, detail="missing or malformed Authorization header")
    return creds.credentials


async def get_current_account(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Account:
    """AC-18.1: decode the JWT, then re-read the account by id - or 401.

    `ensure_demo_seed()` runs the (idempotent, first-call-only) credential-table seed via the sync
    bridge, so a fresh process serves the very first login without a separate provisioning step.
    """
    token = bearer_token(creds)
    try:
        account_id = decode_access_token(token)
        await run_in_threadpool(ensure_demo_seed)
        account = await get_account_by_id(account_id)
    except Unauthorized as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if account is None:
        raise HTTPException(status_code=401, detail="account no longer exists")
    return account

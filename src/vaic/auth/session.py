"""Session service: create/validate/revoke a session (token -> Account) (FR-18).

Backed by `vaic.state.Repository` so the store is swappable (in-memory in tests and dev, Redis for
the running demo - `RedisRepository` already implements the same interface) without touching this
class. Session lifetime in the demo ends with the run (docs/specs/06 "Authentication"); this module
deliberately does not add a TTL policy on top of that.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from ..state import Repository
from .accounts import Account
from .exceptions import Unauthorized


def _default_clock() -> datetime:
    return datetime.now(UTC)


class Session(BaseModel):
    """An issued session. `id` doubles as the opaque bearer token handed back to the caller."""

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    account_id: UUID
    created_at: datetime
    revoked: bool = False


class SessionService:
    """Create, validate, and revoke sessions.

    `clock` is injected (defaulting to the real clock) so tests never depend on wall-clock time -
    pass a fixed callable to get deterministic `created_at` values.
    """

    def __init__(self, repo: Repository, clock: Callable[[], datetime] = _default_clock) -> None:
        self._repo = repo
        self._clock = clock

    def create(self, account: Account) -> Session:
        session = Session(account_id=account.id, created_at=self._clock())
        return self._repo.save(session)

    def validate(self, token: str) -> Session:
        """Return the live Session for `token`, or raise Unauthorized (AC-18.1: 401)."""
        session = self._get(token)
        if session is None or session.revoked:
            raise Unauthorized("no valid session")
        return session

    def revoke(self, token: str) -> None:
        """Revoke a session. Unknown token -> Unauthorized; revoking twice is idempotent."""
        session = self._get(token)
        if session is None:
            raise Unauthorized("no valid session")
        if session.revoked:
            return
        self._repo.save(session.model_copy(update={"revoked": True}))

    def _get(self, token: str) -> Session | None:
        try:
            token_id = UUID(token)
        except (ValueError, AttributeError, TypeError):
            return None
        return self._repo.get(Session, token_id)

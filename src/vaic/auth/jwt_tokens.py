"""FR-18 access tokens: standard JWT (HS256), short-lived, stateless.

`sub` carries the `Account.id` directly - there is no server-side session record to look up or
revoke (a deliberate choice: logout only discards the token client-side; a short `exp`, not a
revocation list, is what actually bounds a leaked token's lifetime). `decode_access_token` raises
`Unauthorized` for anything wrong with the token - expired, bad signature, malformed - so the
caller (`api/deps.py::get_current_account`) has one failure path to handle, matching AC-18.1.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from ..config import Settings, get_settings
from .exceptions import Unauthorized

ALGORITHM = "HS256"


def create_access_token(account_id: UUID, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(account_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str, settings: Settings | None = None) -> UUID:
    settings = settings or get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise Unauthorized("invalid or expired token") from exc

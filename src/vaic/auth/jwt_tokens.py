"""FR-18 access tokens: standard JWT (HS256), short-lived, stateless.

The token carries the resolved `Account` directly as signed claims (`sub`, `username`, `role`,
`patientId`, `resourceId`) - there is no server-side session record and no per-request Postgres
lookup: the signature is what makes trusting these claims safe, exactly like any other JWT-based
auth. This is a deliberate choice: logout only discards the token client-side, and a short `exp`
(not a revocation list) is what actually bounds a leaked token's lifetime - see `config.py`'s
`jwt_expire_minutes`. `decode_access_token` raises `Unauthorized` for anything wrong with the
token - expired, bad signature, malformed - so the caller (`api/deps.py::get_current_account`) has
one failure path to handle, matching AC-18.1.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from ..config import Settings, get_settings
from .accounts import Account
from .exceptions import Unauthorized
from .roles import Role

ALGORITHM = "HS256"


def create_access_token(account: Account, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(account.id),
        "username": account.username,
        "role": account.role.value,
        "patientId": str(account.patient_id) if account.patient_id else None,
        "resourceId": str(account.resource_id) if account.resource_id else None,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str, settings: Settings | None = None) -> Account:
    settings = settings or get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return Account(
            id=payload["sub"],
            username=payload["username"],
            role=Role(payload["role"]),
            patient_id=payload.get("patientId") or None,
            resource_id=payload.get("resourceId") or None,
        )
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise Unauthorized("invalid or expired token") from exc

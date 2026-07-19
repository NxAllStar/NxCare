"""FR-18 password login: verifies a username/password directly against `Patient.password_hash`
or `Resource.password_hash` (bcrypt) - no separate accounts/credentials table.

Patient accounts use `patient_code` as `username` (a patient logs in with the same code shown
throughout the app). Doctor accounts use `Resource.username` (only `ResourceType.DOCTOR` rows are
login-capable, for now - technician/coordinator/admin still use the client-only demo role
selector, `console/auth/StaffAuthContext.tsx`, until a real credential exists for them too).

Both `password_hash` columns are excluded from every API response (`api/schemas.py::camel_schema`'s
`exclude` at each call site) - nothing outside this module ever reads or returns them. Only this
function runs at login time; `api/deps.py::get_current_account` never re-queries Postgres per
request - the signed JWT itself carries the resolved identity (see `jwt_tokens.py`).
"""

from __future__ import annotations

import bcrypt

from ..models import Patient, Resource, ResourceType
from ..state.sql.repository import AsyncPostgresRepository
from .accounts import Account
from .roles import Role

# `bcrypt` directly, not passlib's CryptContext: passlib 1.7.4 (last release, unmaintained) has a
# hardcoded internal self-test that crashes against bcrypt>=4.1 (`ValueError: password cannot be
# longer than 72 bytes`, raised from passlib's OWN bug-detection probe, not from real input) -
# https://github.com/pyca/bcrypt/issues/684. The `bcrypt` package's own `hashpw`/`checkpw` need no
# such shim and have no known incompatibility with the version pinned in pyproject.toml.
_BCRYPT_MAX_BYTES = 72  # bcrypt silently ignores input past this - reject longer up front instead


def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > _BCRYPT_MAX_BYTES:
        raise ValueError(f"password must be at most {_BCRYPT_MAX_BYTES} bytes")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def _verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        return False  # malformed stored hash - fail closed, never raise past a login attempt


async def verify_credentials(
    username: str, password: str, repo: AsyncPostgresRepository | None = None
) -> Account | None:
    """Return the resolved `Account` if `username`/`password` match a real, hashed credential -
    tries `Patient.patient_code` first, then `Resource.username` - or `None`. Never distinguishes
    "unknown username" from "wrong password" to the caller (no account enumeration)."""
    repo = repo or AsyncPostgresRepository()

    patients = await repo.list(Patient, patient_code=username)
    if patients and _verify_password(password, patients[0].password_hash):
        patient = patients[0]
        return Account(
            id=patient.id, username=patient.patient_code, role=Role.PATIENT, patient_id=patient.id
        )

    resources = await repo.list(Resource, username=username)
    if (
        resources
        and resources[0].type is ResourceType.DOCTOR
        and _verify_password(password, resources[0].password_hash)
    ):
        resource = resources[0]
        return Account(
            id=resource.id,
            username=resource.username or username,
            role=Role.DOCTOR,
            resource_id=resource.id,
        )

    return None

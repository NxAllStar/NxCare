"""HTTP surface for FR-18 authentication: JWT-based, backed by real password columns.

`POST /login` takes `{patientCode, password}` and verifies it directly against
`Patient.password_hash` (patient accounts - `patientCode` is literally `Patient.patient_code`) or
`Resource.password_hash` (doctor accounts - the same field carries `Resource.username` instead) -
bcrypt hash comparison, `auth/password_login.py`, against whatever is actually in the database.
There is no synthetic account auto-seeded here: a `Patient`/`Resource` row only becomes a working
login once something sets its `password_hash` (see `auth/password_login.py::hash_password`) -
this router never invents or overwrites one on the caller's behalf. On success it issues a
short-lived signed access token (`auth/jwt_tokens.py`, `jwt_expire_minutes` in `.env.example`);
there is no server-side session record, so `POST /logout` only needs the client to discard the
token - it does not (and structurally cannot) revoke it early. This is stateless by design, not
an oversight (see `jwt_tokens.py`'s docstring).

`GET /demo-accounts` backs the login screen's quick-select buttons: it lists every real `Patient`
row that already has a `password_hash` set, so the button list always matches whatever accounts
can actually log in - never a hardcoded, separately-maintained pair of names.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth import Account
from ..auth.jwt_tokens import create_access_token
from ..auth.password_login import verify_credentials
from ..models import Patient
from ..state.sql.repository import AsyncPostgresRepository
from .deps import get_async_repo, get_current_account
from .schemas import CamelModel

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(CamelModel):
    patient_code: str  # a patient's patient_code, or a doctor's Resource.username
    password: str


class LoginOut(CamelModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    patient_id: str | None = None
    resource_id: str | None = None


class AccountOut(CamelModel):
    id: str
    username: str
    role: str
    patient_id: str | None = None
    resource_id: str | None = None


class DemoAccountOut(CamelModel):
    patient_code: str
    display_name: str


@router.post("/login", response_model=LoginOut)
async def login(body: LoginRequest) -> LoginOut:
    account = await verify_credentials(body.patient_code, body.password)
    if account is None:
        # Same generic failure regardless of cause - unknown username or wrong password are
        # indistinguishable to the caller (no account enumeration).
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = create_access_token(account)
    return LoginOut(
        access_token=token,
        role=account.role.value,
        patient_id=str(account.patient_id) if account.patient_id else None,
        resource_id=str(account.resource_id) if account.resource_id else None,
    )


@router.get("/demo-accounts", response_model=list[DemoAccountOut])
async def demo_accounts(
    repo: AsyncPostgresRepository = Depends(get_async_repo),
) -> list[DemoAccountOut]:
    patients = await repo.list(Patient)
    return [
        DemoAccountOut(patient_code=p.patient_code, display_name=p.full_name)
        for p in patients
        if p.password_hash
    ]


@router.post("/logout", status_code=204)
async def logout() -> None:
    """No-op: the access token is stateless and short-lived (see module docstring) - the client
    discarding it is the whole of "logout" here."""
    return None


@router.get("/me", response_model=AccountOut)
async def me(account: Account = Depends(get_current_account)) -> AccountOut:
    return AccountOut(
        id=str(account.id),
        username=account.username,
        role=account.role.value,
        patient_id=str(account.patient_id) if account.patient_id else None,
        resource_id=str(account.resource_id) if account.resource_id else None,
    )

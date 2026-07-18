"""HTTP surface for FR-18 authentication: JWT-based, backed by a real `account_credentials` table.

`POST /login` takes `{username, password}` and verifies it against `auth/credential_store.py`
(bcrypt hash comparison) - patient accounts use their `patient_code` as `username` (a patient logs
in with the same code shown throughout the app), staff accounts use a plain username. On success
it issues a short-lived signed access token (`auth/jwt_tokens.py`, `JWT_EXPIRE_MINUTES` in
`.env.example`); there is no server-side session record, so `POST /logout` only needs the client
to discard the token - it does not (and structurally cannot) revoke it early. This is stateless by
design, not an oversight (see `jwt_tokens.py`'s docstring).

`GET /demo-accounts` backs the login screen's quick-select buttons: it reads the real `Patient`
rows linked to the two seeded demo accounts (`api/demo_seed.py`) from Postgres, rather than a
second, hand-maintained copy of the same two names in the frontend.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from ..auth import Account
from ..auth.credential_store import verify_credentials
from ..auth.jwt_tokens import create_access_token
from ..models import Patient
from ..state.sql.repository import AsyncPostgresRepository
from .demo_seed import DEMO_PATIENT_2_ID, DEMO_PATIENT_ID, ensure_demo_seed
from .deps import get_async_repo, get_current_account
from .schemas import CamelModel

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(CamelModel):
    username: str  # a patient's patient_code, or a staff account's username
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
    await run_in_threadpool(ensure_demo_seed)
    account = await verify_credentials(body.username, body.password)
    if account is None:
        # Same generic failure regardless of cause - unknown username or wrong password are
        # indistinguishable to the caller (no account enumeration).
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = create_access_token(account.id)
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
    await run_in_threadpool(ensure_demo_seed)
    out: list[DemoAccountOut] = []
    for patient_id in (DEMO_PATIENT_ID, DEMO_PATIENT_2_ID):
        patient = await repo.get(Patient, patient_id)
        if patient is not None:
            out.append(
                DemoAccountOut(patient_code=patient.patient_code, display_name=patient.full_name)
            )
    return out


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

"""FR-22 staff patient search - scope-filtered exactly like every other list endpoint (the FR-18
permission matrix already gives `Role.COORDINATOR` `Scope.ALL` and `Role.DOCTOR`/`Role.TECHNICIAN`
`Scope.ASSIGNED` over `Patient` - this route adds only the `query` text filter on top).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth import Account, CrudOp, Role
from ..auth import Forbidden as AuthForbidden
from ..auth.permissions import list_scoped_async
from ..models import Patient
from ..state.sql.repository import AsyncPostgresRepository
from .deps import PageParams, get_async_repo, get_current_account
from .schemas import camel_schema

router = APIRouter(prefix="/staff", tags=["staff"])

PatientOut = camel_schema(Patient)


@router.get("/patients", response_model=list[PatientOut])
async def search_patients(
    query: str = "",
    page: PageParams = Depends(),
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    if account.role is Role.PATIENT:
        raise HTTPException(status_code=403, detail="role_patient may not search patients")
    try:
        patients = await list_scoped_async(repo, account, Patient, CrudOp.READ)
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    needle = query.strip().lower()
    if needle:
        patients = [
            p for p in patients if needle in p.full_name.lower() or needle in p.patient_code.lower()
        ]
    return page.slice(patients)

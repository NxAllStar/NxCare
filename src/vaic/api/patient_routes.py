"""Patient-centric read routes backing `pages/HomePage.tsx`, `JourneyPage.tsx`,
`lib/api/patient.ts` (`getPatient`, `listAppointments`, `getActiveCarePlan`,
`listPaymentsForTasks`).

`PATCH /patients/{id}/preferences` (the Settings screen's notification-channel preference,
`lib/api/settings.ts`) is deliberately NOT built here: `Patient` has no preference field in
`models/entities.py`/`docs/specs/08-data-model.md`, and bolting one on ad hoc would violate
"Follow the specs" (AGENTS.md rule 2) the same way the six deferred screens would. Flagged for
`data-modeler`/`ba-analyst`, same as the deferred screens.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import Account, CrudOp, resolve_scope
from ..auth import Forbidden as AuthForbidden
from ..auth.scope_async import matches_scope_async
from ..models import Appointment, CarePlan, CarePlanStatus, Patient, Payment
from ..state.sql.repository import AsyncPostgresRepository
from .deps import PageParams, get_async_repo, get_current_account
from .schemas import camel_schema

router = APIRouter(prefix="/patients", tags=["patients"])

PatientOut = camel_schema(Patient)
AppointmentOut = camel_schema(Appointment)
CarePlanOut = camel_schema(CarePlan)
PaymentOut = camel_schema(Payment)


async def _authorized_patient(
    patient_id: UUID, account: Account, repo: AsyncPostgresRepository
) -> Patient:
    try:
        scope = resolve_scope(account, Patient, CrudOp.READ)
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    patient = await repo.get(Patient, patient_id)
    if patient is None or not await matches_scope_async(repo, account, patient, scope):
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(
    patient_id: UUID,
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    return await _authorized_patient(patient_id, account, repo)


@router.get("/{patient_id}/appointments", response_model=list[AppointmentOut])
async def list_patient_appointments(
    patient_id: UUID,
    page: PageParams = Depends(),
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    await _authorized_patient(patient_id, account, repo)
    appointments = await repo.list(Appointment, patient_id=patient_id)
    return page.slice(sorted(appointments, key=lambda a: a.created_at, reverse=True))


@router.get("/{patient_id}/care-plan", response_model=CarePlanOut | None)
async def get_active_care_plan(
    patient_id: UUID,
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    await _authorized_patient(patient_id, account, repo)
    plans = await repo.list(CarePlan, patient_id=patient_id)
    active = [p for p in plans if p.status is not CarePlanStatus.COMPLETED]
    if not active:
        return None
    return max(active, key=lambda p: p.created_at)


@router.get("/{patient_id}/payments", response_model=list[PaymentOut])
async def list_patient_payments(
    patient_id: UUID,
    subject_id: list[UUID] = Query(default=[]),
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    """Batch read: one round trip for however many `subject_id`s the caller asks about, instead
    of the frontend's `listPaymentsForTasks` looping a call per task id."""
    await _authorized_patient(patient_id, account, repo)
    payments = await repo.list(Payment, patient_id=patient_id)
    if subject_id:
        wanted = set(subject_id)
        payments = [p for p in payments if p.subject_id in wanted]
    return payments

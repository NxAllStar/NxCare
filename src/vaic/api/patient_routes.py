"""Patient-facing HTTP surface: two coexisting layers, per the API design plan (docs/tasks) for the
async/sync split (same split `careplan_routes.py` documents).

`build_patient_router(repo)` is the demo/sync-Repository factory backing
`POST /api/patients/resolve` (TASK-038 identity reconciliation): mint-or-lookup by `patient_code`,
idempotent - the console signs orders for a patient and the patient app reads that same patient's
plan. Without one canonical id per person the two surfaces address different patients and the
cross-surface handoff (FR-04) is never observable. This endpoint is that single "give me my ids"
call both surfaces make before touching `/api/careplan/*`; it also guarantees a demo `Appointment`
exists and returns its id, since `/api/careplan/generate` requires an `appointment_id`.
`patient_code` is trusted as given here (no token yet at this bootstrap step - the caller does not
have a `Patient` id, let alone a session, until this call returns one), the same posture the
careplan/intake demo routes already take with `actor_role`/`diagnosed_by`. Local/dev demo state
only, never real patient data (agent-guardrails.md).

The module-level `router` below is the native-async, `AsyncPostgresRepository`-backed,
FR-18-authenticated read layer backing `pages/HomePage.tsx`, `JourneyPage.tsx`,
`lib/api/patient.ts` (`getPatient`, `listAppointments`, `getActiveCarePlan`, `listPaymentsForTasks`)
- reached only once a caller already holds a bearer token from `POST /auth/login`
(`auth_routes.py`), i.e. after `resolve`/`login` has already happened.

`PATCH /patients/{id}/preferences` (the Settings screen's notification-channel preference,
`lib/api/settings.ts`) is deliberately NOT built here: `Patient` has no preference field in
`models/entities.py`/`docs/specs/08-data-model.md`, and bolting one on ad hoc would violate
"Follow the specs" (AGENTS.md rule 2) the same way the six deferred screens would. Flagged for
`data-modeler`/`ba-analyst`, same as the deferred screens.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from ..auth import Account, CrudOp, resolve_scope
from ..auth import Forbidden as AuthForbidden
from ..auth.scope_async import matches_scope_async
from ..models import Appointment, CarePlan, CarePlanStatus, Patient, Payment
from ..state import Repository
from ..state.sql.repository import AsyncPostgresRepository
from .deps import PageParams, get_async_repo, get_current_account
from .schemas import camel_schema


class ResolvePatientRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patientCode: str
    fullName: str | None = None


class ResolvePatientResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patientId: str
    appointmentId: str
    patientCode: str


def build_patient_router(repo: Repository) -> APIRouter:
    """Bind the demo `Repository` into the router's closure - one repo instance per running app
    (same rationale as `build_careplan_router`: a module-level router would accumulate handlers)."""
    router = APIRouter(prefix="/api/patients", tags=["patients"])

    @router.post("/resolve", response_model=ResolvePatientResponse)
    def resolve(body: ResolvePatientRequest) -> ResolvePatientResponse:
        code = body.patientCode.strip()
        if not code:
            raise HTTPException(422, detail="patientCode must not be empty")

        existing = repo.list(Patient, patient_code=code)
        if existing:
            patient = existing[0]
        else:
            # `full_name` is PII (NFR-SEC-01); default to the code itself rather than invent a name,
            # so a mint with no name supplied never fabricates patient identity data.
            patient = repo.save(Patient(full_name=body.fullName or code, patient_code=code))

        appointments = repo.list(Appointment, patient_id=patient.id)
        if appointments:
            appointment = appointments[0]
        else:
            appointment = repo.save(Appointment(patient_id=patient.id, specialty="general"))

        return ResolvePatientResponse(
            patientId=str(patient.id),
            appointmentId=str(appointment.id),
            patientCode=code,
        )

    return router


# --- Native-async, FR-18-authenticated layer (AsyncPostgresRepository) -----------------------

router = APIRouter(prefix="/patients", tags=["patients"])

PatientOut = camel_schema(Patient, exclude={"password_hash"})
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

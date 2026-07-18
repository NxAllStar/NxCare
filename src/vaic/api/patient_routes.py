"""HTTP surface: resolve a patient's scannable code to the canonical UUID both the staff console and
the patient app must share (TASK-038 identity reconciliation).

Mint-or-lookup by `patient_code`, idempotent: the console signs orders for a patient and the patient
app reads that same patient's plan. Without one canonical id per person the two surfaces address
different patients and the cross-surface handoff (FR-04) is never observable. This endpoint is that
single "give me my ids" call both surfaces make before touching `/api/careplan/*`.

It also guarantees a demo `Appointment` exists and returns its id, since `/api/careplan/generate`
requires an `appointment_id`; returning it here lets the console call generate without a separate
seed round-trip.

No auth yet (FR-18 is a separate task): `patient_code` is trusted as given, the same posture the
careplan/intake routes already take with `actor_role`/`diagnosed_by`. This is local/dev demo state,
never real patient data (agent-guardrails.md).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from ..models import Appointment, Patient
from ..state import Repository


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

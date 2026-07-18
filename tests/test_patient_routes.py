"""POST /api/patients/resolve: mint-or-lookup a patient by scannable code (TASK-038 identity).

Standalone FastAPI app over an isolated `InMemoryRepository`, same pattern as
`tests/test_careplan_routes.py`.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from vaic.api.patient_routes import build_patient_router
from vaic.models import Appointment, Patient
from vaic.state import InMemoryRepository


def _client(repo):
    app = FastAPI()
    app.include_router(build_patient_router(repo))
    return TestClient(app)


def test_resolve_mints_new_patient_and_appointment():
    repo = InMemoryRepository()
    client = _client(repo)

    response = client.post(
        "/api/patients/resolve",
        json={"patientCode": "BN-941207", "fullName": "Nguyen Thi Lan"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["patientCode"] == "BN-941207"
    patient = repo.get(Patient, UUID(body["patientId"]))
    assert patient is not None
    assert patient.patient_code == "BN-941207"
    assert patient.full_name == "Nguyen Thi Lan"
    appointment = repo.get(Appointment, UUID(body["appointmentId"]))
    assert appointment is not None
    assert appointment.patient_id == patient.id


def test_resolve_is_idempotent_by_code():
    repo = InMemoryRepository()
    client = _client(repo)

    first = client.post("/api/patients/resolve", json={"patientCode": "BN-1"}).json()
    second = client.post("/api/patients/resolve", json={"patientCode": "BN-1"}).json()

    assert first["patientId"] == second["patientId"]
    assert first["appointmentId"] == second["appointmentId"]
    assert len(repo.list(Patient)) == 1
    assert len(repo.list(Appointment)) == 1


def test_resolve_trims_and_rejects_an_empty_code():
    repo = InMemoryRepository()
    client = _client(repo)

    response = client.post("/api/patients/resolve", json={"patientCode": "   "})

    assert response.status_code == 422
    assert repo.list(Patient) == []


def test_resolve_defaults_full_name_to_code_when_absent():
    repo = InMemoryRepository()
    client = _client(repo)

    body = client.post("/api/patients/resolve", json={"patientCode": "BN-X"}).json()

    patient = repo.get(Patient, UUID(body["patientId"]))
    assert patient is not None
    assert patient.full_name == "BN-X"

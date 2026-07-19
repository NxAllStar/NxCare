"""FR-03/FR-04/FR-08 (FR-23 v2.3) HTTP surface: POST /api/careplan/generate.

Builds a standalone FastAPI app around an isolated `InMemoryRepository` (never the process-wide
demo app in `vaic.api.app`) so each test starts from clean, known state - same pattern the intake
chat endpoint would use if it had route-level tests.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from vaic.api.careplan_routes import build_careplan_router
from vaic.models import (
    Appointment,
    ExecutionStatus,
    PaymentStatus,
    Resource,
    ResourceType,
    ServiceType,
    Task,
)
from vaic.state import InMemoryRepository

CAREPLAN_STATIONS = [uuid4(), uuid4()]


def _client(repo):
    app = FastAPI()
    app.include_router(build_careplan_router(repo))
    return TestClient(app)


def _seed_stations(repo):
    for station_id in CAREPLAN_STATIONS:
        repo.save(Resource(id=station_id, type=ResourceType.TECHNICIAN, department_id=uuid4(),
                            is_available=True, capacity_per_hour=10))


def _patch_router_stations(monkeypatch):
    """Point the router's fixed demo station pool at this test's own resources."""
    monkeypatch.setattr(
        "vaic.api.careplan_routes.DEMO_CAREPLAN_STATIONS", tuple(CAREPLAN_STATIONS)
    )


def test_generate_resolves_names_sequences_and_slots_the_route(monkeypatch):
    repo = InMemoryRepository()
    _patch_router_stations(monkeypatch)
    _seed_stations(repo)
    repo.save(ServiceType(
        code="BLOOD_TEST", display_label="Xet nghiem mau",
        requires_fasting=True, turnaround_minutes=30, default_duration_min=10,
    ))
    repo.save(ServiceType(code="XRAY", display_label="Chup X-quang", default_duration_min=15))
    appointment = repo.save(Appointment(patient_id=uuid4(), specialty="general"))

    client = _client(repo)
    response = client.post(
        "/api/careplan/generate",
        json={
            "patient_id": str(appointment.patient_id),
            "appointment_id": str(appointment.id),
            "diagnosed_by": str(uuid4()),
            "actor_role": "role_doctor",
            "conditions": ["fever"],
            "service_type_names": ["blood_test", "Chup X-quang"],
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ACTIVE"
    assert body["allSlotted"] is True
    assert len(body["route"]) == 2
    assert {step["serviceTypeCode"] for step in body["route"]} == {"BLOOD_TEST", "XRAY"}
    for step in body["route"]:
        assert step["resourceId"] in {str(s) for s in CAREPLAN_STATIONS}
        assert step["start"] is not None


def test_generate_rejects_unknown_appointment(monkeypatch):
    repo = InMemoryRepository()
    _patch_router_stations(monkeypatch)
    _seed_stations(repo)

    client = _client(repo)
    response = client.post(
        "/api/careplan/generate",
        json={
            "patient_id": str(uuid4()),
            "appointment_id": str(uuid4()),
            "diagnosed_by": str(uuid4()),
            "service_type_names": ["blood_test"],
        },
    )

    assert response.status_code == 404


def test_generate_refuses_the_whole_request_when_a_test_name_does_not_resolve(monkeypatch):
    repo = InMemoryRepository()
    _patch_router_stations(monkeypatch)
    _seed_stations(repo)
    repo.save(ServiceType(code="BLOOD_TEST", display_label="Xet nghiem mau",
                          default_duration_min=10))
    appointment = repo.save(Appointment(patient_id=uuid4(), specialty="general"))

    client = _client(repo)
    response = client.post(
        "/api/careplan/generate",
        json={
            "patient_id": str(appointment.patient_id),
            "appointment_id": str(appointment.id),
            "diagnosed_by": str(uuid4()),
            "service_type_names": ["blood_test", "Does Not Exist"],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["unmatchedServiceNames"] == ["Does Not Exist"]


def test_generate_routes_to_the_least_busy_station_first(monkeypatch):
    repo = InMemoryRepository()
    _patch_router_stations(monkeypatch)
    _seed_stations(repo)
    repo.save(ServiceType(code="ULTRASOUND", display_label="Sieu am", default_duration_min=20))
    appointment = repo.save(Appointment(patient_id=uuid4(), specialty="general"))

    busy_station, light_station = CAREPLAN_STATIONS
    repo.save(Task(care_plan_id=uuid4(), service_order_id=uuid4(), owner_id=busy_station,
                    payment_status=PaymentStatus.PAID, execution_status=ExecutionStatus.PENDING,
                    estimated_duration_min=200))

    client = _client(repo)
    response = client.post(
        "/api/careplan/generate",
        json={
            "patient_id": str(appointment.patient_id),
            "appointment_id": str(appointment.id),
            "diagnosed_by": str(uuid4()),
            "service_type_names": ["ultrasound"],
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["route"][0]["resourceId"] == str(light_station)


def test_get_active_care_plan_returns_the_generated_route(monkeypatch):
    repo = InMemoryRepository()
    _patch_router_stations(monkeypatch)
    _seed_stations(repo)
    repo.save(ServiceType(code="BLOOD_TEST", display_label="Xet nghiem mau",
                          requires_fasting=True, turnaround_minutes=30, default_duration_min=10))
    appointment = repo.save(Appointment(patient_id=uuid4(), specialty="general"))

    client = _client(repo)
    generated = client.post(
        "/api/careplan/generate",
        json={
            "patient_id": str(appointment.patient_id),
            "appointment_id": str(appointment.id),
            "diagnosed_by": str(uuid4()),
            "service_type_names": ["blood_test"],
        },
    )
    assert generated.status_code == 200, generated.text

    response = client.get(f"/api/careplan/patient/{appointment.patient_id}/active")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["carePlanId"] == generated.json()["carePlanId"]
    assert body["status"] == "ACTIVE"
    assert len(body["tasks"]) == 1
    task = body["tasks"][0]
    assert task["serviceTypeCode"] == "BLOOD_TEST"
    assert task["executionStatus"] == "LOCKED"
    assert task["paymentStatus"] == "UNPAID"


def test_get_active_care_plan_404s_when_patient_has_none(monkeypatch):
    repo = InMemoryRepository()
    _patch_router_stations(monkeypatch)
    _seed_stations(repo)

    client = _client(repo)
    response = client.get(f"/api/careplan/patient/{uuid4()}/active")

    assert response.status_code == 404

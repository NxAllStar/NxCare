"""The real-time seam on /api/careplan: generate publishes a refresh event, and /stream serves SSE
(TASK-038). Standalone app over an isolated repo, same pattern as `tests/test_careplan_routes.py`.
"""

from __future__ import annotations

import asyncio
from asyncio import QueueEmpty
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from vaic.api.careplan_routes import _sse_stream, build_careplan_router
from vaic.api.events import CarePlanEventBus
from vaic.models import Appointment, Resource, ResourceType, ServiceType
from vaic.state import InMemoryRepository

STATIONS = [uuid4(), uuid4()]


def _seed(repo):
    for station_id in STATIONS:
        repo.save(
            Resource(
                id=station_id,
                type=ResourceType.TECHNICIAN,
                department_id=uuid4(),
                is_available=True,
                capacity_per_hour=10,
            )
        )
    repo.save(
        ServiceType(code="BLOOD_TEST", display_label="Xet nghiem mau", default_duration_min=10)
    )


def _generate_body(repo):
    patient_id = uuid4()
    appointment = repo.save(Appointment(patient_id=patient_id, specialty="general"))
    return patient_id, {
        "patient_id": str(patient_id),
        "appointment_id": str(appointment.id),
        "diagnosed_by": str(uuid4()),
        "service_type_names": ["Xet nghiem mau"],
    }


def test_generate_publishes_update_event_to_the_subscribed_patient(monkeypatch):
    monkeypatch.setattr("vaic.api.careplan_routes.DEMO_CAREPLAN_STATIONS", tuple(STATIONS))
    repo = InMemoryRepository()
    _seed(repo)
    bus = CarePlanEventBus()
    app = FastAPI()
    app.include_router(build_careplan_router(repo, bus))
    client = TestClient(app)

    patient_id, body = _generate_body(repo)
    queue = bus.subscribe(patient_id)
    response = client.post("/api/careplan/generate", json=body)

    assert response.status_code == 200
    event = queue.get_nowait()
    assert event["type"] == "careplan.updated"
    assert event["carePlanId"] == response.json()["carePlanId"]


def test_generate_does_not_notify_other_patients(monkeypatch):
    monkeypatch.setattr("vaic.api.careplan_routes.DEMO_CAREPLAN_STATIONS", tuple(STATIONS))
    repo = InMemoryRepository()
    _seed(repo)
    bus = CarePlanEventBus()
    app = FastAPI()
    app.include_router(build_careplan_router(repo, bus))
    client = TestClient(app)

    _, body = _generate_body(repo)
    other_queue = bus.subscribe(uuid4())
    client.post("/api/careplan/generate", json=body)

    with pytest.raises(QueueEmpty):
        other_queue.get_nowait()


def test_generate_still_succeeds_without_a_bus(monkeypatch):
    monkeypatch.setattr("vaic.api.careplan_routes.DEMO_CAREPLAN_STATIONS", tuple(STATIONS))
    repo = InMemoryRepository()
    _seed(repo)
    app = FastAPI()
    app.include_router(build_careplan_router(repo))  # no bus
    client = TestClient(app)

    _, body = _generate_body(repo)
    response = client.post("/api/careplan/generate", json=body)

    assert response.status_code == 200


def test_stream_returns_503_when_no_bus_is_wired():
    repo = InMemoryRepository()
    app = FastAPI()
    app.include_router(build_careplan_router(repo))
    client = TestClient(app)

    response = client.get(f"/api/careplan/patient/{uuid4()}/stream")

    assert response.status_code == 503


def test_sse_stream_yields_connected_then_the_published_event():
    bus = CarePlanEventBus()
    patient_id = uuid4()

    async def run():
        gen = _sse_stream(bus, patient_id, heartbeat=0.05)
        first = await gen.__anext__()
        bus.publish(patient_id, {"type": "careplan.updated", "carePlanId": "cp-1"})
        second = await gen.__anext__()
        await gen.aclose()
        return first, second

    first, second = asyncio.run(run())
    assert first == ": connected\n\n"
    assert second == 'data: {"type": "careplan.updated", "carePlanId": "cp-1"}\n\n'


def test_sse_stream_emits_keep_alive_when_idle():
    bus = CarePlanEventBus()
    patient_id = uuid4()

    async def run():
        gen = _sse_stream(bus, patient_id, heartbeat=0.01)
        await gen.__anext__()  # ": connected"
        heartbeat = await gen.__anext__()  # nothing published -> heartbeat after timeout
        await gen.aclose()
        return heartbeat

    assert asyncio.run(run()) == ": keep-alive\n\n"


def test_sse_stream_unsubscribes_on_close():
    bus = CarePlanEventBus()
    patient_id = uuid4()

    async def run():
        gen = _sse_stream(bus, patient_id, heartbeat=1)
        await gen.__anext__()
        assert bus.subscriber_count(patient_id) == 1
        await gen.aclose()

    asyncio.run(run())
    assert bus.subscriber_count(patient_id) == 0

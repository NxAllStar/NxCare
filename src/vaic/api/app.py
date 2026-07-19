"""FastAPI entry point (tech-stack.md "Serving: FastAPI").

`create_app` builds one process-wide demo `Repository`, seeds it (`demo_state.py`), and mounts the
sync/demo routers (intake, careplan, patient, staff, coordinator) alongside the native-async,
`AsyncPostgresRepository` + FR-18-authenticated routers (auth, appointments, careplan, journey,
notifications, patient, forecast, disruption, dashboard, staff) - see the API design plan
(docs/tasks) for why both layers coexist rather than one replacing the other. CORS is opened only
to the configured frontend origin(s) - never `*` with credentials (security-privacy.md "Permissive
CORS").
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..models import AuditLogEntry, Diagnosis, ScanEvent, ServiceOrder, ServiceType, Slot
from . import (
    appointment_routes,
    auth_routes,
    careplan_routes,
    dashboard_routes,
    disruption_routes,
    forecast_routes,
    journey_routes,
    notifications_routes,
    patient_routes,
    staff_routes,
)
from .careplan_routes import build_careplan_router
from .coordinator_routes import build_coordinator_router
from .crud import build_entity_router
from .demo_state import (
    build_repository,
    seed_arrival_demo,
    seed_consult_queue_demo,
    seed_demo_careplan_stations,
    seed_demo_patients,
    seed_demo_resources,
    seed_demo_service_catalog,
    seed_service_types_demo,
    sync_service_types_from_postgres,
)
from .events import CarePlanEventBus
from .intake_routes import build_intake_router
from .patient_routes import build_patient_router
from .staff_routes import build_staff_router


def create_app() -> FastAPI:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "info").upper())

    bus = CarePlanEventBus()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        # Record the serving loop so the synchronous `/generate` handler (run in a worker thread)
        # can hand SSE events back to the loop threadsafely (see events.py).
        bus.bind_loop(asyncio.get_running_loop())
        yield

    app = FastAPI(title="VAIC API (demo)", version="0.1.0", lifespan=lifespan)

    origins = [
        origin.strip()
        for origin in os.environ.get("VAIC_CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["*"],
    )

    repo = build_repository()
    seed_demo_resources(repo)
    seed_demo_careplan_stations(repo)
    seed_demo_patients(repo)
    # Postgres config wins; the demo catalog only fills codes it did not supply (idempotent).
    sync_service_types_from_postgres(repo)
    seed_demo_service_catalog(repo)
    seed_arrival_demo(repo)
    seed_service_types_demo(repo)
    seed_consult_queue_demo(repo)  # requires seed_arrival_demo to have run first (its department)
    app.include_router(build_intake_router(repo))
    app.include_router(build_careplan_router(repo, bus))
    app.include_router(build_patient_router(repo))
    app.include_router(build_staff_router(repo))
    app.include_router(build_coordinator_router(repo))

    # Native-async routers (AsyncPostgresRepository) and sync-adapter-bridged routers (existing
    # agents/* business logic) - see the API design plan (docs/tasks) for the async/sync split.
    app.include_router(auth_routes.router)
    app.include_router(patient_routes.router)
    app.include_router(appointment_routes.router)
    app.include_router(careplan_routes.router)
    app.include_router(journey_routes.router)
    app.include_router(notifications_routes.router)
    app.include_router(forecast_routes.router)
    app.include_router(disruption_routes.router)
    app.include_router(dashboard_routes.router)
    app.include_router(staff_routes.router)

    # Reference/log entities with no special business rule (DRY: one factory, see api/crud.py).
    app.include_router(build_entity_router(ServiceType, "/service-types", ["service-types"]))
    app.include_router(build_entity_router(Slot, "/slots-log", ["slots"]))
    app.include_router(build_entity_router(Diagnosis, "/diagnoses-log", ["diagnoses"]))
    app.include_router(build_entity_router(ServiceOrder, "/service-orders", ["service-orders"]))
    app.include_router(build_entity_router(ScanEvent, "/scan-events", ["scan-events"]))
    app.include_router(build_entity_router(AuditLogEntry, "/audit-log", ["audit-log"]))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

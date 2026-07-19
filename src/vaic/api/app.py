"""FastAPI entry point (tech-stack.md "Serving: FastAPI").

`create_app` builds one process-wide demo `Repository`, seeds it (`demo_state.py`), and mounts the
intake router. CORS is opened only to the configured frontend origin(s) - never `*` with
credentials (security-privacy.md "Permissive CORS").
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .careplan_routes import build_careplan_router
from .demo_state import (
    build_repository,
    seed_demo_careplan_stations,
    seed_demo_patients,
    seed_demo_resources,
    seed_demo_service_catalog,
    sync_service_types_from_postgres,
)
from .events import CarePlanEventBus
from .intake_routes import build_intake_router
from .patient_routes import build_patient_router


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
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    repo = build_repository()
    seed_demo_resources(repo)
    seed_demo_careplan_stations(repo)
    seed_demo_patients(repo)
    # Postgres config wins; the demo catalog only fills codes it did not supply (idempotent).
    sync_service_types_from_postgres(repo)
    seed_demo_service_catalog(repo)
    app.include_router(build_intake_router(repo))
    app.include_router(build_careplan_router(repo, bus))
    app.include_router(build_patient_router(repo))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

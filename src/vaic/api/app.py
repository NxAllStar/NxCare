"""FastAPI entry point (tech-stack.md "Serving: FastAPI").

`create_app` builds one process-wide demo `Repository`, seeds it (`demo_state.py`), and mounts the
intake router (patient-facing) and the staff router (front-desk/doctor-facing consult-queue
actions). CORS is opened only to the configured frontend origin(s) - never `*` with credentials
(security-privacy.md "Permissive CORS").
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .coordinator_routes import build_coordinator_router
from .demo_state import (
    build_repository,
    seed_arrival_demo,
    seed_consult_queue_demo,
    seed_demo_care_plan,
    seed_demo_resources,
    seed_service_types_demo,
)
from .intake_routes import build_intake_router
from .staff_routes import build_staff_router


def create_app() -> FastAPI:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "info").upper())
    app = FastAPI(title="VAIC API (demo)", version="0.1.0")

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
    seed_arrival_demo(repo)
    seed_service_types_demo(repo)
    seed_demo_care_plan(repo)
    seed_consult_queue_demo(repo)
    app.include_router(build_intake_router(repo))
    app.include_router(build_staff_router(repo))
    app.include_router(build_coordinator_router(repo))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

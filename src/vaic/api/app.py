"""FastAPI entry point (tech-stack.md "Serving: FastAPI").

`create_app` builds one process-wide demo `Repository`, seeds it (`demo_state.py`), and mounts the
intake router. CORS is opened only to the configured frontend origin(s) - never `*` with
credentials (security-privacy.md "Permissive CORS").
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .demo_state import build_repository, seed_demo_resources
from .intake_routes import build_intake_router


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
    app.include_router(build_intake_router(repo))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

"""FastAPI serving layer (tech-stack.md "Serving: FastAPI").

Framework-agnostic domain code (agents, state, forecast) lives elsewhere; this package is the only
place that knows about HTTP. `create_app` is the single entry point `uvicorn` targets.
"""

from __future__ import annotations

from .app import create_app

__all__ = ["create_app"]

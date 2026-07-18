"""The action unit that flows from an agent, through the checker, to a tool."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: str
    actor: str  # agent name or human role, for the audit log (never a secret / PII)
    params: dict[str, Any] = {}
    reasoning: str = ""


class Decision(BaseModel):
    allowed: bool
    reason: str = ""


class ActionResult(BaseModel):
    allowed: bool  # did it pass the closed-action-space + constraint checks
    ok: bool  # did the tool run successfully (only meaningful when allowed)
    reason: str = ""
    output: dict | None = None
    audit_id: UUID | None = None

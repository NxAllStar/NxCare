"""HTTP surface for one Intake Agent chat turn (FR-01, FR-02, BF-05).

Wires the existing, already-tested domain logic (`extract_triage`, `recommend_slots`) behind a
single endpoint instead of duplicating triage/emergency rules in the frontend. Patient chat text is
untrusted content (NFR-SEC-11): it is passed into `extract_triage` as DATA and is never echoed back
beyond the fixed reply strings below.

`DemoTriageLLM` and `DemoForecastLLM` are deterministic placeholders, not a real model client -
tech-stack.md's self-hosted Qwen provider for Intake is not wired yet (no credential exists for it
in this environment, and model-policy.md gates real provider calls). `DemoForecastLLM` always
raises `ForecastLLMError`, which `estimate_wait` already handles by falling back to the tested
deterministic BASELINE path (BR-03) - no new math is invented here.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from ..agents.intake.emergency import detect_emergency
from ..agents.intake.slots import recommend_slots
from ..agents.intake.triage import TriageLLM, extract_triage
from ..forecast import ForecastLLMError
from ..state import Repository
from .demo_state import DEMO_OWNER_BUSY, DEMO_OWNER_LIGHT

router = APIRouter(prefix="/api/intake", tags=["intake"])

# Same fixed reference date the intake booking path uses (agents/intake/agent.py), so a slot's
# `start` here lines up with what a later `book_appointment` call against `hour` would produce.
_BOOKING_REFERENCE_DATE = datetime(2026, 1, 1, tzinfo=UTC)
_DEMO_HOURS = [9, 10]
_DEMO_SPECIALTY = "NOI_TONG_QUAT"

_EMERGENCY_REPLY_VI = (
    "Trieu chung ban mo ta co the la tinh huong khan cap. Vui long lien he nhan vien y te ngay "
    "hoac goi 115 - minh chua the xep lich thuong quy trong truong hop nay."
)
_ROUTINE_REPLY_VI = (
    "Cam on ban da mo ta trieu chung. Day la goi y dinh tuyen, khong phai chan doan - minh de xuat "
    "vai khung gio it dong ben duoi."
)


class DemoTriageLLM:
    """Deterministic stand-in for the real `TriageLLM` client (see module docstring)."""

    def extract(self, prompt: dict) -> dict:
        del prompt  # the deterministic demo path does not vary by transcript content
        return {
            "specialty": _DEMO_SPECIALTY,
            "priority_level": "ROUTINE",
            "constraints": [],
            "emergency_suspected": False,
        }


class DemoForecastLLM:
    """Deterministic stand-in that always defers to the tested BASELINE fallback (see docstring)."""

    def estimate_wait(self, features: dict[str, Any]) -> dict[str, Any]:
        del features
        raise ForecastLLMError("no live forecast provider configured in this demo")


_TRIAGE_LLM: TriageLLM = DemoTriageLLM()
_FORECAST_LLM = DemoForecastLLM()


def _load_level(eta_minutes: float) -> str:
    if eta_minutes < 20:
        return "low"
    if eta_minutes < 45:
        return "medium"
    return "high"


def _eta_label(eta_minutes: float) -> str:
    # A range, never a hard number (PRD-FR-12 6.1) - bucketed to the nearest 15-minute band.
    low = int(eta_minutes // 15) * 15
    return f"~{low}-{low + 15} phut"


class IntakeChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    sender: str
    text: str
    createdAt: str
    aiGenerated: bool


class RankedSlotSuggestionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slotId: str
    specialty: str
    start: str
    etaLabel: str
    loadLevel: str


class IntakeChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply: ChatMessageOut
    suggestedSlots: list[RankedSlotSuggestionOut]
    emergencySuspected: bool


def build_intake_router(repo: Repository) -> APIRouter:
    """Bind the demo `Repository` into the router's closure - one repo instance per running app."""

    @router.post("/chat", response_model=IntakeChatResponse)
    def chat(body: IntakeChatRequest) -> IntakeChatResponse:
        triage = extract_triage(body.text, _TRIAGE_LLM)
        # Deterministic override belt-and-suspenders (AC-01.2): extract_triage already runs this
        # check internally, re-checking here costs nothing and keeps this handler self-evident.
        emergency = triage.emergency_suspected or detect_emergency(body.text, triage.priority_level)
        now = datetime.now(UTC).isoformat()

        if emergency:
            return IntakeChatResponse(
                reply=ChatMessageOut(
                    id=str(uuid4()),
                    sender="agent",
                    text=_EMERGENCY_REPLY_VI,
                    createdAt=now,
                    aiGenerated=True,
                ),
                suggestedSlots=[],
                emergencySuspected=True,
            )

        proposals = recommend_slots(
            repo,
            _DEMO_SPECIALTY,
            [DEMO_OWNER_LIGHT, DEMO_OWNER_BUSY],
            _DEMO_HOURS,
            _FORECAST_LLM,
        )
        suggested = [
            RankedSlotSuggestionOut(
                slotId=f"{proposal.owner_id}-{proposal.hour}",
                specialty=_DEMO_SPECIALTY,
                start=(_BOOKING_REFERENCE_DATE + timedelta(hours=proposal.hour)).isoformat(),
                etaLabel=_eta_label(proposal.eta_minutes),
                loadLevel=_load_level(proposal.eta_minutes),
            )
            for proposal in proposals
        ]

        return IntakeChatResponse(
            reply=ChatMessageOut(
                id=str(uuid4()),
                sender="agent",
                text=_ROUTINE_REPLY_VI,
                createdAt=now,
                aiGenerated=True,
            ),
            suggestedSlots=suggested,
            emergencySuspected=False,
        )

    return router

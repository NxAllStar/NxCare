"""HTTP surface for one Intake Agent chat turn (FR-01, FR-02, BF-05).

Wires the existing, already-tested domain logic (`extract_triage`, `recommend_slots`) behind a
single endpoint instead of duplicating triage/emergency rules in the frontend. Patient chat text is
untrusted content (NFR-SEC-11): it is passed into `extract_triage` as DATA and is never echoed back
beyond the fixed reply strings below.

Triage extraction uses the real `HttpTriageLLM` (an OpenAI-compatible client against
`LLM_API_BASE_URL`) when `Settings.chat_configured`, built once at router-construction time by
`build_triage_llm` (`agents/intake/llm_client.py`). A per-request provider failure or malformed
output degrades to the deterministic `RuleBasedTriageLLM` for that one request rather than a 500 -
the same "validation failure is a handled outcome" posture as the forecast baseline (ai-governance.md).

`DemoForecastLLM` is still a deterministic placeholder: no forecast provider is wired yet
(model-policy.md gates real provider calls, and this task's scope is the triage/chat path). It
always raises `ForecastLLMError`, which `estimate_wait` already handles by falling back to the
tested deterministic BASELINE path (BR-03) - no new math is invented here.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, ValidationError

from ..agents.intake.emergency import detect_emergency
from ..agents.intake.llm_client import RuleBasedTriageLLM, TriageLLMError, build_triage_llm
from ..agents.intake.slots import recommend_slots
from ..agents.intake.triage import extract_triage
from ..forecast import ForecastLLMError
from ..state import Repository
from .demo_state import DEMO_OWNER_BUSY, DEMO_OWNER_LIGHT

router = APIRouter(prefix="/api/intake", tags=["intake"])
logger = logging.getLogger(__name__)

# Same fixed reference date the intake booking path uses (agents/intake/agent.py), so a slot's
# `start` here lines up with what a later `book_appointment` call against `hour` would produce.
_BOOKING_REFERENCE_DATE = datetime(2026, 1, 1, tzinfo=UTC)
_DEMO_HOURS = [9, 10]

_EMERGENCY_REPLY_VI = (
    "Trieu chung ban mo ta co the la tinh huong khan cap. Vui long lien he nhan vien y te ngay "
    "hoac goi 115 - minh chua the xep lich thuong quy trong truong hop nay."
)
_ROUTINE_REPLY_VI = (
    "Cam on ban da mo ta trieu chung. Day la goi y dinh tuyen, khong phai chan doan - minh de xuat "
    "vai khung gio it dong ben duoi."
)


class DemoForecastLLM:
    """Deterministic stand-in that always defers to the tested BASELINE fallback (see docstring)."""

    def estimate_wait(self, features: dict[str, Any]) -> dict[str, Any]:
        del features
        raise ForecastLLMError("no live forecast provider configured in this demo")


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

    triage_llm = build_triage_llm()  # real HttpTriageLLM when configured, else RuleBasedTriageLLM

    @router.post("/chat", response_model=IntakeChatResponse)
    def chat(body: IntakeChatRequest) -> IntakeChatResponse:
        try:
            triage = extract_triage(body.text, triage_llm)
            logger.info(
                "intake triage via real provider: specialty=%s priority=%s",
                triage.specialty,
                triage.priority_level,
            )
        except (TriageLLMError, ValidationError) as exc:
            # Degrade this one request to the deterministic extractor rather than a 500
            # (ai-governance.md "validation failure is a handled outcome") - never trust or retry
            # with a half-parsed provider response. Log the class of failure, never the transcript
            # (D8, NFR-SEC-11): `exc` here is a provider/schema error message, not patient content.
            logger.warning("intake triage provider degraded to rule-based fallback: %s", exc)
            triage = extract_triage(body.text, RuleBasedTriageLLM())
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

        # The two demo Resources are generic stand-ins, not specialty-mapped (no specialty->owner
        # directory exists in this demo yet - slots.py's `recommend_slots` docstring notes that
        # mapping is the caller's responsibility). The specialty LABEL shown to the patient is still
        # the real triage classification, not a hardcoded value.
        proposals = recommend_slots(
            repo,
            triage.specialty,
            [DEMO_OWNER_LIGHT, DEMO_OWNER_BUSY],
            _DEMO_HOURS,
            _FORECAST_LLM,
        )
        suggested = [
            RankedSlotSuggestionOut(
                slotId=f"{proposal.owner_id}-{proposal.hour}",
                specialty=triage.specialty,
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

"""HTTP surface for the patient assistant: one chat endpoint, plus confirm.

A single `/chat` turn drives everything (there is no separate triage/slot endpoint any more): the
patient's message is untrusted DATA (NFR-SEC-11), a deterministic red-flag check gates emergencies
(BF-05), and otherwise the assistant agent decides intent - it suggests the least-crowded arrival
times when the patient is asking *when to come*, and just replies normally otherwise. Reservation
data is retrieved from the store in code (`summarize_reservations`) and the agent reasons over it
(grounding contract); the model never invents counts and its output is schema-validated before use.

The assistant uses the real `HttpArrivalChatLLM` (OpenAI-compatible against `LLM_API_BASE_URL`) when
a provider is configured, else a deterministic fallback - "real agent when configured, safe
deterministic behaviour otherwise" (ai-governance.md). `/confirm` logs the patient's accepted time.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from ..agents.intake.arrival import confirm_arrival_slot, summarize_reservations
from ..agents.intake.arrival_chat import respond_to_chat
from ..agents.intake.arrival_llm_client import build_arrival_chat_llm
from ..agents.intake.emergency import detect_emergency
from ..models import PriorityLevel
from ..state import Repository
from .demo_state import ARRIVAL_DEMO_ANCHOR, ARRIVAL_DEMO_DAYS

logger = logging.getLogger(__name__)

_DEFAULT_SPECIALTY = "GENERAL_MEDICINE"

_EMERGENCY_REPLY = (
    "The symptoms you describe may be an emergency. Please contact a medical staff member now or "
    "call emergency services - I can't schedule a routine visit in this case."
)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str  # the patient's message; untrusted content, used as DATA only


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    sender: str
    text: str
    createdAt: str
    aiGenerated: bool


class ArrivalBlockOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str  # YYYY-MM-DD
    startHour: int
    endHour: int
    reservationCount: int
    reason: str


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply: ChatMessageOut  # the agent's natural-language answer
    intent: str  # "SCHEDULE" | "CHAT" | "EMERGENCY"
    recommendations: list[ArrivalBlockOut]  # time blocks (empty unless intent == SCHEDULE)
    emergencySuspected: bool


class ConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patientId: str
    start: str  # ISO datetime of the accepted time
    specialty: str | None = None  # optional; a time-block arrival is not specialty-bound yet
    ownerId: str | None = None  # optional; the doctor is assigned at the desk on arrival


class ConfirmResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appointmentId: str
    ownerId: str | None
    start: str
    status: str


def build_intake_router(repo: Repository) -> APIRouter:
    """Bind the demo `Repository` into the router's closure - one repo instance per running app.

    The router is constructed here (not a module-global) so each call returns an independent router
    bound to its own repo; a shared global would re-register routes and leak repos across callers.
    """
    router = APIRouter(prefix="/api/intake", tags=["intake"])
    assistant_llm = build_arrival_chat_llm()  # real client when configured, else deterministic

    @router.post("/chat", response_model=ChatResponse)
    def chat(body: ChatRequest) -> ChatResponse:
        """One chat turn: emergency-gate, then the agent replies (and suggests times on intent)."""
        now = datetime.now(UTC).isoformat()

        def _message(text: str) -> ChatMessageOut:
            return ChatMessageOut(
                id=str(uuid4()), sender="agent", text=text, createdAt=now, aiGenerated=True
            )

        # Safety gate first (BF-05): a red-flag message is never answered with a scheduling
        # suggestion. Deterministic check on the raw text - no LLM needed to refuse an emergency.
        if detect_emergency(body.text, PriorityLevel.ROUTINE):
            return ChatResponse(
                reply=_message(_EMERGENCY_REPLY),
                intent="EMERGENCY",
                recommendations=[],
                emergencySuspected=True,
            )

        # Grounding: search the store for reservations vs working hours (code), then the agent
        # reasons over that summary and decides intent itself.
        summary = summarize_reservations(repo, ARRIVAL_DEMO_ANCHOR, ARRIVAL_DEMO_DAYS)
        reply = respond_to_chat(body.text, summary, assistant_llm)
        logger.info("assistant intent=%s blocks=%d", reply.intent, len(reply.recommendations))

        return ChatResponse(
            reply=_message(reply.message),
            intent=reply.intent,
            recommendations=[
                ArrivalBlockOut(
                    date=block.date,
                    startHour=block.start_hour,
                    endHour=block.end_hour,
                    reservationCount=block.reservation_count,
                    reason=block.reason,
                )
                for block in reply.recommendations
            ],
            emergencySuspected=False,
        )

    @router.post("/confirm", response_model=ConfirmResponse)
    def confirm(body: ConfirmRequest) -> ConfirmResponse:
        """Log the patient's accepted arrival time as a PROPOSED Appointment (log which time)."""
        try:
            patient_id = UUID(body.patientId)
            owner_id = UUID(body.ownerId) if body.ownerId else None
            start = datetime.fromisoformat(body.start)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid id or datetime") from exc

        appointment = confirm_arrival_slot(
            repo, patient_id, body.specialty or _DEFAULT_SPECIALTY, start, owner_id
        )
        return ConfirmResponse(
            appointmentId=str(appointment.id),
            ownerId=str(appointment.owner_id) if appointment.owner_id else None,
            start=appointment.slot_start.isoformat(),
            status=appointment.status.value,
        )

    return router

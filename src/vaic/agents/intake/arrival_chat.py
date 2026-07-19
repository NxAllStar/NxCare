"""The patient assistant: one chat that answers normally, and suggests arrival times on intent.

A single agent turn. The reasoner is given the patient message (untrusted DATA) plus a reservation
summary (CONTEXT) and decides the intent itself:

- `SCHEDULE` - the patient wants to know when to come / avoid the crowd -> it recommends the
  least-crowded time blocks, grounded in the retrieved reservation counts (never invented).
- `CHAT` - anything else -> it just replies helpfully, with no recommendations.

`respond_to_chat` runs the retrieve -> reason -> validate flow on PocketFlow behind agent-core
(ADR-001), exactly like the Journey chat. A real LLM answers when a provider is configured
(`arrival_llm_client.build_arrival_chat_llm`); the deterministic reasoner here is only the
offline/failure fallback. Model output is never trusted - it reaches the caller only through
`AssistantReply` validation (NFR-SEC-12), and the schema bounds hours so an out-of-range block is
rejected.
"""

from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ..core import run_reason_flow
from .arrival import CLOSE_HOUR, OPEN_HOUR, DayLoad

AssistantIntent = Literal["SCHEDULE", "CHAT"]

# Deterministic-fallback-only hints that a message is about *when* to come. The real LLM classifies
# intent on its own; this list is used solely by the offline reasoner below.
_SCHEDULE_MARKERS = (
    "when", "what time", "which time", "time to come", "come in", "arrive", "schedule",
    "appointment", "book", "gio", "khi nao", "luc nao", "may gio", "den kham", "di kham",
    "di benh vien", "dat lich", "hen kham", "lich kham",
)


class ArrivalBlock(BaseModel):
    """One recommended time block, e.g. 08:00-09:00 on a given date."""

    model_config = ConfigDict(extra="forbid")

    date: str  # ISO date, e.g. "2026-07-20"
    start_hour: int = Field(ge=0, le=23)
    end_hour: int = Field(ge=1, le=24)
    reservation_count: int = Field(ge=0, default=0)
    reason: str = ""

    @model_validator(mode="after")
    def _end_after_start(self) -> ArrivalBlock:
        if self.end_hour <= self.start_hour:
            raise ValueError("end_hour must be greater than start_hour")
        return self


class AssistantReply(BaseModel):
    """The validated shape the reasoner must return: intent, a message, and optional time blocks."""

    model_config = ConfigDict(extra="forbid")

    intent: AssistantIntent = "CHAT"
    message: str
    recommendations: list[ArrivalBlock] = Field(default_factory=list)


class ArrivalChatLLM(Protocol):
    """An assistant reasoning client. Returns a raw dict matching `AssistantReply`."""

    def reply(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        """Reason over the (untrusted) `message` and reservation `context`; return a raw dict."""
        ...


class ArrivalChatError(Exception):
    """Raised by an `ArrivalChatLLM` on a provider/transport failure (timeout, outage, rate)."""


def build_context(
    summary: list[DayLoad], *, open_hour: int = OPEN_HOUR, close_hour: int = CLOSE_HOUR
) -> dict[str, Any]:
    """Turn the retrieved reservation summary into the CONTEXT dict the reasoner sees."""
    return {
        "working_hours": {"open_hour": open_hour, "close_hour": close_hour},
        "days": [
            {
                "date": day.day.isoformat(),
                "weekday": day.weekday,
                "hours": [
                    {"hour": hour.hour, "reservations": hour.reservations} for hour in day.hours
                ],
            }
            for day in summary
        ],
    }


def _least_crowded_blocks(context: dict[str, Any], top_n: int = 3) -> list[dict[str, Any]]:
    """The `top_n` least-crowded working hours as 1-hour block dicts (deterministic)."""
    cells = [
        (day["date"], hour["hour"], hour["reservations"])
        for day in context.get("days", [])
        for hour in day["hours"]
    ]
    cells.sort(key=lambda cell: (cell[2], cell[0], cell[1]))  # fewest reservations, then soonest
    return [
        {
            "date": iso_date,
            "start_hour": hour,
            "end_hour": hour + 1,
            "reservation_count": count,
            "reason": f"{count} reservation(s) in this hour",
        }
        for iso_date, hour, count in cells[:top_n]
    ]


def _deterministic_reply(message: str, context: dict[str, Any]) -> dict[str, Any]:
    """Offline/fallback reasoner: classify intent by keyword, then answer accordingly."""
    text = message.lower()
    if not any(marker in text for marker in _SCHEDULE_MARKERS):
        return {
            "intent": "CHAT",
            "message": (
                "I can help you pick a time to come in with the shortest wait, or answer questions "
                "about your visit. What would you like?"
            ),
            "recommendations": [],
        }

    blocks = _least_crowded_blocks(context)
    hours = context.get("working_hours", {})
    if blocks:
        spans = ", ".join(
            f"{b['date']} {b['start_hour']:02d}:00-{b['end_hour']:02d}:00" for b in blocks
        )
        text_out = (
            f"The hospital is open {hours.get('open_hour', OPEN_HOUR):02d}:00-"
            f"{hours.get('close_hour', CLOSE_HOUR):02d}:00. The quietest times are: {spans}."
        )
    else:
        text_out = "There are no working hours to recommend right now."
    return {"intent": "SCHEDULE", "message": text_out, "recommendations": blocks}


class RuleBasedArrivalChatLLM:
    """Deterministic reasoner for the demo/tests and the no-provider fallback (no network)."""

    def reply(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        return _deterministic_reply(message, context)


def respond_to_chat(
    message: str,
    summary: list[DayLoad],
    llm: ArrivalChatLLM,
    *,
    open_hour: int = OPEN_HOUR,
    close_hour: int = CLOSE_HOUR,
) -> AssistantReply:
    """Run the assistant over the reservation `summary`; return a validated `AssistantReply`.

    Runs reason -> validate on PocketFlow (ADR-001): the reasoner is retried, its raw output is
    schema-validated, and on a reasoner error or off-schema output it degrades to the deterministic
    reply instead of raising or trusting unvalidated text.
    """
    context = build_context(summary, open_hour=open_hour, close_hour=close_hour)

    def _on_error() -> AssistantReply:
        return AssistantReply.model_validate(_deterministic_reply(message, context))

    return run_reason_flow(
        llm,
        message,
        context,
        validate=AssistantReply.model_validate,
        on_error=_on_error,
        reason_errors=(ArrivalChatError,),
        validate_errors=(ValidationError,),
    )

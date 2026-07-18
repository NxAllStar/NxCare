"""Arrival-time reasoning: the agent that tells a patient when to come (extends FR-02).

`recommend_arrival_times` runs the retrieve -> reason -> validate flow on PocketFlow behind
agent-core (ADR-001), exactly like the Journey chat: the reservation summary retrieved by
`arrival.summarize_reservations` is the CONTEXT, the patient message is untrusted DATA, and the
reasoner returns a schema-validated `ArrivalRecommendation`. A real LLM answers when a provider is
configured (`arrival_llm_client.build_arrival_chat_llm`); the deterministic reasoner here is only
the offline/failure fallback so the feature degrades instead of erroring (ai-governance.md).

Model output is never trusted: it reaches the caller only through `ArrivalRecommendation`
validation (NFR-SEC-12), and the schema bounds hours so an out-of-range block is rejected.
"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ..core import run_reason_flow
from .arrival import CLOSE_HOUR, OPEN_HOUR, DayLoad


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


class ArrivalRecommendation(BaseModel):
    """The validated shape the reasoner must return: patient-facing text plus structured blocks."""

    model_config = ConfigDict(extra="forbid")

    message: str
    recommendations: list[ArrivalBlock]


class ArrivalChatLLM(Protocol):
    """An arrival-reasoning client. Returns a raw dict matching `ArrivalRecommendation`."""

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


def _deterministic(
    summary: list[DayLoad], *, open_hour: int, close_hour: int, top_n: int = 3
) -> ArrivalRecommendation:
    """Offline/fallback reasoner: pick the `top_n` least-crowded working hours as 1-hour blocks."""
    cells = [
        (day.day.isoformat(), hour.hour, hour.reservations)
        for day in summary
        for hour in day.hours
    ]
    cells.sort(key=lambda cell: (cell[2], cell[0], cell[1]))  # fewest reservations, then soonest
    chosen = cells[:top_n]

    blocks = [
        ArrivalBlock(
            date=iso_date,
            start_hour=hour,
            end_hour=hour + 1,
            reservation_count=count,
            reason=f"{count} reservation(s) in this hour",
        )
        for iso_date, hour, count in chosen
    ]
    if not blocks:
        message = "There are no working hours to recommend right now."
    else:
        spans = ", ".join(f"{b.date} {b.start_hour:02d}:00-{b.end_hour:02d}:00" for b in blocks)
        message = (
            f"The hospital is open {open_hour:02d}:00-{close_hour:02d}:00. The quietest times to "
            f"come are: {spans}."
        )
    return ArrivalRecommendation(message=message, recommendations=blocks)


def recommend_arrival_times(
    message: str,
    summary: list[DayLoad],
    llm: ArrivalChatLLM,
    *,
    open_hour: int = OPEN_HOUR,
    close_hour: int = CLOSE_HOUR,
) -> ArrivalRecommendation:
    """Reason over the reservation `summary` and return a validated `ArrivalRecommendation`.

    Runs reason -> validate on PocketFlow (ADR-001): the reasoner is retried, its raw output is
    schema-validated, and on a reasoner error or off-schema output it degrades to the deterministic
    least-crowded pick instead of raising or trusting unvalidated text.
    """
    context = build_context(summary, open_hour=open_hour, close_hour=close_hour)

    def _on_error() -> ArrivalRecommendation:
        return _deterministic(summary, open_hour=open_hour, close_hour=close_hour)

    return run_reason_flow(
        llm,
        message,
        context,
        validate=ArrivalRecommendation.model_validate,
        on_error=_on_error,
        reason_errors=(ArrivalChatError,),
        validate_errors=(ValidationError,),
    )


class RuleBasedArrivalChatLLM:
    """Deterministic reasoner for the demo/tests and the no-provider fallback (no network).

    Returns the same least-crowded pick as the on-error fallback, shaped as a raw dict so it flows
    through the identical validation path a real client's output would.
    """

    def __init__(self, *, open_hour: int = OPEN_HOUR, close_hour: int = CLOSE_HOUR) -> None:
        self._open_hour = open_hour
        self._close_hour = close_hour

    def reply(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        del message  # the deterministic reasoner ranks by reservation count, not message content
        blocks = [
            {"date": day["date"], "hour": hour["hour"], "reservations": hour["reservations"]}
            for day in context.get("days", [])
            for hour in day["hours"]
        ]
        blocks.sort(key=lambda cell: (cell["reservations"], cell["date"], cell["hour"]))
        chosen = blocks[:3]
        recommendations = [
            {
                "date": cell["date"],
                "start_hour": cell["hour"],
                "end_hour": cell["hour"] + 1,
                "reservation_count": cell["reservations"],
                "reason": f"{cell['reservations']} reservation(s) in this hour",
            }
            for cell in chosen
        ]
        if recommendations:
            spans = ", ".join(
                f"{c['date']} {c['start_hour']:02d}:00-{c['end_hour']:02d}:00"
                for c in recommendations
            )
            text = (
                f"The hospital is open {self._open_hour:02d}:00-{self._close_hour:02d}:00. "
                f"The quietest times to come are: {spans}."
            )
        else:
            text = "There are no working hours to recommend right now."
        return {"message": text, "recommendations": recommendations}

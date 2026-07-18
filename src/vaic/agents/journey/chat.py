"""Patient chat handling for the Journey Agent (FR-06).

Patient chat is untrusted DATA, never an instruction (.claude/rules/agent-guardrails.md; NFR-SEC-11;
LLM01, Agentic Top 10 #1). Two structural guarantees make an embedded command harmless:

1. The reasoner returns a schema-validated `ChatReply` whose only channels back into the system are
   a bounded `intent` enum and an optional `requested_task_code` string - there is NO field that
   can carry a state-mutating command. Free model text lands only in `answer`, shown to the patient.
2. The agent maps an intent only to a dependency-legal reorder (resequence.py). There is no code
   path from chat to `execution_status`, so "mark all my tasks DONE" cannot change any task's state
   (FR-06 AC-06.3), whatever the model returns.

`RuleBasedJourneyChatLLM` is a deterministic reasoner used by the demo and tests; production swaps a
real Qwen client behind the same `JourneyChatLLM` protocol (tech-stack.md), and the caller
schema-validates its output all the same - the client is never trusted.
"""

from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, ValidationError

from ..core import run_reason_flow

ChatIntent = Literal["ASK_FASTING", "ASK_REORDER", "INFO", "REFUSE"]


class ChatReply(BaseModel):
    """The schema-validated shape of the reasoner's output (NFR-SEC-12).

    Deliberately narrow: `answer` is patient-facing text and `intent` is a closed set - there is no
    field through which chat content can request a privileged, state-changing, or task-targeting
    action. `extra="forbid"` rejects any unexpected key the model returns.
    """

    model_config = ConfigDict(extra="forbid")

    answer: str
    intent: ChatIntent = "INFO"


class JourneyChatLLM(Protocol):
    """A journey-chat reasoning client.

    Receives the patient message as DATA plus a small context dict; returns a raw dict matching
    `ChatReply`. The caller validates it - the client is never trusted, and any instruction inside
    the message is treated as data, not obeyed.
    """

    def reply(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        """Reason over the (untrusted) `message` and return a `{answer, intent, ...}` dict."""
        ...


class ChatReasonerError(Exception):
    """Raised by a `JourneyChatLLM` when it cannot produce a reply (timeout, outage, rate limit)."""


# Command-like tokens that signal an attempt to steer the agent rather than ask a question. They do
# not grant anything - the structural guarantees above already prevent execution - but recognising
# them lets the agent answer with a neutral refusal instead of a confused reorder (AC-06.3).
_INJECTION_MARKERS = (
    "mark ",
    "set status",
    "set all",
    "done",
    "ignore previous",
    "ignore all",
    "delete",
    "drop ",
    "system:",
    "you are",
)
_FASTING_MARKERS = ("eat", "breakfast", "food", "drink", "ăn", "uống", "nhịn")
_REORDER_MARKERS = ("swap", "reorder", "first", "sooner", "earlier", "trước", "đổi")


class RuleBasedJourneyChatLLM:
    """Deterministic journey-chat reasoner for the demo and tests (no network, no randomness).

    It never executes embedded instructions - it classifies the message into a bounded intent and
    returns patient-facing text. A message that reads like a command is classified `REFUSE`.
    """

    def reply(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        text = message.lower()
        if any(marker in text for marker in _INJECTION_MARKERS):
            return {
                "answer": "I can help with questions about your visit, but I cannot change task "
                "statuses from chat. A step advances only when the room owner scans your code.",
                "intent": "REFUSE",
            }
        if any(marker in text for marker in _FASTING_MARKERS):
            if not context.get("has_fasting_step"):
                # No fasting task on this plan: a fasting-refusal here would be false clinical
                # guidance. Answer neutrally instead (no bring-forward, no restriction claimed).
                return {
                    "answer": "There is no fasting restriction on your plan right now, so you may "
                    "eat and drink as usual. I will let you know if that changes.",
                    "intent": "INFO",
                }
            return {
                "answer": "You still have a fasting test scheduled, so please do not eat or drink "
                "yet. I will bring that test as early as possible so you can eat sooner.",
                "intent": "ASK_FASTING",
            }
        if any(marker in text for marker in _REORDER_MARKERS):
            return {
                "answer": "I will try to reorder your remaining steps to shorten the wait, as long "
                "as the required order allows it.",
                "intent": "ASK_REORDER",
            }
        return {
            "answer": "Thanks for the message. I will keep you posted on your next step and its "
            "estimated wait.",
            "intent": "INFO",
        }


def _neutral_reply() -> ChatReply:
    """The neutral fallback used when reasoning fails or its output cannot be validated."""
    return ChatReply(answer="I could not process that just now; your plan is unchanged.")


def interpret_chat(message: str, context: dict[str, Any], llm: JourneyChatLLM) -> ChatReply:
    """Run the reasoner over an untrusted `message` and return a validated `ChatReply`.

    Runs the retrieve -> reason -> validate flow on PocketFlow behind agent-core (ADR-001): the
    reasoner call is retried, its raw output is schema-validated to `ChatReply` (NFR-SEC-12), and on
    a reasoner error or malformed output it degrades to a neutral reply rather than raising or
    trusting unvalidated text (FR-06 "on failure, hold current order and send a neutral notice").
    """
    return run_reason_flow(
        llm,
        message,
        context,
        validate=ChatReply.model_validate,
        on_error=_neutral_reply,
        # Degrade only on a declared reasoner failure or off-schema output; a programming error
        # (e.g. a bad kwarg or a typo in a client) propagates instead of masquerading as an outage.
        reason_errors=(ChatReasonerError,),
        validate_errors=(ValidationError,),
    )

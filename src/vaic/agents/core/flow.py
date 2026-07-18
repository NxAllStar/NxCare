"""The agentic reasoning flow, built on PocketFlow (ADR-001), isolated behind agent-core.

This is the first concrete use of PocketFlow in the codebase. Per ADR-001 the framework must not
leak past `agent-core`: every agent and tool stays plain, framework-agnostic Python and calls
`run_reason_flow`, passing only callables and data. Swapping the framework (the ADR-001 reversal to
LangGraph) is therefore a change to this file, not to any agent.

The flow expresses the retrieve -> reason -> validate shape shared by the product's model calls
(the same shape the forecast tool hand-rolls in `forecast/tool.py`):

    reason (LLM, retried)  --ok-->    validate (schema)  --> result
                           --error--> neutral fallback   --> result

Reason and validate each fall back to a caller-supplied neutral result instead of raising, so a
provider outage or malformed output is a handled outcome, not an exception (ai-governance.md
"Validation failure is a handled outcome"). Model output is never trusted: it reaches `result` only
through the caller's `validate` (NFR-SEC-12).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pocketflow import Flow, Node

# Sentinel placed on the shared store when the reason or validate step fails, so the flow routes to
# the neutral fallback instead of carrying an untrusted or absent value forward.
_FAILED = object()


class _ReasonNode(Node):
    """Call the (untrusted) model client. PocketFlow retries `exec` up to `max_retries` times."""

    def prep(self, shared: dict[str, Any]) -> dict[str, Any]:
        return shared

    def exec(self, prep_res: dict[str, Any]) -> Any:
        return prep_res["llm"].reply(prep_res["message"], prep_res["context"])

    def exec_fallback(self, prep_res: dict[str, Any], exc: Exception) -> Any:
        # Degrade only on the caller's declared provider-failure family (timeout, outage, rate
        # limit, bad response). Any other exception is an unexpected code defect, not flaky I/O:
        # let it propagate rather than mask it as a provider outage (code-quality.md "Swallowed
        # errors" - a masked bug ships looking like transient flakiness).
        if isinstance(exc, prep_res["reason_errors"]):
            return _FAILED
        raise exc

    def post(self, shared: dict[str, Any], prep_res: dict[str, Any], exec_res: Any) -> str:
        shared["raw"] = exec_res
        return "error" if exec_res is _FAILED else "ok"


class _ValidateNode(Node):
    """Schema-validate the raw model output (NFR-SEC-12). Validation failure -> neutral result."""

    def prep(self, shared: dict[str, Any]) -> dict[str, Any]:
        return shared

    def exec(self, prep_res: dict[str, Any]) -> Any:
        return prep_res["validate"](prep_res["raw"])

    def exec_fallback(self, prep_res: dict[str, Any], exc: Exception) -> Any:
        # Same discipline as the reason node: a genuine validation failure (the model returned
        # off-schema output) degrades; any other exception is a defect and propagates.
        if isinstance(exc, prep_res["validate_errors"]):
            return _FAILED
        raise exc

    def post(self, shared: dict[str, Any], prep_res: dict[str, Any], exec_res: Any) -> str:
        shared["result"] = prep_res["on_error"]() if exec_res is _FAILED else exec_res
        return "default"


class _FallbackNode(Node):
    """Produce the caller's neutral result when reasoning could not yield validated output."""

    def prep(self, shared: dict[str, Any]) -> dict[str, Any]:
        return shared

    def post(self, shared: dict[str, Any], prep_res: dict[str, Any], exec_res: Any) -> str:
        shared["result"] = prep_res["on_error"]()
        return "default"


def run_reason_flow(
    llm: Any,
    message: str,
    context: dict[str, Any],
    validate: Callable[[Any], Any],
    on_error: Callable[[], Any],
    *,
    reason_errors: tuple[type[BaseException], ...] = (Exception,),
    validate_errors: tuple[type[BaseException], ...] = (Exception,),
    max_retries: int = 2,
    wait: float = 0,
) -> Any:
    """Run reason -> validate as a PocketFlow flow; return the validated result (or `on_error()`).

    - `llm.reply(message, context)` produces raw model output; it is attempted `max_retries` times
      (PocketFlow counts total attempts, so `max_retries=2` is one initial try plus one retry).
    - `validate(raw)` turns the raw output into the caller's validated type; on failure the flow
      returns `on_error()`.
    - `message` is passed through as untrusted DATA - the client, not this flow, builds the prompt,
      and the client is responsible for keeping instruction and data in separate regions.
    - `reason_errors` / `validate_errors` declare which exception types are treated as expected
      provider/validation failures (and so degrade to `on_error()`); anything else propagates so a
      code defect is not silently masked as a provider outage. Callers should pass a narrow family
      (e.g. the client's own error type and known transport errors) rather than the default.
    """
    reason = _ReasonNode(max_retries=max_retries, wait=wait)
    validate_node = _ValidateNode()
    fallback = _FallbackNode()

    reason - "ok" >> validate_node
    reason - "error" >> fallback

    shared: dict[str, Any] = {
        "llm": llm,
        "message": message,
        "context": context,
        "validate": validate,
        "on_error": on_error,
        "reason_errors": reason_errors,
        "validate_errors": validate_errors,
    }
    Flow(start=reason).run(shared)
    return shared["result"]

"""Reason phase of the FR-07 grounding contract.

`ForecastLLM` is a narrow client Protocol so production can wire a real provider later and every
test injects a fake instead - no real network call ever happens from this package or its tests
(.claude/rules/testing.md "mock every external provider", model-policy.md).
"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class ForecastLLMError(Exception):
    """Raised by a `ForecastLLM` implementation when it cannot produce an estimate.

    Covers timeout, rate limit, and provider outage. The tool treats this the same as any other
    validation failure: fall back to the deterministic baseline, flagged LOW_CONFIDENCE
    (NFR-REL-04, AC-07.2).
    """


class LLMEstimate(BaseModel):
    """The schema-validated shape of the LLM's reasoning output (grounding contract step 2).

    Schema-validated before use, never trusted as-is (NFR-SEC-12). `cited_features` must name
    only features that were actually retrieved - enforced downstream by the provenance check in
    `validate.py`, not by this schema (the schema cannot know what was retrieved).
    """

    model_config = ConfigDict(extra="forbid")

    value: float
    confidence: float = Field(ge=0.0, le=1.0)
    cited_features: list[str]


class ForecastLLM(Protocol):
    """A forecast-reasoning client.

    Receives ONLY the retrieved, observed features (`RetrievedFeatures.as_prompt_dict()`) and
    must return a raw dict matching `LLMEstimate` - the caller schema-validates it, never the
    client. The LLM must not introduce facts beyond what it was given.
    """

    def estimate_wait(self, features: dict[str, Any]) -> dict[str, Any]:
        """Reason over `features` and return `{value, confidence, cited_features}`."""
        ...

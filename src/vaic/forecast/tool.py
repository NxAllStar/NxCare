"""The forecast tool: `estimate_wait`, the FR-07 tool-interface entry point.

Runs the three-phase grounding contract - retrieve (code), reason (LLM), validate (code) - and
returns `{value, confidence, provenance, source}` where `source` is `"LLM"` or `"BASELINE"`.
Deterministic given a fixed seed (BR-15): the tool itself has no randomness, and the only
non-deterministic piece (the LLM call) is behind the `ForecastLLM` protocol, mocked in every test.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, ValidationError

from ..state import Repository
from .features import RetrievedFeatures, retrieve_features
from .llm import ForecastLLM, ForecastLLMError, LLMEstimate
from .validate import baseline_estimate, validate

# Fixed seed recorded here so a real provider client (wired later) can be configured to run
# deterministically for demo reproducibility (BR-15, NFR-REL-05). Unused by the fake/test clients.
FORECAST_SEED = 42

# Confidence attached to every baseline result - deliberately low, alongside the literal
# "LOW_CONFIDENCE" flag in `provenance`, so a consumer cannot mistake a fallback for a reasoned
# estimate (NFR-REL-04).
BASELINE_CONFIDENCE = 0.2

Source = Literal["LLM", "BASELINE"]


class ForecastResult(BaseModel):
    """The tool-interface return shape (FR-07): every consumer sees this, never a raw number."""

    model_config = ConfigDict(extra="forbid")

    value: float
    confidence: float
    provenance: str
    source: Source


def _baseline_result(features: RetrievedFeatures, reason: str) -> ForecastResult:
    value = baseline_estimate(features)
    return ForecastResult(
        value=value,
        confidence=BASELINE_CONFIDENCE,
        provenance=(
            f"LOW_CONFIDENCE baseline: queue_length({features.queue_length}) x "
            f"median_service_time({features.median_service_time}) - rejected LLM value: {reason}"
        ),
        source="BASELINE",
    )


def estimate_wait(repo: Repository, owner_id: UUID, hour: int, llm: ForecastLLM) -> ForecastResult:
    """Return the ETA in minutes for `owner_id`'s queue at `hour` (FR-07 AC-07.1).

    1. Retrieve (code) - `retrieve_features` pulls queue state, historical service times, and
       resource availability. These are data, never model output.
    2. Reason (LLM) - `llm.estimate_wait` receives ONLY the retrieved features and returns a raw
       `{value, confidence, cited_features}`.
    3. Validate (code) - schema-validate the raw output (NFR-SEC-12), then run the range,
       monotonic-sanity, and provenance checks. Any failure - including the LLM being unavailable
       at all - rejects the LLM value and falls back to the deterministic baseline
       (`queue_length x median_service_time`), flagged LOW_CONFIDENCE.
    """
    features = retrieve_features(repo, owner_id, hour)

    try:
        raw = llm.estimate_wait(features.as_prompt_dict())
    except ForecastLLMError as exc:
        return _baseline_result(features, f"LLM unavailable: {exc}")

    try:
        estimate = LLMEstimate.model_validate(raw)
    except ValidationError as exc:
        return _baseline_result(features, f"malformed LLM output: {exc.error_count()} error(s)")

    failure = validate(estimate, features)
    if failure is not None:
        return _baseline_result(features, failure)

    return ForecastResult(
        value=estimate.value,
        confidence=estimate.confidence,
        provenance=f"LLM grounded in cited_features={estimate.cited_features}",
        source="LLM",
    )

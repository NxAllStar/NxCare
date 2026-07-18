"""Validate phase of the FR-07 grounding contract - deterministic code, never an LLM call.

Enforces, in the order the spec lists them: (a) range check, (b) monotonic sanity check, (c)
provenance check. Any violation rejects the LLM value; the tool then falls back to the
deterministic baseline (BR-14, BR-15, NFR-SEC-20).
"""

from __future__ import annotations

from .features import RetrievedFeatures
from .llm import LLMEstimate

# Range-check upper bound multiplier - the spec's "he so an toan" (safety factor) applied to the
# queue-derived band, so a plausible-but-uncertain LLM value is not rejected purely for being a
# little higher than the naive baseline.
SAFETY_FACTOR = 1.5

# Monotonic-sanity floor multiplier: with a non-empty queue, the ETA must be at least this
# fraction of `queue_length * median_service_time` - a longer queue must not yield a lower ETA.
MIN_QUEUE_FACTOR = 0.3


def baseline_estimate(features: RetrievedFeatures) -> float:
    """`queue_length x median_service_time` (BR-14) - the deterministic fallback value."""
    return round(features.queue_length * features.median_service_time, 2)


def range_check(value: float, features: RetrievedFeatures) -> str | None:
    """Value must fall within the band derived from retrieved data: `[0, band_upper]`."""
    band_upper = max(features.queue_length, 1) * features.median_service_time * SAFETY_FACTOR
    if value < 0 or value > band_upper:
        return f"range check failed: value {value} outside [0, {band_upper}]"
    return None


def monotonic_sanity_check(value: float, features: RetrievedFeatures) -> str | None:
    """A longer queue must not yield a lower ETA than that queue length implies."""
    if features.queue_length == 0:
        return None  # no floor to apply when nothing is queued
    floor = features.queue_length * features.median_service_time * MIN_QUEUE_FACTOR
    if value < floor:
        return (
            f"monotonic sanity check failed: value {value} below floor {floor} "
            f"for queue_length={features.queue_length}"
        )
    return None


def provenance_check(estimate: LLMEstimate, features: RetrievedFeatures) -> str | None:
    """Every `cited_features` entry must exist in the retrieved set; at least one is required."""
    if not estimate.cited_features:
        return "provenance check failed: no cited_features given"
    allowed = set(features.as_prompt_dict())
    unknown = [f for f in estimate.cited_features if f not in allowed]
    if unknown:
        return f"provenance check failed: cited feature(s) not retrieved: {unknown}"
    return None


def validate(estimate: LLMEstimate, features: RetrievedFeatures) -> str | None:
    """Run the three checks in the grounding-contract order; return the first failure reason.

    Returns None when `estimate` passes every check, meaning it is safe to use as-is.
    """
    return (
        range_check(estimate.value, features)
        or monotonic_sanity_check(estimate.value, features)
        or provenance_check(estimate, features)
    )

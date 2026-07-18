"""Forecast tool (FR-07): an LLM-with-reasoning exposed as a tool, per OI-20 - not trained ML.

Enforces the retrieve-reason-validate grounding contract: every forecast number is grounded in
observed data and range-validated before use (BR-14, BR-15, NFR-SEC-20). See the "Grounding
contract" in docs/specs/05-functional-requirements.md#fr-07.
"""

from __future__ import annotations

from .features import DEFAULT_MEDIAN_SERVICE_MINUTES, RetrievedFeatures, retrieve_features
from .llm import ForecastLLM, ForecastLLMError, LLMEstimate
from .tool import BASELINE_CONFIDENCE, FORECAST_SEED, ForecastResult, estimate_wait
from .validate import baseline_estimate, validate

__all__ = [
    "DEFAULT_MEDIAN_SERVICE_MINUTES",
    "RetrievedFeatures",
    "retrieve_features",
    "ForecastLLM",
    "ForecastLLMError",
    "LLMEstimate",
    "BASELINE_CONFIDENCE",
    "FORECAST_SEED",
    "ForecastResult",
    "estimate_wait",
    "baseline_estimate",
    "validate",
]

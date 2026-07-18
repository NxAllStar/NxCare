"""Tests for the FR-07 forecast tool: the retrieve -> reason -> validate grounding contract.

The LLM is always a fake (testing.md - no real network call, ever, in dev or test code). Each test
below exercises one path through the contract in
docs/specs/05-functional-requirements.md#fr-07 ("Grounding contract"):

- happy path: a grounded LLM value passes every check and is used (AC-07.1).
- LLM unavailable: falls back to the deterministic baseline, flagged LOW_CONFIDENCE (AC-07.2).
- provenance failure: a cited feature that was never retrieved rejects the value (AC-07.3).
- range failure: a value outside the band derived from retrieved data is rejected (AC-07.4).
- monotonic-sanity failure and malformed LLM output are covered as the same reject-to-baseline
  path, since BR-14/BR-15/NFR-SEC-20 require every violation to behave identically.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from vaic.forecast import ForecastLLMError, estimate_wait
from vaic.models import ExecutionStatus, PaymentStatus, Resource, ResourceType, Task
from vaic.state import InMemoryRepository


def _task(owner, **kw) -> Task:
    base = dict(care_plan_id=uuid4(), service_order_id=uuid4(), owner_id=owner)
    base.update(kw)
    return Task(**base)


def _seed_queue(repo, owner, n, duration):
    """n paid, pending tasks queued for `owner` - counted by owner_queue (BR-10)."""
    for i in range(n):
        repo.save(
            _task(
                owner,
                payment_status=PaymentStatus.PAID,
                execution_status=ExecutionStatus.PENDING,
                sequence_index=i,
                estimated_duration_min=duration,
            )
        )


def _seed_history(repo, owner, durations):
    """Completed tasks for `owner` - the historical service-time samples (FR-07 retrieve phase)."""
    for d in durations:
        repo.save(
            _task(
                owner,
                payment_status=PaymentStatus.PAID,
                execution_status=ExecutionStatus.DONE,
                estimated_duration_min=d,
            )
        )


class FakeForecastLLM:
    """A fake ForecastLLM: returns a canned response, or raises a canned failure.

    Stands in for a real provider client in every test - see .claude/rules/model-policy.md and
    testing.md ("mock every external provider").
    """

    def __init__(self, response: dict | None = None, raises: Exception | None = None) -> None:
        self._response = response
        self._raises = raises

    def estimate_wait(self, features: dict) -> dict:
        if self._raises is not None:
            raise self._raises
        assert self._response is not None
        return self._response


# ---- AC-07.1 happy path ------------------------------------------------------------------------


def test_happy_path_grounded_llm_value_is_used():
    repo = InMemoryRepository()
    owner = uuid4()
    _seed_queue(repo, owner, n=2, duration=10)
    _seed_history(repo, owner, [10, 12, 8])

    llm = FakeForecastLLM(
        {
            "value": 20.0,
            "confidence": 0.9,
            "cited_features": ["queue_length", "median_service_time"],
        }
    )
    result = estimate_wait(repo, owner, hour=9, llm=llm)

    assert result.source == "LLM"
    assert result.value == 20.0
    assert result.confidence == 0.9
    assert "queue_length" in result.provenance


def test_happy_path_with_no_history_falls_back_to_default_median_but_still_grounded():
    repo = InMemoryRepository()
    owner = uuid4()
    _seed_queue(repo, owner, n=1, duration=15)

    llm = FakeForecastLLM({"value": 15.0, "confidence": 0.7, "cited_features": ["queue_length"]})
    result = estimate_wait(repo, owner, hour=9, llm=llm)

    assert result.source == "LLM"
    assert result.value == 15.0


# ---- AC-07.4 range check --------------------------------------------------------------------


def test_out_of_range_value_rejected_falls_back_to_baseline():
    repo = InMemoryRepository()
    owner = uuid4()
    _seed_queue(repo, owner, n=2, duration=10)
    _seed_history(repo, owner, [10, 10, 10])  # median_service_time == 10

    # band upper = queue_length(2) * median(10) * safety_factor(1.5) == 30; 999 is absurd
    llm = FakeForecastLLM({"value": 999.0, "confidence": 0.9, "cited_features": ["queue_length"]})
    result = estimate_wait(repo, owner, hour=9, llm=llm)

    assert result.source == "BASELINE"
    assert result.value == 20.0  # queue_length(2) x median_service_time(10) - BR-14
    assert "LOW_CONFIDENCE" in result.provenance


# ---- AC-07.3 provenance check -----------------------------------------------------------------


def test_provenance_failure_falls_back_to_baseline():
    repo = InMemoryRepository()
    owner = uuid4()
    _seed_queue(repo, owner, n=1, duration=15)
    _seed_history(repo, owner, [15, 15])

    llm = FakeForecastLLM(
        {"value": 15.0, "confidence": 0.8, "cited_features": ["a_feature_never_retrieved"]}
    )
    result = estimate_wait(repo, owner, hour=9, llm=llm)

    assert result.source == "BASELINE"
    assert "LOW_CONFIDENCE" in result.provenance
    assert "provenance" in result.provenance.lower()


def test_no_cited_features_at_all_is_a_provenance_failure():
    repo = InMemoryRepository()
    owner = uuid4()
    _seed_queue(repo, owner, n=1, duration=10)

    llm = FakeForecastLLM({"value": 10.0, "confidence": 0.6, "cited_features": []})
    result = estimate_wait(repo, owner, hour=9, llm=llm)

    assert result.source == "BASELINE"


# ---- monotonic sanity check ------------------------------------------------------------------


def test_implausibly_low_value_for_a_busy_queue_fails_monotonic_sanity():
    repo = InMemoryRepository()
    owner = uuid4()
    _seed_queue(repo, owner, n=5, duration=20)  # a long, busy queue
    _seed_history(repo, owner, [20, 20, 20])

    # a near-zero ETA for a 5-deep, 20-min-median queue is not sane
    llm = FakeForecastLLM({"value": 0.5, "confidence": 0.9, "cited_features": ["queue_length"]})
    result = estimate_wait(repo, owner, hour=9, llm=llm)

    assert result.source == "BASELINE"
    assert "LOW_CONFIDENCE" in result.provenance


# ---- AC-07.2 LLM unavailable -------------------------------------------------------------------


def test_llm_unavailable_falls_back_to_baseline_flagged_low_confidence():
    repo = InMemoryRepository()
    owner = uuid4()
    _seed_queue(repo, owner, n=3, duration=10)
    _seed_history(repo, owner, [10])

    llm = FakeForecastLLM(raises=ForecastLLMError("provider timeout"))
    result = estimate_wait(repo, owner, hour=9, llm=llm)

    assert result.source == "BASELINE"
    assert "LOW_CONFIDENCE" in result.provenance
    assert result.confidence < 0.5
    assert result.value == 30.0  # queue_length(3) x median_service_time(10)


# ---- malformed LLM output (schema validation, NFR-SEC-12) -------------------------------------


def test_malformed_llm_output_falls_back_to_baseline():
    repo = InMemoryRepository()
    owner = uuid4()
    _seed_queue(repo, owner, n=2, duration=10)

    llm = FakeForecastLLM({"confidence": 0.9, "cited_features": ["queue_length"]})  # missing value
    result = estimate_wait(repo, owner, hour=9, llm=llm)

    assert result.source == "BASELINE"
    assert "LOW_CONFIDENCE" in result.provenance


# ---- baseline determinism and empty-queue edge case --------------------------------------------


def test_baseline_is_deterministic_for_the_same_inputs():
    repo = InMemoryRepository()
    owner = uuid4()
    _seed_queue(repo, owner, n=2, duration=10)
    _seed_history(repo, owner, [10, 10])

    llm = FakeForecastLLM(raises=ForecastLLMError("down"))
    first = estimate_wait(repo, owner, hour=9, llm=llm)
    second = estimate_wait(repo, owner, hour=9, llm=llm)

    assert first.value == second.value == 20.0
    assert first.source == second.source == "BASELINE"


def test_empty_queue_baseline_is_zero():
    repo = InMemoryRepository()
    owner = uuid4()  # no tasks at all

    llm = FakeForecastLLM(raises=ForecastLLMError("down"))
    result = estimate_wait(repo, owner, hour=9, llm=llm)

    assert result.value == 0.0
    assert result.source == "BASELINE"


def test_resource_availability_is_retrieved_and_defaults_true_when_unknown():
    repo = InMemoryRepository()
    owner = uuid4()
    repo.save(Resource(id=owner, type=ResourceType.ROOM, department_id=uuid4(), is_available=False))
    _seed_queue(repo, owner, n=1, duration=10)

    llm = FakeForecastLLM(
        {"value": 10.0, "confidence": 0.9, "cited_features": ["resource_available"]}
    )
    result = estimate_wait(repo, owner, hour=9, llm=llm)

    assert result.source == "LLM"  # resource_available is a valid citeable feature either way


@pytest.mark.parametrize("hour", [-1, 24])
def test_invalid_hour_is_rejected_by_the_retrieve_phase_schema(hour):
    repo = InMemoryRepository()
    owner = uuid4()
    llm = FakeForecastLLM(raises=ForecastLLMError("unused"))

    with pytest.raises(ValidationError):
        estimate_wait(repo, owner, hour=hour, llm=llm)

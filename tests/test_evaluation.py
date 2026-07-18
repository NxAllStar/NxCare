"""A/B evaluation summary (TASK-012): the headline improvement of a policy over the FIFO baseline.

Covers: the comparison math against hand-built metrics, a deterministic congested cohort where the
load-aware (agent-style least-crowded) policy measurably beats FIFO, and safe handling of a
zero-wait baseline.
"""

from __future__ import annotations

from vaic.simulator.areas import AreaConfig
from vaic.simulator.evaluation import (
    AbComparison,
    compare_metrics,
    evaluate_ab,
    evaluate_ab_multi,
    headline,
    headline_aggregate,
)
from vaic.simulator.metrics import Metrics

CONGESTED_AREA = (
    AreaConfig(name="busy", num_rooms=2, weight=1.0, min_service_min=5.0, max_service_min=30.0),
)
# Moderate load over several high-variance rooms: the regime where join-shortest-queue routing
# robustly helps on average. A single seed is noisy, so the aggregate is taken over many seeds.
ROBUST_AREA = (
    AreaConfig(name="busy", num_rooms=4, weight=1.0, min_service_min=5.0, max_service_min=45.0),
)


def _metrics(avg_wait, peak, mae=0.0):
    return Metrics(
        patient_count=10,
        average_wait_min=avg_wait,
        peak_load_per_area={"busy": peak},
        room_utilisation_per_area={"busy": 0.5},
        equipment_utilisation_per_area={},
        eta_mae_min=mae,
    )


def test_compare_math_matches_hand_computed_values():
    baseline = _metrics(avg_wait=20.0, peak=10, mae=8.0)
    candidate = _metrics(avg_wait=15.0, peak=8, mae=6.0)

    result = compare_metrics(baseline, candidate)

    assert result.wait_reduction_min == 5.0
    assert result.wait_reduction_pct == 25.0  # 5 / 20
    assert result.peak_reduction_pct == 20.0  # (10 - 8) / 10
    assert result.eta_mae_delta_min == -2.0  # candidate lower is better (negative delta)


def test_zero_baseline_wait_is_safe():
    result = compare_metrics(_metrics(avg_wait=0.0, peak=0), _metrics(avg_wait=0.0, peak=0))
    assert result.wait_reduction_pct == 0.0
    assert result.peak_reduction_pct == 0.0


def test_evaluate_ab_shows_a_real_wait_reduction_on_a_congested_cohort():
    result = evaluate_ab(seed=100, num_patients=40, area_configs=CONGESTED_AREA)

    assert isinstance(result, AbComparison)
    assert result.baseline_name == "fifo" and result.candidate_name == "load_aware"
    # the agent-style policy genuinely cuts the average wait vs the FIFO baseline (G-01)
    assert result.candidate.average_wait_min < result.baseline.average_wait_min
    assert result.wait_reduction_min > 0 and result.wait_reduction_pct > 0


def test_evaluate_ab_is_deterministic_by_seed():
    a = evaluate_ab(seed=100, num_patients=40, area_configs=CONGESTED_AREA)
    b = evaluate_ab(seed=100, num_patients=40, area_configs=CONGESTED_AREA)
    assert a.wait_reduction_min == b.wait_reduction_min
    assert a.wait_reduction_pct == b.wait_reduction_pct


def test_headline_is_human_readable_and_names_the_delta():
    result = evaluate_ab(seed=100, num_patients=40, area_configs=CONGESTED_AREA)
    text = headline(result)
    assert "fifo" in text and "load_aware" in text
    assert "%" in text  # the improvement percentage is surfaced for the demo


def test_multi_seed_aggregate_shows_a_robust_mean_improvement():
    aggregate = evaluate_ab_multi(
        seeds=range(200, 230), num_patients=40, area_configs=ROBUST_AREA
    )
    assert aggregate.seeds == 30
    # replicated over 30 cohorts, the smart policy lowers the mean wait and wins on balance
    assert aggregate.candidate_mean_wait_min < aggregate.baseline_mean_wait_min
    assert aggregate.mean_wait_reduction_pct > 0
    assert aggregate.seeds_favouring_candidate > aggregate.seeds / 2
    assert aggregate.min_wait_reduction_pct <= aggregate.max_wait_reduction_pct


def test_multi_seed_aggregate_is_deterministic():
    a = evaluate_ab_multi(seeds=range(200, 210), num_patients=40, area_configs=ROBUST_AREA)
    b = evaluate_ab_multi(seeds=range(200, 210), num_patients=40, area_configs=ROBUST_AREA)
    assert a.mean_wait_reduction_pct == b.mean_wait_reduction_pct


def test_multi_seed_headline_reports_the_spread_and_win_rate():
    aggregate = evaluate_ab_multi(
        seeds=range(200, 230), num_patients=40, area_configs=ROBUST_AREA
    )
    text = headline_aggregate(aggregate)
    assert "30 seeded cohorts" in text
    assert "/30 runs" in text  # honest about how many seeds favoured the smart policy


def test_multi_seed_requires_at_least_one_seed():
    import pytest

    with pytest.raises(ValueError):
        evaluate_ab_multi(seeds=[], num_patients=40, area_configs=ROBUST_AREA)

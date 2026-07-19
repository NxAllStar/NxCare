"""A/B evaluation summary (TASK-012): turn two policies' metrics into a headline improvement.

The harness (`harness.run_ab`) already runs the FIFO baseline and the load-aware policy on the same
seeded cohort. This module adds the one thing a demo and a business case need on top: the delta -
how much less patients wait, and how much the peak congestion drops, under the smarter policy versus
the current-process FIFO baseline (docs/specs/01-overview.md success metrics).

The load-aware policy is join-shortest-queue - the same least-crowded-first routing the Coordinator
applies in the running system (FR-02 / FR-10), so this A/B is an honest stand-in for "agent vs
today's manual queueing" until the live agent policy is plugged behind the same interface.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from statistics import mean

from .areas import DEFAULT_AREAS, AreaConfig
from .disruptions import DisruptionSpec
from .harness import run_ab
from .metrics import Metrics


@dataclass(frozen=True)
class AbComparison:
    """The baseline and candidate metrics plus the derived improvement (candidate over baseline)."""

    baseline_name: str
    candidate_name: str
    baseline: Metrics
    candidate: Metrics
    wait_reduction_min: float  # baseline avg wait minus candidate avg wait (positive = better)
    wait_reduction_pct: float  # the same as a percentage of the baseline wait
    peak_reduction_pct: float  # drop in the worst per-area peak load, as a percentage
    eta_mae_delta_min: float  # candidate MAE minus baseline MAE (negative = better forecast)


def _pct(reduction: float, baseline: float) -> float:
    """`reduction` as a percentage of `baseline`; 0.0 when the baseline is 0 (no divide-by-zero)."""
    return (reduction / baseline * 100.0) if baseline > 0 else 0.0


def compare_metrics(
    baseline: Metrics,
    candidate: Metrics,
    *,
    baseline_name: str = "fifo",
    candidate_name: str = "load_aware",
) -> AbComparison:
    """Derive the headline improvement of `candidate` over `baseline`."""
    wait_reduction = baseline.average_wait_min - candidate.average_wait_min
    baseline_peak = max(baseline.peak_load_per_area.values(), default=0)
    candidate_peak = max(candidate.peak_load_per_area.values(), default=0)
    return AbComparison(
        baseline_name=baseline_name,
        candidate_name=candidate_name,
        baseline=baseline,
        candidate=candidate,
        wait_reduction_min=wait_reduction,
        wait_reduction_pct=_pct(wait_reduction, baseline.average_wait_min),
        peak_reduction_pct=_pct(baseline_peak - candidate_peak, baseline_peak),
        eta_mae_delta_min=candidate.eta_mae_min - baseline.eta_mae_min,
    )


def evaluate_ab(
    seed: int,
    num_patients: int,
    area_configs: Sequence[AreaConfig] = DEFAULT_AREAS,
    disruptions: Sequence[DisruptionSpec] = (),
) -> AbComparison:
    """Run the FIFO-vs-load-aware A/B on one seeded cohort and summarise the improvement."""
    results = run_ab(seed, num_patients, area_configs, disruptions)
    return compare_metrics(results["fifo"], results["load_aware"])


@dataclass(frozen=True)
class AbAggregate:
    """The A/B improvement averaged over many seeded cohorts (replication, not a single lucky run).

    A single seed is noisy - one cohort can favour either policy. The mean over many seeds, plus how
    many seeds favoured the candidate, is the honest number a business case should quote.
    """

    seeds: int
    num_patients: int
    baseline_mean_wait_min: float
    candidate_mean_wait_min: float
    mean_wait_reduction_pct: float
    min_wait_reduction_pct: float
    max_wait_reduction_pct: float
    seeds_favouring_candidate: int


def evaluate_ab_multi(
    seeds: Iterable[int],
    num_patients: int,
    area_configs: Sequence[AreaConfig] = DEFAULT_AREAS,
    disruptions: Sequence[DisruptionSpec] = (),
) -> AbAggregate:
    """Run the A/B over every seed and aggregate the wait-reduction across the runs."""
    comparisons = [
        evaluate_ab(seed, num_patients, area_configs, disruptions) for seed in seeds
    ]
    if not comparisons:
        raise ValueError("evaluate_ab_multi needs at least one seed")
    reductions = [c.wait_reduction_pct for c in comparisons]
    return AbAggregate(
        seeds=len(comparisons),
        num_patients=num_patients,
        baseline_mean_wait_min=mean(c.baseline.average_wait_min for c in comparisons),
        candidate_mean_wait_min=mean(c.candidate.average_wait_min for c in comparisons),
        mean_wait_reduction_pct=mean(reductions),
        min_wait_reduction_pct=min(reductions),
        max_wait_reduction_pct=max(reductions),
        seeds_favouring_candidate=sum(1 for r in reductions if r > 0),
    )


def headline_aggregate(aggregate: AbAggregate) -> str:
    """A demo-ready summary of the replicated A/B, honest about the spread across seeds."""
    return (
        f"load_aware vs fifo over {aggregate.seeds} seeded cohorts "
        f"({aggregate.num_patients} patients each): average wait "
        f"{aggregate.baseline_mean_wait_min:.1f} -> {aggregate.candidate_mean_wait_min:.1f} min, "
        f"mean {aggregate.mean_wait_reduction_pct:.0f}% lower "
        f"(range {aggregate.min_wait_reduction_pct:.0f}% to "
        f"{aggregate.max_wait_reduction_pct:.0f}%; favoured the smart policy in "
        f"{aggregate.seeds_favouring_candidate}/{aggregate.seeds} runs)"
    )


def headline(comparison: AbComparison) -> str:
    """A short, demo-ready summary of the improvement (deterministic, no wall-clock)."""
    return (
        f"{comparison.candidate_name} vs {comparison.baseline_name} baseline "
        f"({comparison.baseline.patient_count} patients): "
        f"average wait {comparison.baseline.average_wait_min:.1f} -> "
        f"{comparison.candidate.average_wait_min:.1f} min "
        f"({comparison.wait_reduction_pct:.0f}% lower); "
        f"peak load {comparison.peak_reduction_pct:.0f}% lower"
    )

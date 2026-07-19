"""Local run entry point: `python -m vaic.simulator.run --seed 42 --patients 80`.

Prints the four headline metrics (average wait, peak load per area, room/equipment utilisation,
ETA MAE) for the FIFO baseline and the load-aware policy on the same seeded cohort.
"""

from __future__ import annotations

import argparse

from .areas import AreaConfig
from .evaluation import compare_metrics, evaluate_ab_multi, headline, headline_aggregate
from .harness import run_ab
from .metrics import Metrics

# A high-variance, room-constrained area at moderate load: the regime where least-crowded-first
# routing (the policy the Coordinator applies, FR-02/FR-10) beats FIFO on average. In the full
# hospital the binding constraint is shared equipment, not room choice, so routing alone barely
# moves the average - an honest distinction, and why the Disruption agent reallocates the bottleneck
# rather than just re-routing. The A/B is replicated over many seeds since a single cohort is noisy.
_CONGESTED_DEMO = (
    AreaConfig(name="busy", num_rooms=4, weight=1.0, min_service_min=5.0, max_service_min=45.0),
)
_CONGESTED_DEMO_PATIENTS = 40
_CONGESTED_DEMO_SEEDS = range(200, 230)


def _format_metrics(policy_name: str, metrics: Metrics) -> str:
    lines = [
        f"== {policy_name} ==",
        f"patients: {metrics.patient_count}",
        f"average wait (min): {metrics.average_wait_min:.2f}",
        f"ETA MAE (min): {metrics.eta_mae_min:.2f}",
        "peak load per area:",
    ]
    for area, peak in sorted(metrics.peak_load_per_area.items()):
        lines.append(f"  {area}: {peak}")
    lines.append("room utilisation per area:")
    for area, utilisation in sorted(metrics.room_utilisation_per_area.items()):
        lines.append(f"  {area}: {utilisation:.1%}")
    if metrics.equipment_utilisation_per_area:
        lines.append("equipment utilisation per area:")
        for area, utilisation in sorted(metrics.equipment_utilisation_per_area.items()):
            lines.append(f"  {area}: {utilisation:.1%}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="VAIC simulator: FIFO baseline vs load-aware policy A/B on a seeded cohort."
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="RNG seed (BR-15: deterministic cohort)"
    )
    parser.add_argument(
        "--patients", type=int, default=80, help="cohort size (AS-04: ~50-100)"
    )
    args = parser.parse_args(argv)

    print("### Full hospital (DEFAULT_AREAS) ###\n")
    results = run_ab(seed=args.seed, num_patients=args.patients)
    for policy_name, metrics in results.items():
        print(_format_metrics(policy_name, metrics))
        print()
    print("== headline (full hospital) ==")
    print(headline(compare_metrics(results["fifo"], results["load_aware"])))
    print(
        "note: the full hospital is equipment-bound, so room routing alone barely moves the "
        "average - reallocating the bottleneck is the Disruption agent's job, not routing."
    )
    print()

    print("### Congested room-constrained area (replicated A/B) ###\n")
    aggregate = evaluate_ab_multi(
        seeds=_CONGESTED_DEMO_SEEDS,
        num_patients=_CONGESTED_DEMO_PATIENTS,
        area_configs=_CONGESTED_DEMO,
    )
    print("== headline (congested area, averaged over seeds) ==")
    print(headline_aggregate(aggregate))


if __name__ == "__main__":
    main()

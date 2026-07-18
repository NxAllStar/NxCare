"""The eval harness: runs the FIFO baseline and a policy on the same seeded cohort (G-01..G-03).

Each call regenerates the cohort from the same seed, so the same patients, in the same order, hit
each policy - only the routing decision differs. That keeps the wait-time and utilisation deltas
between policies honest (docs/specs/01-overview.md success metrics: "A/B on the same simulated
cohort").
"""

from __future__ import annotations

from collections.abc import Sequence

from .areas import DEFAULT_AREAS, AreaConfig
from .cohort import generate_cohort
from .disruptions import DisruptionSpec
from .metrics import Metrics, compute_metrics
from .policies import FIFOPolicy, LoadAwarePolicy, SchedulingPolicy
from .world import run_world


def run_policy(
    seed: int,
    num_patients: int,
    policy: SchedulingPolicy,
    area_configs: Sequence[AreaConfig] = DEFAULT_AREAS,
    disruptions: Sequence[DisruptionSpec] = (),
) -> Metrics:
    """Run one policy against the seeded cohort and return its metrics.

    Same `seed` and `num_patients` always produce the same cohort (BR-15), so calling this twice
    with identical arguments reproduces identical `Metrics`.
    """
    patients = generate_cohort(seed=seed, num_patients=num_patients, areas=area_configs)
    result = run_world(patients, policy, area_configs=area_configs, disruptions=disruptions)
    room_counts = {area.name: area.num_rooms for area in area_configs}
    equipment_capacity = {
        area.name: area.equipment_capacity for area in area_configs if area.equipment_capacity
    }
    return compute_metrics(
        result.recorder, result.total_duration_min, room_counts, equipment_capacity
    )


def run_ab(
    seed: int,
    num_patients: int,
    area_configs: Sequence[AreaConfig] = DEFAULT_AREAS,
    disruptions: Sequence[DisruptionSpec] = (),
) -> dict[str, Metrics]:
    """Run the FIFO baseline and the load-aware policy on the same seeded cohort.

    Phase 2 adds an agent-orchestrated policy behind the same `SchedulingPolicy` interface and
    slots into this same A/B without changing the harness (see spec 12-technical-feasibility.md).
    """
    return {
        "fifo": run_policy(seed, num_patients, FIFOPolicy(), area_configs, disruptions),
        "load_aware": run_policy(seed, num_patients, LoadAwarePolicy(), area_configs, disruptions),
    }

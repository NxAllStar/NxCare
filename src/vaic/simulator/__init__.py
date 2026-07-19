"""VAIC hospital simulator (TASK-006).

A deterministic SimPy "world": synthetic patient arrivals, rooms/equipment as SimPy resources,
injectable disruption events, a minimal scheduling-policy interface (FIFO baseline vs a load-aware
policy), and an eval harness that runs both on the same seeded cohort and reports the metrics named
in docs/specs/01-overview.md (average wait, peak load per area, room/equipment utilisation, ETA
MAE). Synthetic data only (AS-03); deterministic by seed (BR-15, NFR-REL-05).
"""

from __future__ import annotations

from .areas import DEFAULT_AREAS, AreaConfig
from .cohort import PatientArrival, generate_cohort
from .disruptions import DisruptionSpec, equipment_failure, room_failure
from .evaluation import (
    AbAggregate,
    AbComparison,
    compare_metrics,
    evaluate_ab,
    evaluate_ab_multi,
    headline,
    headline_aggregate,
)
from .harness import run_ab, run_policy
from .metrics import Metrics, PatientRecord
from .policies import FIFOPolicy, LoadAwarePolicy, SchedulingPolicy
from .world import WorldResult, run_world

__all__ = [
    "AreaConfig",
    "DEFAULT_AREAS",
    "PatientArrival",
    "generate_cohort",
    "DisruptionSpec",
    "equipment_failure",
    "room_failure",
    "run_ab",
    "run_policy",
    "AbAggregate",
    "AbComparison",
    "compare_metrics",
    "evaluate_ab",
    "evaluate_ab_multi",
    "headline",
    "headline_aggregate",
    "Metrics",
    "PatientRecord",
    "FIFOPolicy",
    "LoadAwarePolicy",
    "SchedulingPolicy",
    "WorldResult",
    "run_world",
]

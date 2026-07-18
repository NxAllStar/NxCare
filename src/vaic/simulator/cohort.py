"""Synthetic, seeded patient-arrival generation (AS-03: synthetic data only).

`PatientArrival` is deliberately its own lightweight record rather than a reuse of
`vaic.models.entities.Patient`: that model's `created_at` defaults to the wall clock
(`datetime.now`), which would make two "identical" seeded runs compare unequal for a reason that has
nothing to do with the simulation. The simulator only needs the scheduling-relevant subset of
patient state (id, arrival time, area, priority, service duration), so it keeps its own record and
stays exactly reproducible from a seed (BR-15, NFR-REL-05).
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from ..models.enums import PriorityLevel
from .areas import DEFAULT_AREAS, AreaConfig

# A four-hour simulated morning, matching the business flows this simulator stands in for.
ARRIVAL_WINDOW_MIN = 240.0

# Most arrivals are routine; urgent and emergency are rarer, matching real intake mix (FR-01).
PRIORITY_WEIGHTS: tuple[tuple[PriorityLevel, float], ...] = (
    (PriorityLevel.ROUTINE, 0.75),
    (PriorityLevel.URGENT, 0.20),
    (PriorityLevel.EMERGENCY, 0.05),
)


@dataclass(frozen=True)
class PatientArrival:
    """A synthetic patient's arrival and service-scheduling data for one simulated visit."""

    patient_id: UUID
    arrival_min: float
    area: str
    priority: PriorityLevel
    service_duration_min: float


def generate_cohort(
    seed: int,
    num_patients: int,
    areas: Sequence[AreaConfig] = DEFAULT_AREAS,
    arrival_window_min: float = ARRIVAL_WINDOW_MIN,
) -> list[PatientArrival]:
    """Generate `num_patients` synthetic arrivals, deterministic in `seed` (BR-15, NFR-REL-05).

    Same seed and same arguments always produce the same list, byte-for-byte: every random draw
    comes from one `random.Random(seed)` instance, drawn in a fixed order.
    """
    rng = random.Random(seed)
    area_names = [area.name for area in areas]
    area_weights = [area.weight for area in areas]
    areas_by_name = {area.name: area for area in areas}
    priority_values = [priority for priority, _ in PRIORITY_WEIGHTS]
    priority_weights = [weight for _, weight in PRIORITY_WEIGHTS]

    arrivals: list[PatientArrival] = []
    for _ in range(num_patients):
        area_name = rng.choices(area_names, weights=area_weights, k=1)[0]
        area = areas_by_name[area_name]
        arrival_min = rng.uniform(0.0, arrival_window_min)
        priority = rng.choices(priority_values, weights=priority_weights, k=1)[0]
        duration = rng.uniform(area.min_service_min, area.max_service_min)
        patient_id = UUID(int=rng.getrandbits(128))
        arrivals.append(
            PatientArrival(
                patient_id=patient_id,
                arrival_min=arrival_min,
                area=area_name,
                priority=priority,
                service_duration_min=duration,
            )
        )

    arrivals.sort(key=lambda patient: patient.arrival_min)
    return arrivals

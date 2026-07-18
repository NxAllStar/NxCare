"""Hospital areas: the rooms and shared equipment the simulated world is built from.

An area is a group of identical rooms (a SimPy `Resource` each, capacity 1) that may also share one
scarce piece of equipment (e.g. an X-ray machine), modelled as one shared `Resource` with its own
capacity. This is deliberately generic - it is the "world" TASK-006 owns, not the full multi-stage
care pathway (that sequencing belongs to the Care Plan / Journey agents, Phase 2).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AreaConfig:
    """One hospital area: its rooms, its arrival share, and its service-time range."""

    name: str
    num_rooms: int
    weight: float  # relative share of the cohort routed to this area
    min_service_min: float
    max_service_min: float
    equipment_capacity: int | None = None  # None: no shared equipment needed in this area

    def __post_init__(self) -> None:
        if self.num_rooms < 1:
            raise ValueError(f"{self.name}: num_rooms must be >= 1, got {self.num_rooms}")
        if self.weight <= 0:
            raise ValueError(f"{self.name}: weight must be > 0, got {self.weight}")
        if self.min_service_min < 0 or self.max_service_min < self.min_service_min:
            raise ValueError(f"{self.name}: invalid service range")
        if self.equipment_capacity is not None and self.equipment_capacity < 1:
            raise ValueError(f"{self.name}: equipment_capacity must be >= 1 when set")


# A believable morning cohort across four areas (AS-04 scale, ~50-100 patients per run). `lab` and
# `imaging` also contend for one shared machine each - the equipment side of G-03 (utilisation).
DEFAULT_AREAS: tuple[AreaConfig, ...] = (
    AreaConfig(
        name="reception", num_rooms=3, weight=0.30, min_service_min=5.0, max_service_min=10.0
    ),
    AreaConfig(
        name="consult", num_rooms=4, weight=0.35, min_service_min=10.0, max_service_min=25.0
    ),
    AreaConfig(
        name="lab",
        num_rooms=2,
        weight=0.20,
        min_service_min=8.0,
        max_service_min=15.0,
        equipment_capacity=1,
    ),
    AreaConfig(
        name="imaging",
        num_rooms=2,
        weight=0.15,
        min_service_min=15.0,
        max_service_min=30.0,
        equipment_capacity=1,
    ),
)

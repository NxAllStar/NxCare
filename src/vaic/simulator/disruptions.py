"""Injectable disruption events: a room or shared equipment goes out of service for a window.

Modelled non-preemptively: the outage is a background SimPy process that requests the affected
resource at `start_min` and holds it for `duration_min`, queueing behind whatever is already using
it exactly like a patient would. That is an intentional, documented simplification for this
hackathon-scope simulator (a real failure would preempt); it keeps the world deterministic and
simple to test while still making the resource genuinely unavailable for the injected window.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models.enums import DisruptionEventType

_VALID_TARGETS = ("room", "equipment")


@dataclass(frozen=True)
class DisruptionSpec:
    """One scripted disruption: `area`'s room (or shared equipment) is down for a window."""

    area: str
    target: str  # "room" or "equipment"
    start_min: float
    duration_min: float
    room_index: int = 0  # only meaningful when target == "room"
    event_type: DisruptionEventType = DisruptionEventType.EQUIPMENT_FAILURE

    def __post_init__(self) -> None:
        if self.target not in _VALID_TARGETS:
            raise ValueError(f"target must be one of {_VALID_TARGETS}, got {self.target!r}")
        if self.duration_min < 0 or self.start_min < 0:
            raise ValueError("start_min and duration_min must be >= 0")


def equipment_failure(area: str, start_min: float, duration_min: float) -> DisruptionSpec:
    """A shared-equipment outage in `area`, from `start_min` for `duration_min`."""
    return DisruptionSpec(
        area=area, target="equipment", start_min=start_min, duration_min=duration_min
    )


def room_failure(
    area: str, room_index: int, start_min: float, duration_min: float
) -> DisruptionSpec:
    """A single room going out of service in `area`, from `start_min` for `duration_min`."""
    return DisruptionSpec(
        area=area,
        target="room",
        room_index=room_index,
        start_min=start_min,
        duration_min=duration_min,
    )

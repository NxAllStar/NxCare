"""The scheduling-policy interface: FIFO baseline vs a simple load-aware policy.

`SchedulingPolicy` is the one hook a routing strategy needs to plug into the world in `world.py`.
Phase 2 plugs the real agent-orchestrated Coordinator behind this same interface (see
docs/specs/12-technical-feasibility.md); for now, only the two policies needed for an honest A/B
exist: `FIFOPolicy` (today's manual per-area queueing, per docs/specs/01-overview.md "current
process") and `LoadAwarePolicy` (join-shortest-queue, in the spirit of FR-02's least-crowded-slot
idea).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class SchedulingPolicy(ABC):
    """Decides which room (by index within its area) an arriving patient is routed to."""

    name: str

    @abstractmethod
    def select_room(self, area: str, room_loads: Sequence[int]) -> int:
        """Return the index into `room_loads` (one entry per room in `area`) to route to.

        `room_loads[i]` is the current occupancy of room `i` (in-service count plus queue length)
        at the moment this patient arrives.
        """


class FIFOPolicy(SchedulingPolicy):
    """Baseline: cycles through an area's rooms in strict arrival order, blind to current load.

    This mirrors "each area manages its own queue" from docs/specs/01-overview.md: a patient is
    handed the next room in rotation regardless of how backed up it already is.
    """

    name = "fifo"

    def __init__(self) -> None:
        self._next_index: dict[str, int] = {}

    def select_room(self, area: str, room_loads: Sequence[int]) -> int:
        current = self._next_index.get(area, 0)
        self._next_index[area] = current + 1
        return current % len(room_loads)


class LoadAwarePolicy(SchedulingPolicy):
    """Routes each arrival to the currently least-loaded room in its area (join-shortest-queue).

    Ties break toward the lowest room index, so behaviour stays deterministic given the same
    sequence of arrivals.
    """

    name = "load_aware"

    def select_room(self, area: str, room_loads: Sequence[int]) -> int:
        return min(range(len(room_loads)), key=lambda index: room_loads[index])

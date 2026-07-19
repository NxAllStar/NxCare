"""Hospital-wide state snapshot: the deterministic "perceive" half of the Coordinator loop (FR-10).

The snapshot is built by plain code, never a model (FR-10: "snapshot built by code" - the model
reasons over it, it does not fabricate it). The Coordinator reads it to decide what to do; the
coordinator console renders it as a load heatmap (FR-12). Load and queue depth follow the same
BR-10 rule the rest of the system uses (unpaid/LOCKED tasks count for nothing), reusing the shared
`owner_queue` / `owner_load_minutes` queries so the rule is never re-implemented here.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ...models import Resource
from ...state import Repository, owner_load_minutes, owner_queue


class OwnerLoad(BaseModel):
    """One resource's current load - the unit a heatmap cell renders."""

    model_config = ConfigDict(extra="forbid")

    owner_id: UUID
    resource_type: str
    department_id: UUID
    is_available: bool
    queue_depth: int  # paid, not-yet-finished tasks in this owner's queue (BR-10)
    load_minutes: int  # sum of their estimated minutes


class HospitalSnapshot(BaseModel):
    """A point-in-time picture of hospital-wide load, ordered by owner id for a stable render."""

    model_config = ConfigDict(extra="forbid")

    owners: list[OwnerLoad]

    def busiest(self) -> OwnerLoad | None:
        """The available owner carrying the most queued minutes, or None when all idle/closed."""
        available = [o for o in self.owners if o.is_available]
        return max(available, key=lambda o: o.load_minutes, default=None)

    def for_owner(self, owner_id: UUID) -> OwnerLoad | None:
        return next((o for o in self.owners if o.owner_id == owner_id), None)


def build_snapshot(repo: Repository) -> HospitalSnapshot:
    """Read every resource's live queue into a snapshot (deterministic, no model call)."""
    owners = [
        OwnerLoad(
            owner_id=resource.id,
            resource_type=resource.type.value,
            department_id=resource.department_id,
            is_available=resource.is_available,
            queue_depth=len(owner_queue(repo, resource.id)),
            load_minutes=owner_load_minutes(repo, resource.id),
        )
        for resource in sorted(repo.list(Resource), key=lambda r: str(r.id))
    ]
    return HospitalSnapshot(owners=owners)

"""Framework-agnostic state interface.

Persistence lives behind `Repository` so the store can be swapped without touching domain code
(a durable store is not yet chosen - spec OI-15). No agent-framework import belongs in this layer,
so it is safe under either option in ADR-001.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar
from uuid import UUID

from ..models.entities import PatientLocation, Task, _Base
from ..models.enums import ExecutionStatus, PatientLocationStatus

T = TypeVar("T", bound=_Base)


class Repository(ABC):
    """CRUD over domain entities, keyed by entity type and id."""

    @abstractmethod
    def save(self, entity: T) -> T:
        """Insert or replace `entity`; returns the stored value."""

    @abstractmethod
    def get(self, model_cls: type[T], entity_id: UUID) -> T | None:
        """Return the entity of `model_cls` with `entity_id`, or None."""

    @abstractmethod
    def list(self, model_cls: type[T], **filters) -> list[T]:
        """Return all entities of `model_cls` matching every attribute in `filters`."""

    @abstractmethod
    def delete(self, model_cls: type[T], entity_id: UUID) -> bool:
        """Remove the entity; return True if it existed."""


# ---- domain queries (encode the rules that must not be re-implemented per caller) --------------

def owner_queue(repo: Repository, owner_id: UUID) -> list[Task]:
    """Tasks that actually sit in an owner's queue: paid and not yet finished.

    Unpaid (LOCKED) tasks are excluded - BR-10 - so ETA and load reflect the patients who will
    actually be served. Ordered by sequence_index.
    """
    tasks = [t for t in repo.list(Task, owner_id=owner_id) if t.in_queue]
    return sorted(tasks, key=lambda t: t.sequence_index)


def owner_load_minutes(repo: Repository, owner_id: UUID) -> int:
    """Total estimated minutes queued for an owner - unpaid tasks contribute nothing (BR-10)."""
    return sum(t.estimated_duration_min for t in owner_queue(repo, owner_id))


def matches(task: Task, status: ExecutionStatus) -> bool:  # small helper for readability in callers
    return task.execution_status is status


def room_occupancy(repo: Repository, resource_id: UUID) -> int:
    """Count of patients currently AT_ROOM at `resource_id`, for the room-occupancy dashboard."""
    return len(
        repo.list(PatientLocation, current_resource_id=resource_id, status=PatientLocationStatus.AT_ROOM)
    )

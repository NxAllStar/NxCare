"""State layer: a swappable Repository plus the domain queries that encode load/queue rules."""

from __future__ import annotations

from .memory import InMemoryRepository
from .repository import Repository, owner_load_minutes, owner_queue

__all__ = [
    "InMemoryRepository",
    "Repository",
    "owner_load_minutes",
    "owner_queue",
]

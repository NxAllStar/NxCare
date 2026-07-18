"""In-memory Repository for tests and local/dev runs.

Stores deep copies so a caller cannot mutate stored state by holding a reference - keeping domain
updates explicit (save-what-you-changed) rather than accidental.
"""

from __future__ import annotations

from uuid import UUID

from ..models.entities import _Base
from .repository import Repository, T


class InMemoryRepository(Repository):
    def __init__(self) -> None:
        self._data: dict[str, dict[UUID, _Base]] = {}

    def _bucket(self, model_cls: type[_Base]) -> dict[UUID, _Base]:
        return self._data.setdefault(model_cls.__name__, {})

    def save(self, entity: T) -> T:
        self._bucket(type(entity))[entity.id] = entity.model_copy(deep=True)
        return entity

    def get(self, model_cls: type[T], entity_id: UUID) -> T | None:
        found = self._bucket(model_cls).get(entity_id)
        return found.model_copy(deep=True) if found is not None else None  # type: ignore[return-value]

    def list(self, model_cls: type[T], **filters) -> list[T]:
        out: list[T] = []
        for entity in self._bucket(model_cls).values():
            if all(getattr(entity, k) == v for k, v in filters.items()):
                out.append(entity.model_copy(deep=True))  # type: ignore[arg-type]
        return out

    def delete(self, model_cls: type[T], entity_id: UUID) -> bool:
        return self._bucket(model_cls).pop(entity_id, None) is not None

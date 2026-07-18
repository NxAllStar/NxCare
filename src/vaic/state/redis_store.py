"""Redis-backed Repository for the running demo.

Same interface as InMemoryRepository, so domain code never knows which is in use. Entities are
stored as JSON under `vaic:<EntityType>:<id>`. `redis` is imported lazily so tests and the
in-memory path do not require a running server.
"""

from __future__ import annotations

from uuid import UUID

from ..models.entities import _Base
from .repository import Repository, T

_KEY = "vaic:{cls}:{id}"
_PREFIX = "vaic:{cls}:"


class RedisRepository(Repository):
    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        import redis  # lazy: not needed for the in-memory path

        self._r = redis.Redis.from_url(url, decode_responses=True)

    def save(self, entity: T) -> T:
        key = _KEY.format(cls=type(entity).__name__, id=entity.id)
        self._r.set(key, entity.model_dump_json())
        return entity

    def get(self, model_cls: type[T], entity_id: UUID) -> T | None:
        raw = self._r.get(_KEY.format(cls=model_cls.__name__, id=entity_id))
        return model_cls.model_validate_json(raw) if raw is not None else None

    def list(self, model_cls: type[T], **filters) -> list[T]:
        out: list[T] = []
        for key in self._r.scan_iter(match=_PREFIX.format(cls=model_cls.__name__) + "*"):
            raw = self._r.get(key)
            if raw is None:
                continue
            entity = model_cls.model_validate_json(raw)
            if all(getattr(entity, k) == v for k, v in filters.items()):
                out.append(entity)
        return out

    def delete(self, model_cls: type[T], entity_id: UUID) -> bool:
        return self._r.delete(_KEY.format(cls=model_cls.__name__, id=entity_id)) > 0


assert issubclass(RedisRepository, Repository)  # interface parity with InMemoryRepository
assert _Base  # imported for type clarity; entities are the only things stored

"""Async CRUD over the PostgreSQL durable store (OI-15), one repository for all 15 entities.

`AsyncPostgresRepository` is the async counterpart of `vaic.state.Repository` - same four
operations (save/get/list/delete), same entity types, but backed by an `AsyncSession` instead of
Redis or the in-memory dict. It is not a subclass of `Repository` (that ABC is synchronous by
contract) and it is not wired into `build_repository()` in `api/demo_state.py`: FastAPI's demo
startup path is synchronous, and swapping the app's default store is a separate decision (OI-15 is
resolved here only at the persistence-option level).

Every entity field name matches its ORM column name 1:1 (see `models.py`), so the row<->entity
conversion is generic instead of fifteen near-identical hand-written methods (DRY).
"""

from __future__ import annotations

from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ...models.entities import Appointment as AppointmentEntity
from ...models.entities import (
    AuditLogEntry,
    CarePlan,
    Diagnosis,
    DisruptionEvent,
    IntakeSession,
    Notification,
    Patient,
    Payment,
    Resource,
    ScanEvent,
    ServiceOrder,
    ServiceType,
    Slot,
    Task,
    _Base,
)
from ..postgres import get_sessionmaker as _default_sessionmaker
from . import models as orm

T = TypeVar("T", bound=_Base)

# Pydantic entity -> mapped ORM row class, in the same order as `entities.ENTITIES`.
_ROW_FOR: dict[type[_Base], type[orm.Base]] = {
    Patient: orm.PatientRow,
    IntakeSession: orm.IntakeSessionRow,
    AppointmentEntity: orm.AppointmentRow,
    Diagnosis: orm.DiagnosisRow,
    ServiceOrder: orm.ServiceOrderRow,
    ServiceType: orm.ServiceTypeRow,
    CarePlan: orm.CarePlanRow,
    Task: orm.TaskRow,
    Slot: orm.SlotRow,
    Payment: orm.PaymentRow,
    Resource: orm.ResourceRow,
    DisruptionEvent: orm.DisruptionEventRow,
    Notification: orm.NotificationRow,
    AuditLogEntry: orm.AuditLogEntryRow,
    ScanEvent: orm.ScanEventRow,
}


def _row_cls(model_cls: type[T]) -> type[orm.Base]:
    try:
        return _ROW_FOR[model_cls]
    except KeyError:
        raise ValueError(f"no ORM row registered for {model_cls.__name__}") from None


def _to_entity(model_cls: type[T], row: orm.Base) -> T:
    return model_cls.model_validate(row, from_attributes=True)


class AsyncPostgresRepository:
    """CRUD over the 15 entities in `ENTITIES`, keyed by entity type and id, via `AsyncSession`."""

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._sessionmaker = sessionmaker or _default_sessionmaker()

    async def save(self, entity: T) -> T:
        """Insert `entity`, or replace it in place if a row with the same id already exists."""
        row_cls = _row_cls(type(entity))
        data = entity.model_dump(mode="python")
        async with self._sessionmaker() as session, session.begin():
            row = await session.get(row_cls, entity.id)
            if row is None:
                session.add(row_cls(**data))
            else:
                for field, value in data.items():
                    setattr(row, field, value)
        return entity

    async def get(self, model_cls: type[T], entity_id: UUID) -> T | None:
        row_cls = _row_cls(model_cls)
        async with self._sessionmaker() as session:
            row = await session.get(row_cls, entity_id)
            return _to_entity(model_cls, row) if row is not None else None

    async def list(self, model_cls: type[T], **filters) -> list[T]:
        row_cls = _row_cls(model_cls)
        stmt = select(row_cls).filter_by(**filters)
        async with self._sessionmaker() as session:
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_entity(model_cls, row) for row in rows]

    async def delete(self, model_cls: type[T], entity_id: UUID) -> bool:
        row_cls = _row_cls(model_cls)
        async with self._sessionmaker() as session, session.begin():
            row = await session.get(row_cls, entity_id)
            if row is None:
                return False
            await session.delete(row)
        return True

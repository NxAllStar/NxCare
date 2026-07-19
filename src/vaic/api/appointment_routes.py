"""FR-02 slot browsing + FR-19 booking/reschedule/cancel, backing `pages/BookPage.tsx`
(`lib/api/booking.ts`) and the reschedule/cancel actions in `lib/api/patient.ts`.

`GET /slots` reuses the already-tested `agents/intake/slots.recommend_slots` (FR-02) via the sync
adapter bridge rather than reimplementing least-crowded ranking - same reasoning as
`careplan_routes` and `journey_routes`. There is still no specialty->owner directory (`Resource`
carries no specialty field - the same data-model gap `agents/intake/agent.py`'s
`_book_appointment` and `agents/intake/slots.py`'s `_has_room` already document); callers may pass
explicit `owner_id` candidates, else every available `DOCTOR` resource is tried.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.concurrency import run_in_threadpool

from ..agents.intake.slots import recommend_slots
from ..auth import Account, CrudOp, resolve_scope
from ..auth import Forbidden as AuthForbidden
from ..auth.scope_async import matches_scope_async
from ..forecast import ForecastLLMError
from ..models import Appointment, AppointmentStatus, PaymentStatus, Resource, ResourceType
from ..state.sql.repository import AsyncPostgresRepository
from ..state.sql.sync_adapter import PostgresRepositorySyncAdapter
from .deps import get_async_repo, get_current_account, get_sync_adapter
from .schemas import CamelModel, camel_schema

router = APIRouter(tags=["appointments"])

AppointmentOut = camel_schema(Appointment)

_BOOKING_REFERENCE_DATE = datetime(2026, 1, 1, tzinfo=UTC)
_DEMO_HOURS = [9, 10, 11, 14, 15]


class _DemoForecastLLM:
    """Same posture as `intake_routes.py`'s `DemoForecastLLM`: no live provider wired for this
    demo, so `estimate_wait` always falls back to the tested deterministic BASELINE (BR-03)."""

    def estimate_wait(self, features: dict[str, Any]) -> dict[str, Any]:
        del features
        raise ForecastLLMError("no live forecast provider configured in this demo")


def _load_level(eta_minutes: float) -> str:
    if eta_minutes < 20:
        return "low"
    if eta_minutes < 45:
        return "medium"
    return "high"


class SlotOut(CamelModel):
    owner_id: UUID
    specialty: str
    start: datetime
    eta_minutes: float
    load_level: str


class BookAppointmentRequest(CamelModel):
    patient_id: UUID
    specialty: str
    owner_id: UUID
    hour: int


class RescheduleRequest(CamelModel):
    slot_start: datetime | None = None
    status: AppointmentStatus | None = None


@router.get("/slots", response_model=list[SlotOut])
async def list_slots(
    specialty: str,
    owner_id: list[UUID] = Query(default=[]),
    account: Account = Depends(get_current_account),
    adapter: PostgresRepositorySyncAdapter = Depends(get_sync_adapter),
):
    try:
        resolve_scope(account, Appointment, CrudOp.CREATE)  # browsing precedes booking - same gate
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    candidates = owner_id or [
        r.id
        for r in await run_in_threadpool(adapter.list, Resource, type=ResourceType.DOCTOR)
        if r.is_available
    ]
    proposals = await run_in_threadpool(
        recommend_slots, adapter, specialty, candidates, _DEMO_HOURS, _DemoForecastLLM()
    )
    return [
        SlotOut(
            owner_id=p.owner_id,
            specialty=specialty,
            start=_BOOKING_REFERENCE_DATE + timedelta(hours=p.hour),
            eta_minutes=p.eta_minutes,
            load_level=_load_level(p.eta_minutes),
        )
        for p in proposals
    ]


@router.post("/appointments", response_model=AppointmentOut, status_code=201)
async def book_appointment(
    body: BookAppointmentRequest,
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    try:
        resolve_scope(account, Appointment, CrudOp.CREATE)
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    resource = await repo.get(Resource, body.owner_id)
    if resource is None or not resource.is_available:
        raise HTTPException(status_code=409, detail="resource unavailable")

    appointment = Appointment(
        patient_id=body.patient_id,
        specialty=body.specialty,
        status=AppointmentStatus.BOOKED,
        payment_status=PaymentStatus.UNPAID,
        slot_start=_BOOKING_REFERENCE_DATE + timedelta(hours=body.hour),
    )
    return await repo.save(appointment)


@router.patch("/appointments/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(
    appointment_id: UUID,
    body: RescheduleRequest,
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    """Reschedule (`slotStart`) or cancel (`status: CANCELLED`) - FR-19."""
    try:
        scope = resolve_scope(account, Appointment, CrudOp.UPDATE)
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    appointment = await repo.get(Appointment, appointment_id)
    if appointment is None or not await matches_scope_async(repo, account, appointment, scope):
        raise HTTPException(status_code=404, detail="Appointment not found")

    updates = body.model_dump(exclude_unset=True)
    return await repo.save(appointment.model_copy(update=updates))

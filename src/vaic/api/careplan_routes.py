"""FR-03/FR-04/FR-05: diagnosis+order capture, care-plan generation/sequencing, the proceed gate.

Every handler here goes through the sync-adapter bridge (`state/sql/sync_adapter.py`) into the
already-tested `agents/careplan/*` logic - `capture_diagnosis_and_orders`, `generate_care_plan`
(which internally batch-sequences the whole order list via `sequence_orders`, BR-08), and the
proceed-gate tool - rather than reimplementing any of it against `AsyncPostgresRepository` directly.

Owner assignment and slot-candidate generation have no dedicated directory yet (same gap
`agents/intake/slots.py` and `agents/intake/agent.py` already document: `Resource` carries no
specialty field) - the caller supplies one owner per service order, and this router offers exactly
that owner as the only slot candidate. A real scheduling/optimizer surface is FR-08/FR-23's job, not
reinvented here.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from ..agents.careplan.care_plan import (
    build_activate_care_plan_tool,
    build_create_care_plan_tool,
    build_create_task_tool,
    generate_care_plan,
)
from ..agents.careplan.gate import ConfirmPaymentIn, build_confirm_payment_tool
from ..agents.careplan.orders import (
    build_create_diagnosis_tool,
    build_create_service_order_tool,
    capture_diagnosis_and_orders,
)
from ..agents.careplan.sequencing import SequencedOrder
from ..agents.careplan.slots import SlotCandidate, build_allocate_slot_tool
from ..agents.core import ActionExecutor
from ..auth import Account, CrudOp, Role, resolve_scope
from ..auth import Forbidden as AuthForbidden
from ..auth.scope_async import matches_scope_async
from ..models import CarePlan, Diagnosis, ServiceOrder, ServiceType, Task
from ..state.sql.repository import AsyncPostgresRepository
from ..state.sql.sync_adapter import PostgresRepositorySyncAdapter
from ..tools import AuditLog, ConstraintChecker, ToolError, ToolRegistry
from .deps import get_async_repo, get_current_account, get_sync_adapter
from .schemas import CamelModel, camel_schema

router = APIRouter(tags=["careplan"])

CarePlanOut = camel_schema(CarePlan)
TaskOut = camel_schema(Task)

# Demo-only scheduling default (matches `intake_routes.py`'s fixed reference date): each task's
# only slot candidate starts one hour after the previous, on its assigned owner.
_REFERENCE_DATE = datetime(2026, 1, 1, tzinfo=UTC)


def _build_executor(adapter: PostgresRepositorySyncAdapter) -> ActionExecutor:
    registry = ToolRegistry()
    registry.register(build_create_diagnosis_tool())
    registry.register(build_create_service_order_tool())
    registry.register(build_create_care_plan_tool())
    registry.register(build_create_task_tool())
    registry.register(build_allocate_slot_tool())
    registry.register(build_activate_care_plan_tool())
    registry.register(build_confirm_payment_tool())
    return ActionExecutor(adapter, registry, ConstraintChecker(adapter), AuditLog(adapter))


def _require_doctor_or_admin(account: Account) -> None:
    """CarePlan generation follows directly from a doctor's signed diagnosis/orders (BR-05); the
    FR-18 permission matrix (`auth/permissions.py`) has no CREATE op registered for CarePlan under
    any non-admin role yet - this is a pragmatic gate pending that matrix being extended, not a
    silent bypass of it."""
    if account.role not in (Role.DOCTOR, Role.ADMIN):
        detail = f"role {account.role.value} may not generate a care plan"
        raise HTTPException(status_code=403, detail=detail)


class CreateDiagnosisRequest(CamelModel):
    appointment_id: UUID
    conditions: list[str] = []
    diagnosed_by: UUID
    actor_role: str
    service_type_ids: list[UUID]


class CaptureOut(CamelModel):
    ok: bool
    diagnosis_id: UUID | None
    order_ids: list[UUID]


@router.post("/diagnoses", response_model=CaptureOut, status_code=201)
async def create_diagnosis(
    body: CreateDiagnosisRequest,
    account: Account = Depends(get_current_account),
    adapter: PostgresRepositorySyncAdapter = Depends(get_sync_adapter),
):
    _require_doctor_or_admin(account)
    executor = _build_executor(adapter)
    result = await run_in_threadpool(
        capture_diagnosis_and_orders,
        executor,
        str(account.id),
        body.appointment_id,
        body.conditions,
        body.diagnosed_by,
        body.actor_role,
        body.service_type_ids,
    )
    order_ids = [
        UUID(r.output["service_order_id"]) for r in result.order_results if r.ok and r.output
    ]
    return CaptureOut(ok=result.ok, diagnosis_id=result.diagnosis_id, order_ids=order_ids)


class OrderOwner(CamelModel):
    service_order_id: UUID
    owner_id: UUID


class CreateCarePlanRequest(CamelModel):
    patient_id: UUID
    diagnosis_id: UUID
    order_owners: list[OrderOwner]


class CarePlanCreateOut(CamelModel):
    care_plan: CarePlanOut
    tasks: list[TaskOut]
    all_slotted: bool


@router.post("/care-plans", response_model=CarePlanCreateOut, status_code=201)
async def create_care_plan(
    body: CreateCarePlanRequest,
    account: Account = Depends(get_current_account),
    adapter: PostgresRepositorySyncAdapter = Depends(get_sync_adapter),
):
    """Batch by construction: `generate_care_plan` sequences and slots the whole order list in one
    call (BR-07/BR-08), never one task at a time from the caller."""
    _require_doctor_or_admin(account)

    diagnosis = await run_in_threadpool(adapter.get, Diagnosis, body.diagnosis_id)
    if diagnosis is None:
        raise HTTPException(status_code=404, detail="Diagnosis not found")

    owner_by_order: dict[UUID, UUID] = {
        oo.service_order_id: oo.owner_id for oo in body.order_owners
    }
    orders_with_types: list[tuple[ServiceOrder, ServiceType]] = []
    for order_id in owner_by_order:
        order = await run_in_threadpool(adapter.get, ServiceOrder, order_id)
        if order is None:
            raise HTTPException(status_code=404, detail=f"ServiceOrder {order_id} not found")
        service_type = await run_in_threadpool(adapter.get, ServiceType, order.service_type_id)
        if service_type is None:
            detail = f"ServiceType for order {order_id} not found"
            raise HTTPException(status_code=404, detail=detail)
        orders_with_types.append((order, service_type))

    def owner_resolver(order: ServiceOrder, service_type: ServiceType) -> UUID:
        del service_type
        return owner_by_order[order.id]

    def candidates_for(task: Task, seq: SequencedOrder) -> list[SlotCandidate]:
        start = _REFERENCE_DATE + timedelta(hours=seq.sequence_index)
        return [SlotCandidate(resource_id=seq.owner_id, start=start)]

    def estimate_duration(service_type: ServiceType, owner_id: UUID) -> int:
        del owner_id
        return service_type.default_duration_min  # BR-09 seam: real forecast wiring is FR-07's job

    executor = _build_executor(adapter)
    try:
        result = await run_in_threadpool(
            generate_care_plan,
            adapter,
            executor,
            str(account.id),
            body.patient_id,
            diagnosis,
            orders_with_types,
            estimate_duration,
            owner_resolver,
            candidates_for,
        )
    except ToolError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return CarePlanCreateOut(
        care_plan=result.care_plan, tasks=result.tasks, all_slotted=result.all_slotted
    )


@router.get("/care-plans/{care_plan_id}/tasks", response_model=list[TaskOut])
async def list_care_plan_tasks(
    care_plan_id: UUID,
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    try:
        scope = resolve_scope(account, Task, CrudOp.READ)
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    tasks = await repo.list(Task, care_plan_id=care_plan_id)
    return [t for t in tasks if await matches_scope_async(repo, account, t, scope)]


class ConfirmPaymentRequest(CamelModel):
    actor_role: str
    confirmed_by: UUID


@router.post("/care-plans/{care_plan_id}/tasks/{task_id}/proceed", status_code=200)
async def confirm_proceed(
    care_plan_id: UUID,
    task_id: UUID,
    body: ConfirmPaymentRequest,
    account: Account = Depends(get_current_account),
    adapter: PostgresRepositorySyncAdapter = Depends(get_sync_adapter),
):
    """BR-11 proceed gate (FR-05): flips a Task's Payment to PAID, LOCKED -> PENDING."""
    del care_plan_id  # part of the URL for readability/REST nesting; the tool keys off task_id
    tool = build_confirm_payment_tool()
    params = ConfirmPaymentIn(
        task_id=task_id, actor_role=body.actor_role, confirmed_by=body.confirmed_by
    )
    try:
        return await run_in_threadpool(tool.run, params.model_dump(), adapter)
    except ToolError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

"""HTTP surface for FR-03/FR-04/FR-05/FR-08 (v2.3 FR-23): two coexisting layers, per the API design
plan (docs/tasks) for the async/sync split.

`build_careplan_router(repo, bus)` is the demo/sync-Repository factory: doctor enters a patient + a
list of test names, the Care Plan Agent resolves them, checks current station load, and proposes a
route. Doctor input is exactly `patient_id` + `list[str]` test names, matching how the FE form
collects them (`agents/careplan/routing.py` module docstring). This handler is the seam that turns
that raw input into the domain-typed pipeline `capture_diagnosis_and_orders` -> `generate_care_plan`
already expects: `resolve_service_types` maps names to seeded `ServiceType`s (never silently
dropping one that fails to resolve - AC-04 "never adds, drops, or re-targets a service" applies just
as much to never SILENTLY refusing to record one the doctor actually ordered),
`default_duration_estimator` supplies BR-09's per-test average duration from the `ServiceType`
config row, and `queue_aware_candidates_for`/`least_loaded_owner_resolver` supply FR-23's
queue-driven routing: every station offered is ranked by its CURRENT queued load, least-busy first.
`actor_role`/`diagnosed_by` are trusted here exactly as given by the caller (same posture as
`orders.py` and `gate.py`): binding them to an authenticated session is TASK-031/034, out of this
factory's scope - it remains the demo/local-dev seam `build_intake_router`/`build_patient_router`
already are.

The module-level `router` below is the native-async, `AsyncPostgresRepository`-backed,
FR-18-authenticated layer (`auth/*`, `deps.get_current_account`): diagnosis+order capture,
explicit-owner care-plan creation/sequencing, and the proceed gate, bridged into the already-tested
`agents/careplan/*` logic via `state/sql/sync_adapter.py` rather than reimplementing any of it
against `AsyncPostgresRepository` directly. Owner assignment and slot-candidate generation have no
dedicated directory yet (same gap `agents/intake/slots.py` and `agents/intake/agent.py` already
document: `Resource` carries no specialty field) - the caller supplies one owner per service order,
and this router offers exactly that owner as the only slot candidate; a real scheduling/optimizer
surface reusing FR-23's queue-aware resolvers against the authenticated/Postgres path is follow-up
work, not reinvented here.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
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
from ..agents.careplan.routing import (
    default_duration_estimator,
    least_loaded_owner_resolver,
    queue_aware_candidates_for,
    resolve_service_types,
)
from ..agents.careplan.sequencing import SequencedOrder
from ..agents.careplan.slots import SlotCandidate, build_allocate_slot_tool
from ..agents.core import ActionExecutor
from ..auth import Account, CrudOp, Role, resolve_scope
from ..auth import Forbidden as AuthForbidden
from ..auth.scope_async import matches_scope_async
from ..models import (
    Appointment,
    CarePlan,
    CarePlanStatus,
    Diagnosis,
    ServiceOrder,
    ServiceType,
    Slot,
    Task,
)
from ..state import Repository
from ..state.sql.repository import AsyncPostgresRepository
from ..state.sql.sync_adapter import PostgresRepositorySyncAdapter
from ..tools import AuditLog, ConstraintChecker, ToolError, ToolRegistry
from .demo_state import DEMO_CAREPLAN_STATIONS
from .deps import get_async_repo, get_current_account, get_sync_adapter
from .events import CarePlanEventBus
from .schemas import CamelModel, camel_schema

# Same fixed reference date the intake booking path uses (agents/intake/agent.py) - a proposed
# route's `start` here lines up with the demo's other fixed-day slots.
_BOOKING_REFERENCE_DATE = datetime(2026, 1, 1, tzinfo=UTC)
_DEMO_HOURS = [9, 10, 11, 13, 14]

# How long the SSE generator waits on the queue before emitting a comment heartbeat. A periodic
# byte keeps intermediary proxies (and the browser's EventSource) from closing an idle connection;
# it is a `:`-prefixed comment line, which SSE clients ignore.
_SSE_HEARTBEAT_SECONDS = 15.0

# Demo-only scheduling default (matches `intake_routes.py`'s fixed reference date), used by the
# authenticated `/care-plans` route below: each task's only slot candidate starts one hour after
# the previous, on its caller-assigned owner.
_REFERENCE_DATE = datetime(2026, 1, 1, tzinfo=UTC)


async def _sse_stream(
    bus: CarePlanEventBus, patient_id: UUID, heartbeat: float = _SSE_HEARTBEAT_SECONDS
):
    """SSE frames for one patient: a `: connected` comment, then a `data:` line per published event,
    with a `: keep-alive` comment whenever `heartbeat` seconds pass idle.

    Module-level (not nested in the route) so it is unit-testable by driving `__anext__` directly -
    an infinite generator cannot be exercised through the sync TestClient without hanging. The route
    just wraps it in a `StreamingResponse`.
    """
    queue = bus.subscribe(patient_id)
    try:
        # An initial comment flushes headers so the client's connection opens promptly.
        yield ": connected\n\n"
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=heartbeat)
                yield f"data: {json.dumps(event)}\n\n"
            except TimeoutError:
                yield ": keep-alive\n\n"
    finally:
        # Runs on client disconnect (GeneratorExit) too - never leak a dead subscriber.
        bus.unsubscribe(patient_id, queue)


class CarePlanGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: UUID
    appointment_id: UUID
    diagnosed_by: UUID
    actor_role: str = "role_doctor"
    conditions: list[str] = []
    service_type_names: list[str]  # the doctor's raw test list, e.g. ["Xet nghiem mau", "X-quang"]


class RouteStepOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    taskId: str
    serviceTypeCode: str
    serviceTypeLabel: str
    resourceId: str
    start: str | None
    durationMin: int
    sequenceIndex: int


class CarePlanGenerateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    carePlanId: str
    status: str
    allSlotted: bool
    route: list[RouteStepOut]


class PatientTaskOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    taskId: str
    serviceTypeCode: str
    serviceTypeLabel: str
    resourceId: str
    start: str | None
    durationMin: int
    sequenceIndex: int
    executionStatus: str
    paymentStatus: str


class ActiveCarePlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    carePlanId: str
    status: str
    tasks: list[PatientTaskOut]


def _build_demo_executor(repo: Repository) -> ActionExecutor:
    registry = ToolRegistry()
    registry.register(build_create_diagnosis_tool())
    registry.register(build_create_service_order_tool())
    registry.register(build_create_care_plan_tool())
    registry.register(build_create_task_tool())
    registry.register(build_allocate_slot_tool())
    registry.register(build_activate_care_plan_tool())
    audit = AuditLog(repo)
    return ActionExecutor(repo, registry, ConstraintChecker(repo), audit)


def build_careplan_router(repo: Repository, bus: CarePlanEventBus | None = None) -> APIRouter:
    """Bind the demo `Repository` into the router's closure - one repo instance per running app.

    A fresh `APIRouter()` per call, never a module-level singleton: a module-level router would
    accumulate one `/generate` handler per call to this function (each bound to whatever `repo` was
    passed that time), and since `vaic.api.__init__` imports `app.py` - which calls `create_app()`
    at import time - merely IMPORTING this module anywhere already registers one such handler.
    Route-level tests that build a second, independent router (their own isolated repo) would then
    silently hit the first-registered handler's repo instead of their own.

    `bus` is optional: when omitted (route-level unit tests, the standalone demo script) `/generate`
    still works and `/stream` reports the stream is disabled. The running app always passes one so a
    generated plan pushes a live "refresh" to that patient's open screen (TASK-038 real-time).
    """
    router = APIRouter(prefix="/api/careplan", tags=["careplan"])

    @router.post("/generate", response_model=CarePlanGenerateResponse)
    def generate(body: CarePlanGenerateRequest) -> CarePlanGenerateResponse:
        if repo.get(Appointment, body.appointment_id) is None:
            raise HTTPException(404, detail="appointment_id does not reference a known Appointment")

        resolution = resolve_service_types(repo, body.service_type_names)
        if not resolution.ok:
            # Never silently drop a doctor-ordered test (BR-07's spirit): refuse the whole request
            # and name exactly which entries did not match a seeded ServiceType.
            raise HTTPException(
                422,
                detail={
                    "message": "one or more test names did not match a known ServiceType",
                    "unmatchedServiceNames": resolution.unmatched,
                },
            )

        executor = _build_demo_executor(repo)
        capture = capture_diagnosis_and_orders(
            executor,
            actor="careplan-agent",
            appointment_id=body.appointment_id,
            conditions=body.conditions,
            diagnosed_by=body.diagnosed_by,
            actor_role=body.actor_role,
            service_type_ids=[st.id for st in resolution.resolved],
            reasoning="doctor-ordered tests via /api/careplan/generate",
        )
        if not capture.ok:
            first_failure = next(
                (r.reason for r in [capture.diagnosis_result, *capture.order_results] if not r.ok),
                "diagnosis/order capture failed",
            )
            raise HTTPException(422, detail=first_failure)

        diagnosis = repo.get(Diagnosis, capture.diagnosis_id)
        assert diagnosis is not None  # just created above; a missing read-back is a repo defect

        orders_with_types: list[tuple[ServiceOrder, ServiceType]] = []
        pairs = zip(capture.order_results, resolution.resolved, strict=True)
        for order_result, service_type in pairs:
            order = repo.get(ServiceOrder, UUID(order_result.output["service_order_id"]))
            assert order is not None
            orders_with_types.append((order, service_type))

        candidate_stations = list(DEMO_CAREPLAN_STATIONS)
        result = generate_care_plan(
            repo,
            executor,
            actor="careplan-agent",
            patient_id=body.patient_id,
            diagnosis=diagnosis,
            orders_with_types=orders_with_types,
            estimate_duration=default_duration_estimator,
            owner_resolver=least_loaded_owner_resolver(repo, candidate_stations),
            candidates_for=queue_aware_candidates_for(
                repo, candidate_stations, _DEMO_HOURS, _BOOKING_REFERENCE_DATE
            ),
            reasoning="queue-driven route generation (FR-23 v2.3)",
        )

        route: list[RouteStepOut] = []
        for task, seq in zip(result.tasks, result.sequenced, strict=True):
            slots = repo.list(Slot, task_id=task.id)
            slot = slots[0] if slots else None
            route.append(
                RouteStepOut(
                    taskId=str(task.id),
                    serviceTypeCode=seq.service_type.code,
                    serviceTypeLabel=seq.service_type.display_label,
                    resourceId=str(task.owner_id),
                    start=slot.start.isoformat() if slot is not None else None,
                    durationMin=task.estimated_duration_min,
                    sequenceIndex=task.sequence_index,
                )
            )

        # Push a "refresh now" hint to that patient's open screen(s), if any. The event carries no
        # clinical data - the client refetches `/active` under its own auth scope - so a misdelivery
        # could never leak another patient's plan (NFR-SEC-05); it is keyed to this patient only.
        if bus is not None:
            bus.publish(
                body.patient_id,
                {"type": "careplan.updated", "carePlanId": str(result.care_plan.id)},
            )

        return CarePlanGenerateResponse(
            carePlanId=str(result.care_plan.id),
            status=result.care_plan.status.value,
            allSlotted=result.all_slotted,
            route=route,
        )

    @router.get("/patient/{patient_id}/active", response_model=ActiveCarePlanResponse)
    def get_active_care_plan(patient_id: UUID) -> ActiveCarePlanResponse:
        """Read-side companion to `/generate`: the patient screen's source for FR-04's handoff.

        Returns the patient's most recently created `ACTIVE` `CarePlan` with its tasks, sequenced
        and enriched with the `ServiceType` label/code each task's `ServiceOrder` references - the
        same lookup a `DRAFT` plan (not yet fully slotted, see the failure/rollback contract in
        `care_plan.py`) is deliberately excluded from, since it is not yet ready to show a patient.
        """
        plans = [
            plan
            for plan in repo.list(CarePlan, patient_id=patient_id)
            if plan.status is CarePlanStatus.ACTIVE
        ]
        if not plans:
            raise HTTPException(404, detail="no active care plan for this patient")
        plan = max(plans, key=lambda p: p.created_at)

        tasks = sorted(repo.list(Task, care_plan_id=plan.id), key=lambda t: t.sequence_index)
        task_out: list[PatientTaskOut] = []
        for task in tasks:
            order = repo.get(ServiceOrder, task.service_order_id)
            assert order is not None  # created together with the task in generate_care_plan
            service_type = repo.get(ServiceType, order.service_type_id)
            assert service_type is not None
            slots = repo.list(Slot, task_id=task.id)
            slot = slots[0] if slots else None
            task_out.append(
                PatientTaskOut(
                    taskId=str(task.id),
                    serviceTypeCode=service_type.code,
                    serviceTypeLabel=service_type.display_label,
                    resourceId=str(task.owner_id),
                    start=slot.start.isoformat() if slot is not None else None,
                    durationMin=task.estimated_duration_min,
                    sequenceIndex=task.sequence_index,
                    executionStatus=task.execution_status.value,
                    paymentStatus=task.payment_status.value,
                )
            )

        return ActiveCarePlanResponse(
            carePlanId=str(plan.id), status=plan.status.value, tasks=task_out
        )

    @router.get("/patient/{patient_id}/stream")
    async def stream_care_plan_events(patient_id: UUID) -> StreamingResponse:
        """Server-Sent Events for one patient: pushes a `careplan.updated` event whenever a plan is
        (re)generated for them, so the patient screen refetches `/active` immediately instead of
        polling. One long-lived `GET`; the browser's `EventSource` auto-reconnects if it drops.

        Read-only and single-patient: a connection only ever hears its own `patient_id`'s events
        (the bus is keyed by it), and the events carry no clinical payload.
        """
        if bus is None:
            raise HTTPException(503, detail="event stream not enabled on this app instance")

        return StreamingResponse(
            _sse_stream(bus, patient_id),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return router


# --- Native-async, FR-18-authenticated layer (AsyncPostgresRepository) -----------------------

router = APIRouter(tags=["careplan"])

CarePlanOut = camel_schema(CarePlan)
TaskOut = camel_schema(Task)


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

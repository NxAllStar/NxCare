"""HTTP surface for FR-03/FR-04/FR-08 (v2.3 FR-23): doctor enters a patient + a list of test names,
the Care Plan Agent resolves them, checks current station load, and proposes a route.

Doctor input is exactly `patient_id` + `list[str]` test names, matching how the FE form collects
them (`agents/careplan/routing.py` module docstring). This handler is the seam that turns that raw
input into the domain-typed pipeline `capture_diagnosis_and_orders` -> `generate_care_plan` already
expects: `resolve_service_types` maps names to seeded `ServiceType`s (never silently dropping one
that fails to resolve - AC-04 "never adds, drops, or re-targets a service" applies just as much to
never SILENTLY refusing to record one the doctor actually ordered), `default_duration_estimator`
supplies BR-09's per-test average duration from the `ServiceType` config row, and
`queue_aware_candidates_for`/`least_loaded_owner_resolver` supply FR-23's queue-driven routing:
every station offered is ranked by its CURRENT queued load, least-busy first.

`actor_role` / `diagnosed_by` are trusted here exactly as given by the caller (same posture as
`orders.py` and `gate.py`): binding them to an authenticated session is TASK-031/034, out of this
endpoint's scope.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict

from ..agents.careplan.care_plan import (
    build_activate_care_plan_tool,
    build_create_care_plan_tool,
    build_create_task_tool,
    generate_care_plan,
)
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
from ..agents.careplan.slots import build_allocate_slot_tool
from ..agents.core import ActionExecutor
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
from ..tools import AuditLog, ConstraintChecker, ToolRegistry
from .demo_state import DEMO_CAREPLAN_STATIONS
from .events import CarePlanEventBus

# Same fixed reference date the intake booking path uses (agents/intake/agent.py) - a proposed
# route's `start` here lines up with the demo's other fixed-day slots.
_BOOKING_REFERENCE_DATE = datetime(2026, 1, 1, tzinfo=UTC)
_DEMO_HOURS = [9, 10, 11, 13, 14]

# How long the SSE generator waits on the queue before emitting a comment heartbeat. A periodic
# byte keeps intermediary proxies (and the browser's EventSource) from closing an idle connection;
# it is a `:`-prefixed comment line, which SSE clients ignore.
_SSE_HEARTBEAT_SECONDS = 15.0


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


def _build_executor(repo: Repository) -> ActionExecutor:
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

        executor = _build_executor(repo)
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

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

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
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
from ..models import Appointment, Diagnosis, ServiceOrder, ServiceType, Slot
from ..state import Repository
from ..tools import AuditLog, ConstraintChecker, ToolRegistry
from .demo_state import DEMO_CAREPLAN_STATIONS

# Same fixed reference date the intake booking path uses (agents/intake/agent.py) - a proposed
# route's `start` here lines up with the demo's other fixed-day slots.
_BOOKING_REFERENCE_DATE = datetime(2026, 1, 1, tzinfo=UTC)
_DEMO_HOURS = [9, 10, 11, 13, 14]


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


def build_careplan_router(repo: Repository) -> APIRouter:
    """Bind the demo `Repository` into the router's closure - one repo instance per running app.

    A fresh `APIRouter()` per call, never a module-level singleton: a module-level router would
    accumulate one `/generate` handler per call to this function (each bound to whatever `repo` was
    passed that time), and since `vaic.api.__init__` imports `app.py` - which calls `create_app()`
    at import time - merely IMPORTING this module anywhere already registers one such handler.
    Route-level tests that build a second, independent router (their own isolated repo) would then
    silently hit the first-registered handler's repo instead of their own.
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

        return CarePlanGenerateResponse(
            carePlanId=str(result.care_plan.id),
            status=result.care_plan.status.value,
            allSlotted=result.all_slotted,
            route=route,
        )

    return router

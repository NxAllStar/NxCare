"""HTTP surface for the coordinator console (FR-12 backend for FR-09 / FR-10).

Three things the console needs, backed by live agents rather than fixtures:
- a hospital-wide load snapshot to render as a heatmap (`build_snapshot`, FR-10 perceive),
- the disruption/approval queue (re-plans parked above the blast-radius threshold, FR-09),
- one-tap approve / reject on a parked re-plan.

The trigger endpoint runs a disruption through the Coordinator loop so the whole perceive -> reason
-> act path (and its audit trail) is exercised end to end. One `CoordinatorStack` is built per app
and shared across requests, so every call goes through the same guarded executor and audit log.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from ..agents.core import CoordinatorEvent, build_coordinator_stack, build_snapshot
from ..agents.core.disruption import DisruptionError, DisruptionOutcome
from ..auth import Account, authorize
from ..auth import Forbidden as AuthForbidden
from ..models import DisruptionEvent, DisruptionEventType, DisruptionStatus, Resource
from ..state import Repository
from .deps import get_current_account

# Event-type string (API) -> coordinator event kind the rule-based brain routes on.
_EVENT_KIND = {
    DisruptionEventType.EQUIPMENT_FAILURE: "equipment_failure",
    DisruptionEventType.OVERLOAD: "overload",
    DisruptionEventType.SCHEDULE_CHANGE: "overload",
    DisruptionEventType.EMERGENCY: "equipment_failure",
}


class OwnerLoadOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ownerId: str
    resourceType: str
    departmentId: str
    isAvailable: bool
    queueDepth: int
    loadMinutes: int


class SnapshotOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owners: list[OwnerLoadOut]
    busiestOwnerId: str | None


class DisruptionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disruptionId: str
    eventType: str
    status: str
    blastRadius: int
    resourceId: str | None
    decidedBy: str | None


class DisruptionListOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disruptions: list[DisruptionOut]
    pendingApproval: list[DisruptionOut]  # the approval queue the console surfaces (FR-09 US-09)


class DisruptionOutcomeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disruptionId: str
    blastRadius: int
    tier: str
    executed: bool
    status: str
    reassigned: int


class TriggerDisruptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resourceId: str
    eventType: str = DisruptionEventType.EQUIPMENT_FAILURE.value


def _outcome_out(outcome: DisruptionOutcome) -> DisruptionOutcomeOut:
    return DisruptionOutcomeOut(
        disruptionId=str(outcome.disruption_id),
        blastRadius=outcome.blast_radius,
        tier=outcome.tier,
        executed=outcome.executed,
        status=outcome.status,
        reassigned=outcome.reassigned,
    )


def _disruption_out(event: DisruptionEvent) -> DisruptionOut:
    return DisruptionOut(
        disruptionId=str(event.id),
        eventType=event.event_type.value,
        status=event.status.value,
        blastRadius=event.blast_radius,
        resourceId=str(event.resource_id) if event.resource_id else None,
        decidedBy=str(event.decided_by) if event.decided_by else None,
    )


def _parse_uuid(raw: str, field: str) -> UUID:
    try:
        return UUID(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"invalid {field} id") from exc


def build_coordinator_router(repo: Repository) -> APIRouter:
    stack = build_coordinator_stack(repo)
    router = APIRouter(prefix="/coordinator", tags=["coordinator"])

    @router.get("/snapshot", response_model=SnapshotOut)
    def snapshot() -> SnapshotOut:
        snap = build_snapshot(repo)
        busiest = snap.busiest()
        return SnapshotOut(
            owners=[
                OwnerLoadOut(
                    ownerId=str(o.owner_id),
                    resourceType=o.resource_type,
                    departmentId=str(o.department_id),
                    isAvailable=o.is_available,
                    queueDepth=o.queue_depth,
                    loadMinutes=o.load_minutes,
                )
                for o in snap.owners
            ],
            busiestOwnerId=str(busiest.owner_id) if busiest else None,
        )

    @router.get("/disruptions", response_model=DisruptionListOut)
    def disruptions() -> DisruptionListOut:
        events = sorted(repo.list(DisruptionEvent), key=lambda e: e.created_at)
        out = [_disruption_out(e) for e in events]
        pending = [
            _disruption_out(e)
            for e in events
            if e.status is DisruptionStatus.PENDING_APPROVAL
        ]
        return DisruptionListOut(disruptions=out, pendingApproval=pending)

    @router.post("/disruptions", response_model=DisruptionOutcomeOut)
    def trigger(body: TriggerDisruptionRequest) -> DisruptionOutcomeOut:
        resource_id = _parse_uuid(body.resourceId, "resourceId")
        if repo.get(Resource, resource_id) is None:
            raise HTTPException(status_code=404, detail="unknown resource")
        try:
            event_type = DisruptionEventType(body.eventType)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="unknown eventType") from exc

        results = stack.coordinator.handle(
            [CoordinatorEvent(kind=_EVENT_KIND[event_type], resource_id=resource_id)]
        )
        outcome = results[0].disruption
        if outcome is None:  # the coordinator observed but did not delegate a re-plan
            raise HTTPException(status_code=409, detail="event did not produce a re-plan")
        return _outcome_out(outcome)

    @router.post("/disruptions/{disruption_id}/approve", response_model=DisruptionOutcomeOut)
    def approve(
        disruption_id: str, account: Account = Depends(get_current_account)
    ) -> DisruptionOutcomeOut:
        # FR-09 human-in-the-loop gate: `decided_by` is the authenticated principal, never a
        # caller-supplied id (a spoofable id would let any token holder approve a large re-plan
        # and have it audited under someone else's name).
        try:
            authorize(account, "approve_replan")
        except AuthForbidden as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        did = _parse_uuid(disruption_id, "disruption")
        decided_by = account.resource_id or account.id
        try:
            return _outcome_out(stack.disruption.approve(did, decided_by=decided_by))
        except DisruptionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/disruptions/{disruption_id}/reject", response_model=DisruptionOutcomeOut)
    def reject(
        disruption_id: str, account: Account = Depends(get_current_account)
    ) -> DisruptionOutcomeOut:
        try:
            authorize(account, "reject_replan")
        except AuthForbidden as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        did = _parse_uuid(disruption_id, "disruption")
        decided_by = account.resource_id or account.id
        try:
            return _outcome_out(stack.disruption.reject(did, decided_by=decided_by))
        except DisruptionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    return router

"""FR-09/FR-10 disruption reporting and coordinator decisions.

No dedicated Disruption Agent module exists under `agents/` yet (confirmed absent) - these routes
operate directly against `DisruptionEvent`/`AuditLogEntry` via `AsyncPostgresRepository`, native
async, no sync bridge needed. Flagged as a gap: a real Disruption Agent (auto-detection, tiered
autonomy, blast-radius assessment) is separate, larger work, not reinvented here.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ..auth import Account, CrudOp, Role, resolve_scope
from ..auth import Forbidden as AuthForbidden
from ..auth.scope_async import matches_scope_async
from ..models import DisruptionEvent, DisruptionEventType, DisruptionStatus
from ..state.sql.repository import AsyncPostgresRepository
from .deps import PageParams, get_async_repo, get_current_account
from .schemas import CamelModel, camel_schema

router = APIRouter(prefix="/disruptions", tags=["disruptions"])

DisruptionOut = camel_schema(DisruptionEvent)


class ReportDisruptionRequest(CamelModel):
    event_type: DisruptionEventType
    blast_radius: int = 0


@router.post("", response_model=DisruptionOut, status_code=201)
async def report_disruption(
    body: ReportDisruptionRequest,
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    # The FR-18 permission matrix has no CREATE op for DisruptionEvent under any non-admin role
    # (it assumes a future Disruption Agent reports these, not a human CRUD call) - pending that,
    # only coordinator/admin staff may report one here.
    if account.role not in (Role.COORDINATOR, Role.ADMIN):
        detail = f"role {account.role.value} may not report a disruption"
        raise HTTPException(status_code=403, detail=detail)
    event = DisruptionEvent(event_type=body.event_type, blast_radius=body.blast_radius)
    return await repo.save(event)


@router.get("", response_model=list[DisruptionOut])
async def list_disruptions(
    page: PageParams = Depends(),
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    try:
        scope = resolve_scope(account, DisruptionEvent, CrudOp.READ)
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    events = await repo.list(DisruptionEvent)
    visible = [e for e in events if await matches_scope_async(repo, account, e, scope)]
    return page.slice(visible)


class DisruptionDecisionRequest(CamelModel):
    approve: bool


@router.post("/{disruption_id}/decision", response_model=DisruptionOut)
async def decide_disruption(
    disruption_id: UUID,
    body: DisruptionDecisionRequest,
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    """`approve_replan`/`reject_replan` are coordinator/admin-only named actions
    (`auth/permissions.py::ACTION_ROLES`)."""
    if account.role not in (Role.COORDINATOR, Role.ADMIN):
        detail = f"role {account.role.value} may not decide a replan"
        raise HTTPException(status_code=403, detail=detail)
    event = await repo.get(DisruptionEvent, disruption_id)
    if event is None:
        raise HTTPException(status_code=404, detail="DisruptionEvent not found")
    updated = event.model_copy(
        update={
            "status": DisruptionStatus.APPROVED if body.approve else DisruptionStatus.REJECTED,
            "decided_by": account.id,
        }
    )
    return await repo.save(updated)

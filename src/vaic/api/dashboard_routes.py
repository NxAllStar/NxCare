"""FR-12 coordinator dashboard - a genuine batch endpoint: several independent reads fanned out
with `asyncio.gather` in one round trip, instead of the frontend making N sequential requests.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from ..auth import Account, CrudOp, Role, resolve_scope
from ..auth import Forbidden as AuthForbidden
from ..models import DisruptionEvent, DisruptionStatus, Resource, Task
from ..state.sql.repository import AsyncPostgresRepository
from .deps import get_async_repo, get_current_account
from .schemas import CamelModel, camel_schema

router = APIRouter(prefix="/coordinator", tags=["dashboard"])

ResourceOut = camel_schema(Resource)
DisruptionOut = camel_schema(DisruptionEvent)


class OwnerLoadOut(CamelModel):
    owner: ResourceOut
    load_minutes: int
    queue_length: int


class DashboardOut(CamelModel):
    owner_loads: list[OwnerLoadOut]
    pending_disruptions: list[DisruptionOut]


@router.get("/dashboard", response_model=DashboardOut)
async def get_dashboard(
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    if account.role not in (Role.COORDINATOR, Role.ADMIN):
        detail = f"role {account.role.value} may not view the coordinator dashboard"
        raise HTTPException(status_code=403, detail=detail)
    try:
        resolve_scope(account, DisruptionEvent, CrudOp.READ)
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    resources, all_disruptions = await asyncio.gather(
        repo.list(Resource),
        repo.list(DisruptionEvent),
    )

    async def _owner_load(resource: Resource) -> OwnerLoadOut:
        tasks = await repo.list(Task, owner_id=resource.id)
        queue = [t for t in tasks if t.in_queue]
        return OwnerLoadOut(
            owner=resource,
            load_minutes=sum(t.estimated_duration_min for t in queue),
            queue_length=len(queue),
        )

    owner_loads = await asyncio.gather(*(_owner_load(r) for r in resources))
    pending = [
        d
        for d in all_disruptions
        if d.status in (DisruptionStatus.DETECTED, DisruptionStatus.PENDING_APPROVAL)
    ]

    return DashboardOut(owner_loads=list(owner_loads), pending_disruptions=pending)

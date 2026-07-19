"""Generic scope-filtered CRUD router factory, for entities with no special business rule.

Used for `ServiceType`, `Resource`, `DisruptionEvent`, `AuditLogEntry`, `ScanEvent` - reference/log
data whose only "logic" is the FR-18 permission matrix (`auth/permissions.py`), so one factory
covers all of them instead of five near-identical route modules (DRY).

Entities with real business rules (booking capacity, care-plan generation, the proceed gate,
resequencing, notifications) get their own router - see `careplan_routes.py`, `journey_routes.py`,
`appointment_routes.py`, `notifications_routes.py`.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ..auth import Account, CrudOp, Forbidden, resolve_scope
from ..auth.permissions import list_scoped_async
from ..auth.scope_async import matches_scope_async
from ..models.entities import _Base
from ..state.sql.repository import AsyncPostgresRepository
from .deps import PageParams, get_async_repo, get_current_account
from .schemas import camel_schema


def build_entity_router(
    entity_cls: type[_Base],
    prefix: str,
    tags: list[str],
    *,
    allow_create: bool = False,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=tags)
    out_schema = camel_schema(entity_cls)

    @router.get("", response_model=list[out_schema])
    async def list_entities(
        page: PageParams = Depends(),
        account: Account = Depends(get_current_account),
        repo: AsyncPostgresRepository = Depends(get_async_repo),
    ):
        try:
            records = await list_scoped_async(repo, account, entity_cls, CrudOp.READ)
        except Forbidden as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return page.slice(records)

    @router.get("/{entity_id}", response_model=out_schema)
    async def get_entity(
        entity_id: UUID,
        account: Account = Depends(get_current_account),
        repo: AsyncPostgresRepository = Depends(get_async_repo),
    ):
        try:
            scope = resolve_scope(account, entity_cls, CrudOp.READ)
        except Forbidden as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        record = await repo.get(entity_cls, entity_id)
        if record is None or not await matches_scope_async(repo, account, record, scope):
            raise HTTPException(status_code=404, detail=f"{entity_cls.__name__} not found")
        return record

    if allow_create:

        @router.post("", response_model=out_schema, status_code=201)
        async def create_entity(
            body: out_schema,  # type: ignore[valid-type]
            account: Account = Depends(get_current_account),
            repo: AsyncPostgresRepository = Depends(get_async_repo),
        ):
            try:
                resolve_scope(account, entity_cls, CrudOp.CREATE)
            except Forbidden as exc:
                raise HTTPException(status_code=403, detail=str(exc)) from exc
            entity = entity_cls.model_validate(body.model_dump())
            return await repo.save(entity)

    return router

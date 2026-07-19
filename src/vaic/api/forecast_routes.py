"""FR-07 forecast tool: `estimate_wait`, exposed read-only per resource/hour.

`estimate_wait` itself does no I/O beyond `retrieve_features(repo, ...)` and is not async - it is
still routed through the sync-adapter bridge (rather than reimplemented) since it takes the sync
`Repository` interface and this keeps the grounding contract (retrieve/reason/validate, BR-03)
exactly as tested.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from ..auth import Account, CrudOp, resolve_scope
from ..auth import Forbidden as AuthForbidden
from ..forecast import ForecastLLMError, ForecastResult, estimate_wait
from ..models import Resource
from ..state.sql.sync_adapter import PostgresRepositorySyncAdapter
from .deps import get_current_account, get_sync_adapter
from .schemas import CamelModel

router = APIRouter(tags=["forecast"])


class _DemoForecastLLM:
    """Same posture as the other routers' demo stand-in: no live forecast provider is wired for
    this demo (model-policy.md), so every call degrades to the tested BASELINE estimate (BR-03)."""

    def estimate_wait(self, features: dict[str, Any]) -> dict[str, Any]:
        del features
        raise ForecastLLMError("no live forecast provider configured in this demo")


class ForecastOut(CamelModel):
    value: float
    confidence: float
    provenance: str
    source: str


@router.get("/resources/{owner_id}/forecast", response_model=ForecastOut)
async def get_forecast(
    owner_id: UUID,
    hour: int,
    account: Account = Depends(get_current_account),
    adapter: PostgresRepositorySyncAdapter = Depends(get_sync_adapter),
):
    try:
        resolve_scope(account, Resource, CrudOp.READ)
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    result: ForecastResult = await run_in_threadpool(
        estimate_wait, adapter, owner_id, hour, _DemoForecastLLM()
    )
    return ForecastOut(
        value=result.value,
        confidence=result.confidence,
        provenance=result.provenance,
        source=result.source,
    )

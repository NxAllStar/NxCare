"""FR-06/FR-14 Journey Agent (chat, resequencing) and FR-17 patient-code scan.

`resequence` is batch by construction: `propose_resequence`/`apply_order` already take and return
the FULL task list in one call (BR-13's dependency-legal check only means anything over the whole
list at once), never one task at a time. `chat` and `scan` go through the sync-adapter bridge into
the existing tested `agents/journey/*` logic; task/plan reads are native async against
`AsyncPostgresRepository`.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from ..agents.core import ActionExecutor
from ..agents.journey.chat import ChatReasonerError, interpret_chat
from ..agents.journey.llm_client import build_journey_chat_llm
from ..agents.journey.resequence import apply_order, propose_resequence
from ..agents.journey.scan import ScanPatientIn, register_journey_tools
from ..auth import Account, CrudOp, resolve_scope
from ..auth import Forbidden as AuthForbidden
from ..auth.scope_async import matches_scope_async
from ..models import CarePlan, ServiceOrder, ServiceType, Task
from ..state.sql.repository import AsyncPostgresRepository
from ..state.sql.sync_adapter import PostgresRepositorySyncAdapter
from ..tools import Action, AuditLog, ConstraintChecker, ToolRegistry
from .deps import get_async_repo, get_current_account, get_sync_adapter
from .schemas import CamelModel, camel_schema

router = APIRouter(tags=["journey"])

TaskOut = camel_schema(Task)
_journey_llm = build_journey_chat_llm()  # real client when configured, else the rule-based reasoner


async def _authorized_task(task_id: UUID, account: Account, repo: AsyncPostgresRepository) -> Task:
    try:
        scope = resolve_scope(account, Task, CrudOp.READ)
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    task = await repo.get(Task, task_id)
    if task is None or not await matches_scope_async(repo, account, task, scope):
        raise HTTPException(status_code=404, detail="Task not found")
    return task


async def _service_type_for(repo: AsyncPostgresRepository, task: Task) -> ServiceType | None:
    order = await repo.get(ServiceOrder, task.service_order_id)
    return await repo.get(ServiceType, order.service_type_id) if order is not None else None


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: UUID,
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    return await _authorized_task(task_id, account, repo)


class StepDetailOut(CamelModel):
    task: TaskOut
    service_type: str
    requires_fasting: bool
    turnaround_minutes: int


@router.get("/tasks/{task_id}/step-detail", response_model=StepDetailOut)
async def get_step_detail(
    task_id: UUID,
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    task = await _authorized_task(task_id, account, repo)
    service_type = await _service_type_for(repo, task)
    return StepDetailOut(
        task=task,
        service_type=service_type.display_label if service_type else "",
        requires_fasting=bool(service_type and service_type.requires_fasting),
        turnaround_minutes=service_type.turnaround_minutes if service_type else 0,
    )


class ChatRequest(CamelModel):
    care_plan_id: UUID
    message: str


class ChatReplyOut(CamelModel):
    answer: str
    intent: str


@router.post("/journey/chat", response_model=ChatReplyOut)
async def journey_chat(
    body: ChatRequest,
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    try:
        scope = resolve_scope(account, CarePlan, CrudOp.READ)
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    plan = await repo.get(CarePlan, body.care_plan_id)
    if plan is None or not await matches_scope_async(repo, account, plan, scope):
        raise HTTPException(status_code=404, detail="CarePlan not found")

    tasks = await repo.list(Task, care_plan_id=plan.id)
    has_fasting_step = False
    for task in tasks:
        service_type = await _service_type_for(repo, task)
        if service_type is not None and service_type.requires_fasting:
            has_fasting_step = True
            break

    context = {"has_fasting_step": has_fasting_step}
    try:
        reply = await run_in_threadpool(interpret_chat, body.message, context, _journey_llm)
    except ChatReasonerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatReplyOut(answer=reply.answer, intent=reply.intent)


class ResequenceRequest(CamelModel):
    care_plan_id: UUID
    etas: dict[UUID, int] = {}


class ResequenceOut(CamelModel):
    applied: bool
    reason: str | None
    tasks: list[TaskOut]


@router.post("/journey/tasks/resequence", response_model=ResequenceOut)
async def resequence_tasks(
    body: ResequenceRequest,
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    """Batch by construction: one call reorders the plan's whole task list, not one task at a
    time - `propose_resequence`/`apply_order` already operate over the full list."""
    try:
        scope = resolve_scope(account, Task, CrudOp.UPDATE)
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    tasks = await repo.list(Task, care_plan_id=body.care_plan_id)
    if tasks and not await matches_scope_async(repo, account, tasks[0], scope):
        raise HTTPException(status_code=403, detail="not authorized to reorder this plan")

    proposal = propose_resequence(tasks, body.etas)
    if proposal is None:
        return ResequenceOut(applied=False, reason=None, tasks=tasks)

    reordered = apply_order(tasks, proposal.order)
    saved = [await repo.save(t) for t in reordered]
    return ResequenceOut(applied=True, reason=proposal.reason, tasks=saved)


class ScanRequest(CamelModel):
    task_id: UUID
    scanned_by: UUID
    patient_code: str


@router.post("/journey/scan")
async def scan_patient(
    body: ScanRequest,
    account: Account = Depends(get_current_account),
    adapter: PostgresRepositorySyncAdapter = Depends(get_sync_adapter),
):
    registry = ToolRegistry()
    register_journey_tools(registry)
    executor = ActionExecutor(adapter, registry, ConstraintChecker(adapter), AuditLog(adapter))

    action = Action(
        tool="scan_patient",
        actor=str(account.id),
        reasoning="counter/room scan",
        params=ScanPatientIn(
            task_id=body.task_id, scanned_by=body.scanned_by, patient_code=body.patient_code
        ).model_dump(),
    )
    result = await run_in_threadpool(executor.execute, action)
    if not result.ok:
        raise HTTPException(status_code=422, detail=result.reason)
    return result.output

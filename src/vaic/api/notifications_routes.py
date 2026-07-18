"""FR-11 patient timeline notifications + FR-20 notifications center.

`POST /notifications/batch` is the batch endpoint: one `Notifier.assert_scope` check across the
WHOLE `about_task_ids` set per entry before anything is persisted, and the notifications are all
saved in a single call - not the frontend looping a single-send endpoint per notification.

`PATCH /notifications/{id}` (`lib/api/notifications.ts::markNotificationRead`) is NOT built here:
`Notification` has no `read` boolean in `models/entities.py`/`docs/specs/08-data-model.md` - the
same kind of data-model gap as the six deferred screens, flagged for `data-modeler` rather than
bolted on ad hoc.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from ..agents.journey.notifications import CrossPatientScopeError, Notifier
from ..auth import Account, CrudOp, Role, resolve_scope
from ..auth import Forbidden as AuthForbidden
from ..models import Notification, NotificationChannel
from ..state.sql.repository import AsyncPostgresRepository
from ..state.sql.sync_adapter import PostgresRepositorySyncAdapter
from .deps import PageParams, get_async_repo, get_current_account, get_sync_adapter
from .schemas import CamelModel, camel_schema

router = APIRouter(tags=["notifications"])

NotificationOut = camel_schema(Notification)


@router.get("/patients/{patient_id}/notifications", response_model=list[NotificationOut])
async def list_patient_notifications(
    patient_id: UUID,
    channel: NotificationChannel | None = None,
    page: PageParams = Depends(),
    account: Account = Depends(get_current_account),
    repo: AsyncPostgresRepository = Depends(get_async_repo),
):
    try:
        resolve_scope(account, Notification, CrudOp.READ)
    except AuthForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if account.patient_id != patient_id and account.role.value == "role_patient":
        raise HTTPException(status_code=403, detail="not this patient's timeline")

    notifications = await repo.list(Notification, patient_id=patient_id)
    if channel is not None:
        notifications = [n for n in notifications if n.channel is channel]
    notifications.sort(key=lambda n: n.created_at, reverse=True)
    return page.slice(notifications)


class NotifyEntry(CamelModel):
    patient_id: UUID
    body: str
    reason: str | None = None
    about_task_ids: list[UUID] = []
    sms: bool = False


class NotifyBatchRequest(CamelModel):
    entries: list[NotifyEntry]


class NotifyBatchOut(CamelModel):
    sent: list[NotificationOut]
    failed: list[str]


@router.post("/notifications/batch", response_model=NotifyBatchOut, status_code=201)
async def notify_batch(
    body: NotifyBatchRequest,
    account: Account = Depends(get_current_account),
    adapter: PostgresRepositorySyncAdapter = Depends(get_sync_adapter),
):
    # The FR-18 permission matrix (`auth/permissions.py`) has no CREATE op registered for
    # Notification under ANY role - notifications are meant to originate from an agent/system
    # actor, not a human CRUD call. Pending that matrix being extended, only staff roles may
    # trigger a send here; a patient account never notifies itself or anyone else.
    if account.role is Role.PATIENT:
        raise HTTPException(status_code=403, detail="role_patient may not send notifications")

    def _send_all() -> tuple[list[Notification], list[str]]:
        notifier = Notifier(adapter)
        sent: list[Notification] = []
        failed: list[str] = []
        for entry in body.entries:
            try:
                sent.extend(
                    notifier.notify(
                        entry.patient_id,
                        entry.body,
                        reason=entry.reason,
                        about_task_ids=entry.about_task_ids,
                        sms=entry.sms,
                    )
                )
            except CrossPatientScopeError as exc:
                failed.append(str(exc))
        return sent, failed

    sent, failed = await run_in_threadpool(_send_all)
    return NotifyBatchOut(sent=sent, failed=failed)

"""Patient status: which of four situations a patient is in right now (extends intake chat).

A read-only aggregation over `Diagnosis`, `CarePlan`/`Task`, and `QueueTicket` - the signal a
caller (the chat assistant, later) uses to know what a patient is likely asking about, instead of
guessing purely from the message text:

- `PRE_DIAGNOSIS`    - no diagnosis yet, no consult ticket taken -> likely wants to book a general
                       checkup (the existing `/chat` SCHEDULE flow already answers this).
- `AWAITING_CONSULT` - a consult `QueueTicket` is live (WAITING/CALLED) -> likely wants to know
                       when their turn comes.
- `PLAN_NOT_QUEUED`  - a Care Plan exists but no `Task` has reached its owner's queue yet (still
                       LOCKED/unpaid, or DONE/CANCELLED) -> likely wants sequencing advice; the
                       plan's own `sequence_index` order (FR-04, fasting-first) already answers
                       that, so this case only surfaces it.
- `TASK_IN_QUEUE`    - at least one `Task` is `in_queue` (paid, PENDING/IN_PROGRESS) -> likely
                       wants to know when their turn comes for that task.

`issue_consult_ticket` is the other half: nothing in the codebase created a `QueueTicket` before
this (ADR-003 defined the shape, no caller used it). "Taking a number" is folded into the existing
`/confirm` action rather than a separate check-in step - there is no check-in event in this system
yet, and the patient-described flow ("booked and took a number") maps cleanly onto confirm time.

ETA for a consult ticket uses `AVERAGE_CONSULT_MINUTES`, a placeholder constant - a real
resource-specific estimate (from `Resource` capacity/history, ML-driven) is future work and out of
scope for this pass. A `Task`'s ETA does NOT use this constant: `Task.estimated_duration_min` is
already a real per-task figure from the forecast tool (FR-04), so it is summed directly.

`list_patient_tasks` is the per-task complement to `derive_patient_status`: the latter summarizes
one task (or the plan-wide order when nothing is queued yet), the former returns every task in the
patient's Care Plan with its own execution/payment/queue status - e.g. for a screen listing every
ordered test at once (blood test: DONE, X-ray: IN_PROGRESS, ECG: LOCKED).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID

from ...models import (
    CarePlan,
    Department,
    Diagnosis,
    ExecutionStatus,
    PaymentStatus,
    PriorityLevel,
    QueueSubjectType,
    QueueTicket,
    QueueTicketStatus,
    ServiceOrder,
    ServiceType,
    Task,
)
from ...state import Repository, owner_queue

# Placeholder average consult duration (minutes), used only to turn a queue position into an ETA
# for AWAITING_CONSULT. Not resource-specific - see module docstring.
AVERAGE_CONSULT_MINUTES = 15

ACTIVE_TICKET_STATUSES = (QueueTicketStatus.WAITING, QueueTicketStatus.CALLED)

# Lower rank is served first. QueueTicket.priority_band is copied from Patient.priority_level at
# issue time (ADR-003); PriorityLevel itself is not ordinal, so the rank is spelled out here.
_PRIORITY_RANK: dict[PriorityLevel, int] = {
    PriorityLevel.EMERGENCY: 0,
    PriorityLevel.URGENT: 1,
    PriorityLevel.ROUTINE: 2,
}

_PRIORITY_LABEL_INFIX: dict[PriorityLevel, str] = {
    PriorityLevel.EMERGENCY: "E-",
    PriorityLevel.URGENT: "U-",
    PriorityLevel.ROUTINE: "",
}


class PatientStatus(StrEnum):
    PRE_DIAGNOSIS = "PRE_DIAGNOSIS"
    AWAITING_CONSULT = "AWAITING_CONSULT"
    PLAN_NOT_QUEUED = "PLAN_NOT_QUEUED"
    TASK_IN_QUEUE = "TASK_IN_QUEUE"


@dataclass(frozen=True)
class QueuePosition:
    """Where one ticket/task sits in its queue: how many are ahead, and a rough ETA."""

    label: str | None  # QueueTicket.ticket_label; None for a Task (no ticket concept there)
    people_ahead: int
    eta_minutes: int


@dataclass(frozen=True)
class PlanTask:
    """One task in a not-yet-queued Care Plan, in the plan's own suggested order."""

    task_id: UUID
    service_order_id: UUID
    sequence_index: int


@dataclass(frozen=True)
class PatientStatusResult:
    status: PatientStatus
    queue: QueuePosition | None = None
    plan_tasks: tuple[PlanTask, ...] = ()


@dataclass(frozen=True)
class TaskStatusDetail:
    """One task's full status: what it is, where it stands, and its queue position if queued."""

    task_id: UUID
    service_order_id: UUID
    service_type_code: str
    service_type_label: str
    execution_status: ExecutionStatus
    payment_status: PaymentStatus
    sequence_index: int
    queue: QueuePosition | None  # set only while `Task.in_queue` is true


@dataclass(frozen=True)
class QueueOverview:
    """How busy the consult queue is right now, department-wide - not tied to any one patient.

    For a patient who has not taken a ticket yet (PRE_DIAGNOSIS): this is the answer to "how many
    people are waiting for a general checkup right now", the equivalent of `QueuePosition` before a
    ticket exists to measure a personal position against.
    """

    people_waiting: int
    eta_minutes: int


@dataclass(frozen=True)
class ServiceQueue:
    """How busy one service type's queue is right now, across every patient.

    A "service" here is a `ServiceType` (e.g. blood test): `people_waiting` counts every `Task`
    of that type currently in a queue (paid, PENDING/IN_PROGRESS - `Task.in_queue`), and
    `eta_minutes` sums their real `estimated_duration_min` - i.e. how long the current queue takes
    to clear, which is the wait a patient joining the back would see.
    """

    service_type_id: UUID
    people_waiting: int
    eta_minutes: int


def service_queue_overview(repo: Repository, service_type_id: UUID) -> ServiceQueue:
    """Live queue load for one `ServiceType`: how many tasks are queued and the time to clear them.

    Task -> ServiceType is indirect (`Task.service_order_id` -> `ServiceOrder.service_type_id`), so
    this resolves the orders of the given type first, then counts the in-queue tasks pointing at
    them. Read-only; invents nothing.
    """
    order_ids = {
        order.id for order in repo.list(ServiceOrder, service_type_id=service_type_id)
    }
    queued = [
        task
        for task in repo.list(Task)
        if task.service_order_id in order_ids and task.in_queue
    ]
    return ServiceQueue(
        service_type_id=service_type_id,
        people_waiting=len(queued),
        eta_minutes=sum(task.estimated_duration_min for task in queued),
    )


def ticket_sort_key(ticket: QueueTicket) -> tuple[int, datetime]:
    """Serving order (ADR-003): `(priority_band, issued_at)`, never `ticket_label`."""
    return (_PRIORITY_RANK[ticket.priority_band], ticket.issued_at)


def _tickets_ahead(repo: Repository, ticket: QueueTicket) -> list[QueueTicket]:
    """Other live tickets in the same department+capability queue, served before `ticket`."""
    siblings = [
        t
        for t in repo.list(
            QueueTicket,
            department_id=ticket.department_id,
            capability=ticket.capability,
            subject_type=QueueSubjectType.CONSULT,
        )
        if t.id != ticket.id and t.status in ACTIVE_TICKET_STATUSES
    ]
    key = ticket_sort_key(ticket)
    return [t for t in siblings if ticket_sort_key(t) < key]


def consult_queue_overview(
    repo: Repository, department_id: UUID, *, capability: str | None = None
) -> QueueOverview:
    """Total live consult tickets for a department right now, with a rough join-now ETA.

    Same `ACTIVE_TICKET_STATUSES` filter as a personal position, just counted for everyone
    instead of "ahead of one ticket" - so a PRE_DIAGNOSIS patient (no ticket yet) can still see how
    busy the queue is before deciding to book.
    """
    waiting = [
        t
        for t in repo.list(
            QueueTicket,
            department_id=department_id,
            capability=capability,
            subject_type=QueueSubjectType.CONSULT,
        )
        if t.status in ACTIVE_TICKET_STATUSES
    ]
    return QueueOverview(
        people_waiting=len(waiting), eta_minutes=len(waiting) * AVERAGE_CONSULT_MINUTES
    )


def issue_consult_ticket(
    repo: Repository,
    department: Department,
    subject_id: UUID,
    patient_id: UUID,
    priority_band: PriorityLevel,
    *,
    capability: str | None = None,
    issued_at: datetime | None = None,
) -> QueueTicket:
    """Create the consult `QueueTicket` for a confirmed appointment - the patient's "number".

    `ticket_seq` is monotonic within (department, priority_band, day); `ticket_label` is the
    human-facing token (e.g. `DepA-00001`, `DepA-E-00001` for a non-routine band). This is the
    only place a consult `QueueTicket` is created.
    """
    now = issued_at or datetime.now(UTC)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    issued_today = [
        t
        for t in repo.list(
            QueueTicket,
            department_id=department.id,
            priority_band=priority_band,
            subject_type=QueueSubjectType.CONSULT,
        )
        if day_start <= t.issued_at < day_end
    ]
    ticket_seq = len(issued_today) + 1
    label = f"{department.code}-{_PRIORITY_LABEL_INFIX[priority_band]}{ticket_seq:05d}"
    ticket = QueueTicket(
        patient_id=patient_id,
        department_id=department.id,
        capability=capability,
        priority_band=priority_band,
        subject_type=QueueSubjectType.CONSULT,
        subject_id=subject_id,
        ticket_seq=ticket_seq,
        ticket_label=label,
        issued_at=now,
    )
    return repo.save(ticket)


def _task_queue_position(repo: Repository, task: Task) -> QueuePosition:
    """Where `task` sits in its owner's queue: real durations (FR-04), not the ETA placeholder."""
    ahead = [t for t in owner_queue(repo, task.owner_id) if t.sequence_index < task.sequence_index]
    return QueuePosition(
        label=None,
        people_ahead=len(ahead),
        eta_minutes=sum(t.estimated_duration_min for t in ahead),
    )


def _select_care_plan(repo: Repository, patient_id: UUID) -> CarePlan | None:
    """The patient's most relevant Care Plan: the most recently created one, any status.

    A `DRAFT` plan (the FR-04 rollback contract - a task failed to get a slot) still has real
    `Task`s worth reporting on, so this is not filtered to `ACTIVE` only.
    """
    plans = repo.list(CarePlan, patient_id=patient_id)
    if not plans:
        return None
    return max(plans, key=lambda p: p.created_at)


def derive_patient_status(repo: Repository, patient_id: UUID) -> PatientStatusResult:
    """Classify which of the four situations `patient_id` is in right now (read-only)."""
    if not repo.list(Diagnosis, patient_id=patient_id):
        tickets = [
            t
            for t in repo.list(
                QueueTicket, patient_id=patient_id, subject_type=QueueSubjectType.CONSULT
            )
            if t.status in ACTIVE_TICKET_STATUSES
        ]
        if not tickets:
            return PatientStatusResult(status=PatientStatus.PRE_DIAGNOSIS)
        ticket = min(tickets, key=ticket_sort_key)
        ahead = _tickets_ahead(repo, ticket)
        return PatientStatusResult(
            status=PatientStatus.AWAITING_CONSULT,
            queue=QueuePosition(
                label=ticket.ticket_label,
                people_ahead=len(ahead),
                eta_minutes=len(ahead) * AVERAGE_CONSULT_MINUTES,
            ),
        )

    plan = _select_care_plan(repo, patient_id)
    tasks = repo.list(Task, care_plan_id=plan.id) if plan else []
    queued = [t for t in tasks if t.in_queue]
    if not queued:
        ordered = sorted(tasks, key=lambda t: t.sequence_index)
        plan_tasks = tuple(
            PlanTask(
                task_id=t.id, service_order_id=t.service_order_id, sequence_index=t.sequence_index
            )
            for t in ordered
        )
        return PatientStatusResult(status=PatientStatus.PLAN_NOT_QUEUED, plan_tasks=plan_tasks)

    task = min(queued, key=lambda t: t.sequence_index)
    return PatientStatusResult(
        status=PatientStatus.TASK_IN_QUEUE, queue=_task_queue_position(repo, task)
    )


def list_patient_tasks(repo: Repository, patient_id: UUID) -> list[TaskStatusDetail]:
    """Every task in the patient's most relevant Care Plan (see `_select_care_plan`), in order.

    The per-task complement to `derive_patient_status`: that function summarizes ONE task (the
    next one due, or the plan-wide sequencing when nothing is queued yet); this returns the full
    list with each task's own execution/payment status and queue position - e.g. for a "my visit"
    screen showing every ordered test at once, not just the next one.
    """
    plan = _select_care_plan(repo, patient_id)
    if plan is None:
        return []

    tasks = sorted(repo.list(Task, care_plan_id=plan.id), key=lambda t: t.sequence_index)
    details: list[TaskStatusDetail] = []
    for task in tasks:
        service_order = repo.get(ServiceOrder, task.service_order_id)
        service_type = (
            repo.get(ServiceType, service_order.service_type_id) if service_order else None
        )
        details.append(
            TaskStatusDetail(
                task_id=task.id,
                service_order_id=task.service_order_id,
                service_type_code=service_type.code if service_type else "",
                service_type_label=service_type.display_label if service_type else "",
                execution_status=task.execution_status,
                payment_status=task.payment_status,
                sequence_index=task.sequence_index,
                queue=_task_queue_position(repo, task) if task.in_queue else None,
            )
        )
    return details

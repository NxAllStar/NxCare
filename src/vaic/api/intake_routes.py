"""HTTP surface for the patient assistant: one chat endpoint, plus confirm.

A single `/chat` turn drives everything (there is no separate triage/slot endpoint any more): the
patient's message is untrusted DATA (NFR-SEC-11), a deterministic red-flag check gates emergencies
(BF-05), and otherwise the assistant agent decides intent - it suggests the least-crowded arrival
times when the patient is asking *when to come*, and just replies normally otherwise. Reservation
data is retrieved from the store in code (`summarize_reservations`) and the agent reasons over it
(grounding contract); the model never invents counts and its output is schema-validated before use.

The assistant uses the real `HttpArrivalChatLLM` (OpenAI-compatible against `LLM_API_BASE_URL`) when
a provider is configured, else a deterministic fallback - "real agent when configured, safe
deterministic behaviour otherwise" (ai-governance.md). `/confirm` logs the patient's accepted time
and, in the same call, "takes a number": it issues the consult `QueueTicket` (ADR-003) for the new
appointment, so `/status` can later answer "when is my turn". `/status` is a read-only lookup of
which of four situations a patient is in (pre-diagnosis, awaiting consult, plan not queued yet, or
a task in queue); `/queue` is the department-wide equivalent for a patient who has not taken a
number yet; `/tasks` lists every task in the patient's Care Plan with its own status, once a
diagnosis has produced one - see `agents/intake/patient_status.py`.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from ..agents.intake.arrival import confirm_arrival_slot, summarize_reservations
from ..agents.intake.arrival_chat import respond_to_chat
from ..agents.intake.arrival_llm_client import build_arrival_chat_llm
from ..agents.intake.emergency import detect_emergency
from ..agents.intake.patient_status import (
    consult_queue_overview,
    derive_patient_status,
    issue_consult_ticket,
    list_patient_tasks,
    service_queue_overview,
)
from ..agents.intake.task_order import collect_service_queues, suggest_task_order
from ..agents.intake.task_order_llm_client import build_task_order_llm
from ..models import Department, Patient, PriorityLevel, ServiceType
from ..state import Repository
from .demo_state import ARRIVAL_DEMO_ANCHOR, ARRIVAL_DEMO_DAYS, ARRIVAL_DEPARTMENT_ID

logger = logging.getLogger(__name__)

_DEFAULT_SPECIALTY = "GENERAL_MEDICINE"

_EMERGENCY_REPLY = (
    "The symptoms you describe may be an emergency. Please contact a medical staff member now or "
    "call emergency services - I can't schedule a routine visit in this case."
)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str  # the patient's message; untrusted content, used as DATA only


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    sender: str
    text: str
    createdAt: str
    aiGenerated: bool


class ArrivalBlockOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str  # YYYY-MM-DD
    startHour: int
    endHour: int
    reservationCount: int
    reason: str


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply: ChatMessageOut  # the agent's natural-language answer
    intent: str  # "SCHEDULE" | "CHAT" | "EMERGENCY"
    recommendations: list[ArrivalBlockOut]  # time blocks (empty unless intent == SCHEDULE)
    emergencySuspected: bool


class ConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patientId: str
    start: str  # ISO datetime of the accepted time
    specialty: str | None = None  # optional; a time-block arrival is not specialty-bound yet
    ownerId: str | None = None  # optional; the doctor is assigned at the desk on arrival


class ConfirmResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appointmentId: str
    ownerId: str | None
    start: str
    status: str
    ticketLabel: str  # the consult queue number just issued, e.g. "DepA-00001"
    patientCode: str  # the patient's scannable code (FR-17), created here if it did not exist


class QueuePositionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None  # the QueueTicket's label; null when the position is a Task, not a ticket
    peopleAhead: int
    etaMinutes: int


class PlanTaskOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    taskId: str
    serviceOrderId: str
    sequenceIndex: int


class PatientStatusOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str  # PRE_DIAGNOSIS | AWAITING_CONSULT | PLAN_NOT_QUEUED | TASK_IN_QUEUE
    queue: QueuePositionOut | None  # set for AWAITING_CONSULT and TASK_IN_QUEUE
    planTasks: list[PlanTaskOut]  # set for PLAN_NOT_QUEUED, in the plan's own suggested order


class QueueOverviewOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    peopleWaiting: int  # everyone currently WAITING/CALLED for a general checkup, not per-patient
    etaMinutes: int


class TaskStatusOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    taskId: str
    serviceOrderId: str
    serviceTypeCode: str  # e.g. "BLOOD_TEST"; empty string if the ServiceType could not be found
    serviceTypeLabel: str  # human-readable, e.g. "Blood Test"
    executionStatus: str  # LOCKED | PENDING | IN_PROGRESS | DONE | CANCELLED
    paymentStatus: str  # UNPAID | PAID
    sequenceIndex: int
    queue: QueuePositionOut | None  # set only while the task is in_queue (paid, not yet finished)


class TaskListOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: list[TaskStatusOut]  # every task in the patient's Care Plan, in sequence order


class ServiceQueueOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    serviceTypeId: str
    peopleWaiting: int  # tasks of this service type currently in a queue (paid, not finished)
    etaMinutes: int  # time to clear that queue (sum of their estimated durations)


class OrderedServiceOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    taskId: str
    serviceTypeCode: str
    serviceTypeLabel: str
    peopleWaiting: int
    etaMinutes: int
    reason: str  # why this service is placed here in the order


class SuggestTaskOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patientId: str


class TaskOrderOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str  # patient-facing summary of the suggested order
    order: list[OrderedServiceOut]  # the services to do, in the suggested order


def build_intake_router(repo: Repository) -> APIRouter:
    """Bind the demo `Repository` into the router's closure - one repo instance per running app.

    The router is constructed here (not a module-global) so each call returns an independent router
    bound to its own repo; a shared global would re-register routes and leak repos across callers.
    """
    router = APIRouter(prefix="/api/intake", tags=["intake"])
    assistant_llm = build_arrival_chat_llm()  # real client when configured, else deterministic
    task_order_llm = build_task_order_llm()  # same: real provider when configured, else rule-based

    @router.post("/chat", response_model=ChatResponse)
    def chat(body: ChatRequest) -> ChatResponse:
        """One chat turn: emergency-gate, then the agent replies (and suggests times on intent)."""
        now = datetime.now(UTC).isoformat()

        def _message(text: str) -> ChatMessageOut:
            return ChatMessageOut(
                id=str(uuid4()), sender="agent", text=text, createdAt=now, aiGenerated=True
            )

        # Safety gate first (BF-05): a red-flag message is never answered with a scheduling
        # suggestion. Deterministic check on the raw text - no LLM needed to refuse an emergency.
        if detect_emergency(body.text, PriorityLevel.ROUTINE):
            return ChatResponse(
                reply=_message(_EMERGENCY_REPLY),
                intent="EMERGENCY",
                recommendations=[],
                emergencySuspected=True,
            )

        # Grounding: search the store for reservations vs working hours (code), then the agent
        # reasons over that summary and decides intent itself.
        summary = summarize_reservations(repo, ARRIVAL_DEMO_ANCHOR, ARRIVAL_DEMO_DAYS)
        reply = respond_to_chat(body.text, summary, assistant_llm)
        logger.info("assistant intent=%s blocks=%d", reply.intent, len(reply.recommendations))

        return ChatResponse(
            reply=_message(reply.message),
            intent=reply.intent,
            recommendations=[
                ArrivalBlockOut(
                    date=block.date,
                    startHour=block.start_hour,
                    endHour=block.end_hour,
                    reservationCount=block.reservation_count,
                    reason=block.reason,
                )
                for block in reply.recommendations
            ],
            emergencySuspected=False,
        )

    @router.post("/confirm", response_model=ConfirmResponse)
    def confirm(body: ConfirmRequest) -> ConfirmResponse:
        """Log the patient's accepted time (PROPOSED Appointment) and issue their queue number."""
        try:
            patient_id = UUID(body.patientId)
            owner_id = UUID(body.ownerId) if body.ownerId else None
            start = datetime.fromisoformat(body.start)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid id or datetime") from exc

        appointment = confirm_arrival_slot(
            repo, patient_id, body.specialty or _DEFAULT_SPECIALTY, start, owner_id
        )

        # Ensure a Patient record exists: the scan step (FR-17) needs a scannable `patient_code`,
        # and priority_band on the ticket is copied from it. Get-or-create so a repeat confirm keeps
        # the same code. A real intake would create the Patient earlier; the demo does it here.
        patient = repo.get(Patient, patient_id)
        if patient is None:
            patient = repo.save(
                Patient(
                    id=patient_id,
                    full_name="",  # PII - not collected in this demo flow (NFR-SEC-01)
                    patient_code=f"P-{uuid4().hex[:8].upper()}",
                )
            )

        # "Taking a number": issue the consult QueueTicket in the same call (there is no separate
        # check-in step yet) so /status can answer "when is my turn" right away.
        department = repo.get(Department, ARRIVAL_DEPARTMENT_ID)
        if department is None:
            raise HTTPException(status_code=500, detail="arrival department not seeded")
        ticket = issue_consult_ticket(
            repo, department, appointment.id, patient_id, patient.priority_level
        )

        return ConfirmResponse(
            appointmentId=str(appointment.id),
            ownerId=str(appointment.owner_id) if appointment.owner_id else None,
            start=appointment.slot_start.isoformat(),
            status=appointment.status.value,
            ticketLabel=ticket.ticket_label,
            patientCode=patient.patient_code,
        )

    @router.get("/queue", response_model=QueueOverviewOut)
    def queue_overview() -> QueueOverviewOut:
        """How many people are waiting for a general checkup right now (no patient needed).

        For a PRE_DIAGNOSIS patient - no ticket taken yet, so there is no personal position to
        report - this is the "how busy is it" check before they book (see AWAITING_CONSULT's
        `peopleAhead` on `/status` for the personal-position equivalent once they have a ticket).
        """
        department = repo.get(Department, ARRIVAL_DEPARTMENT_ID)
        if department is None:
            raise HTTPException(status_code=500, detail="arrival department not seeded")

        overview = consult_queue_overview(repo, department.id)
        return QueueOverviewOut(
            peopleWaiting=overview.people_waiting, etaMinutes=overview.eta_minutes
        )

    @router.get("/status/{patient_id}", response_model=PatientStatusOut)
    def status(patient_id: str) -> PatientStatusOut:
        """Which of the four situations the patient is in right now (read-only, no LLM call)."""
        try:
            pid = UUID(patient_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid patient id") from exc

        result = derive_patient_status(repo, pid)
        return PatientStatusOut(
            status=result.status.value,
            queue=(
                QueuePositionOut(
                    label=result.queue.label,
                    peopleAhead=result.queue.people_ahead,
                    etaMinutes=result.queue.eta_minutes,
                )
                if result.queue is not None
                else None
            ),
            planTasks=[
                PlanTaskOut(
                    taskId=str(task.task_id),
                    serviceOrderId=str(task.service_order_id),
                    sequenceIndex=task.sequence_index,
                )
                for task in result.plan_tasks
            ],
        )

    @router.get("/tasks/{patient_id}", response_model=TaskListOut)
    def tasks(patient_id: str) -> TaskListOut:
        """Every task in the patient's Care Plan, each with its own status and queue position."""
        try:
            pid = UUID(patient_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid patient id") from exc

        details = list_patient_tasks(repo, pid)
        return TaskListOut(
            tasks=[
                TaskStatusOut(
                    taskId=str(detail.task_id),
                    serviceOrderId=str(detail.service_order_id),
                    serviceTypeCode=detail.service_type_code,
                    serviceTypeLabel=detail.service_type_label,
                    executionStatus=detail.execution_status.value,
                    paymentStatus=detail.payment_status.value,
                    sequenceIndex=detail.sequence_index,
                    queue=(
                        QueuePositionOut(
                            label=detail.queue.label,
                            peopleAhead=detail.queue.people_ahead,
                            etaMinutes=detail.queue.eta_minutes,
                        )
                        if detail.queue is not None
                        else None
                    ),
                )
                for detail in details
            ]
        )

    @router.get("/service-queue/{service_type_id}", response_model=ServiceQueueOut)
    def service_queue(service_type_id: str) -> ServiceQueueOut:
        """How many people are queued for one service type right now, and the time to clear it."""
        try:
            stid = UUID(service_type_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid service type id") from exc
        if repo.get(ServiceType, stid) is None:
            raise HTTPException(status_code=404, detail="unknown service type")

        overview = service_queue_overview(repo, stid)
        return ServiceQueueOut(
            serviceTypeId=str(stid),
            peopleWaiting=overview.people_waiting,
            etaMinutes=overview.eta_minutes,
        )

    @router.post("/suggest-task-order", response_model=TaskOrderOut)
    def suggest_order(body: SuggestTaskOrderRequest) -> TaskOrderOut:
        """Suggest an order for the patient's remaining services, grounded in live queue load.

        Retrieves each remaining service's queue (in code), then the agent proposes an order the
        patient can follow to wait the least; a deterministic shortest-wait-first order is the
        fallback when no provider is configured or the model answers off-schema.
        """
        try:
            pid = UUID(body.patientId)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid patient id") from exc

        # The queue info per task, keyed for enriching the agent's ordered result (which only
        # carries task_id + reason) with the counts we retrieved.
        info_by_task = {str(info.task_id): info for info in collect_service_queues(repo, pid)}
        suggestion = suggest_task_order(repo, pid, task_order_llm)

        ordered: list[OrderedServiceOut] = []
        for entry in suggestion.order:
            info = info_by_task.get(entry.task_id)
            ordered.append(
                OrderedServiceOut(
                    taskId=entry.task_id,
                    serviceTypeCode=info.service_type_code if info else entry.service_type_code,
                    serviceTypeLabel=info.service_type_label if info else "",
                    peopleWaiting=info.people_waiting if info else 0,
                    etaMinutes=info.eta_minutes if info else 0,
                    reason=entry.reason,
                )
            )
        return TaskOrderOut(message=suggestion.message, order=ordered)

    return router

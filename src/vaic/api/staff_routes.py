"""HTTP surface for the front desk / doctor side of the consult queue.

The write side of `intake_routes.py`'s patient-facing reads: a doctor calls the next waiting
patient, records the finished visit's outcome (diagnosis + ordered tests -> tasks) and closes it,
or puts a called-but-absent patient back in the queue. The queue transitions route through
`agents/intake/consult_desk.py`; recording the consult outcome routes through
`agents/careplan/consult_outcome.py` (FR-03 + FR-04). This module only translates HTTP <-> those.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from ..agents.careplan.consult_outcome import (
    ConsultOutcomeError,
    build_consult_outcome_executor,
    record_consult_outcome,
)
from ..agents.careplan.gate import build_confirm_payment_tool
from ..agents.core import ActionExecutor
from ..agents.intake.consult_desk import (
    ConsultDeskError,
    call_next_patient,
    complete_appointment,
    requeue_no_show,
)
from ..agents.journey.scan import register_journey_tools
from ..agents.journey.task_completion import build_complete_task_tool
from ..models import InvalidTransition, ServiceType, Task
from ..state import Repository
from ..tools import Action, AuditLog, ConstraintChecker, ToolRegistry
from .demo_state import ARRIVAL_DEPARTMENT_ID

# Default trusted actor role for the payment gate until FR-18/TASK-031 binds it to an authenticated
# session. `is_authorised_payment_confirmer` accepts role_staff / role_coordinator (BR-11).
_DEFAULT_PAYMENT_ROLE = "role_staff"


class CallNextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ownerId: str  # the calling doctor - a Resource id


class CallNextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticketId: str
    ticketLabel: str
    patientId: str
    appointmentId: str
    ownerId: str


class CompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # All optional: a visit can close with no diagnosis (nothing found, no tests). When any of
    # conditions/serviceTypeIds is present, diagnosedBy is required (who signed the diagnosis).
    diagnosedBy: str | None = None  # the diagnosing doctor - a Resource id
    conditions: list[str] = []
    serviceTypeIds: list[str] = []  # the ordered tests -> one Task each (FR-03 -> FR-04)


class ConsultOutcomeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagnosisId: str
    carePlanId: str
    taskIds: list[str]


class AppointmentStatusOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appointmentId: str
    status: str
    outcome: ConsultOutcomeOut | None  # set when the visit was closed with a diagnosis recorded


class TicketStatusOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticketId: str
    ticketLabel: str
    status: str


class ServiceTypeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    code: str
    label: str
    defaultDurationMin: int


class ServiceTypeListOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    serviceTypes: list[ServiceTypeOut]


class ConfirmPaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmedBy: str  # the authorised staff/system source (Payment.confirmed_by, BR-36)
    actorRole: str | None = None  # defaults to role_staff; must be an authorised source (BR-11)


class ScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scannedBy: str  # must be the task owner (BR-26)
    patientCode: str  # the scanned code; validated against the task's patient (FR-17)


class CompleteTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completedBy: str  # must be the task owner (BR-26)


class TaskStateOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    taskId: str
    executionStatus: str
    paymentStatus: str


def build_staff_router(repo: Repository) -> APIRouter:
    """Bind the demo `Repository` into the router's closure - same pattern as
    `build_intake_router`."""
    router = APIRouter(prefix="/api/staff", tags=["staff"])

    @router.post("/queue/call-next", response_model=CallNextResponse)
    def call_next(body: CallNextRequest) -> CallNextResponse:
        """Call the next waiting patient in the general-checkup queue for `ownerId` to see."""
        try:
            owner_id = UUID(body.ownerId)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid owner id") from exc

        try:
            called = call_next_patient(repo, ARRIVAL_DEPARTMENT_ID, owner_id)
        except ConsultDeskError as exc:
            # A ticket whose Appointment no longer resolves is a data-integrity defect, not an
            # expected outcome - surfaced as 500 rather than left to crash unhandled.
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        if called is None:
            raise HTTPException(status_code=404, detail="no patient waiting")
        return CallNextResponse(
            ticketId=str(called.ticket_id),
            ticketLabel=called.ticket_label,
            patientId=str(called.patient_id),
            appointmentId=str(called.appointment_id),
            ownerId=str(called.owner_id),
        )

    @router.post("/appointments/{appointment_id}/complete", response_model=AppointmentStatusOut)
    def complete(appointment_id: str, body: CompleteRequest | None = None) -> AppointmentStatusOut:
        """Finish a called-in visit: record its outcome (if any), then close it (DONE).

        The visit's outcome is the diagnosis and the tests ordered from it (FR-03), which become
        the patient's tasks (FR-04). The body is optional: a visit with nothing to diagnose closes
        with just a status change. When a diagnosis IS recorded, it happens BEFORE the close, so a
        capture failure (unknown service, non-doctor actor) leaves the visit open, not half-closed.
        """
        try:
            appt_id = UUID(appointment_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid appointment id") from exc

        body = body or CompleteRequest()
        recording = bool(body.conditions or body.serviceTypeIds)
        outcome_out: ConsultOutcomeOut | None = None
        if recording:
            if not body.diagnosedBy:
                raise HTTPException(
                    status_code=422, detail="diagnosedBy is required when recording a diagnosis"
                )
            try:
                diagnosed_by = UUID(body.diagnosedBy)
                service_type_ids = [UUID(sid) for sid in body.serviceTypeIds]
            except ValueError as exc:
                raise HTTPException(status_code=422, detail="invalid id in request") from exc

            outcome_executor = build_consult_outcome_executor(repo)
            try:
                outcome = record_consult_outcome(
                    repo,
                    outcome_executor,
                    appointment_id=appt_id,
                    conditions=body.conditions,
                    diagnosed_by=diagnosed_by,
                    service_type_ids=service_type_ids,
                )
            except ConsultOutcomeError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            outcome_out = ConsultOutcomeOut(
                diagnosisId=str(outcome.diagnosis_id),
                carePlanId=str(outcome.care_plan_id),
                taskIds=[str(tid) for tid in outcome.task_ids],
            )

        try:
            appointment = complete_appointment(repo, appt_id)
        except ConsultDeskError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidTransition as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        return AppointmentStatusOut(
            appointmentId=str(appointment.id), status=appointment.status.value, outcome=outcome_out
        )

    @router.get("/service-types", response_model=ServiceTypeListOut)
    def service_types() -> ServiceTypeListOut:
        """The orderable tests a doctor can put on a diagnosis (for the console's order picker)."""
        types = sorted(repo.list(ServiceType), key=lambda st: st.code)
        return ServiceTypeListOut(
            serviceTypes=[
                ServiceTypeOut(
                    id=str(st.id),
                    code=st.code,
                    label=st.display_label,
                    defaultDurationMin=st.default_duration_min,
                )
                for st in types
            ]
        )

    @router.post("/queue/{ticket_id}/requeue", response_model=TicketStatusOut)
    def requeue(ticket_id: str) -> TicketStatusOut:
        """The called patient did not show: put the same ticket back to WAITING (fresh number)."""
        try:
            tid = UUID(ticket_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid ticket id") from exc

        try:
            ticket = requeue_no_show(repo, tid)
        except ConsultDeskError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidTransition as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        return TicketStatusOut(
            ticketId=str(ticket.id), ticketLabel=ticket.ticket_label, status=ticket.status.value
        )

    def _run_task_action(tool: str, task_id: str, params: dict) -> Task:
        """Run a guarded task-mutating tool through the executor and return the updated Task.

        Maps the executor's ActionResult onto HTTP: an unknown task is 404; a constraint block or
        tool refusal (wrong state, unauthorised role, code mismatch) is 409 with the reason. The
        registry is built per call - cheap, and keeps each action's spine self-contained.
        """
        try:
            tid = UUID(task_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid task id") from exc
        if repo.get(Task, tid) is None:
            raise HTTPException(status_code=404, detail=f"no task {tid}")

        registry = ToolRegistry()
        registry.register(build_confirm_payment_tool())
        register_journey_tools(registry)  # scan_patient
        registry.register(build_complete_task_tool())
        executor = ActionExecutor(repo, registry, ConstraintChecker(repo), AuditLog(repo))

        result = executor.execute(
            Action(
                tool=tool, actor="staff-console", reasoning="", params={"task_id": tid, **params}
            )
        )
        if not result.ok:
            raise HTTPException(status_code=409, detail=result.reason)
        task = repo.get(Task, tid)
        assert task is not None  # just mutated by the tool above
        return task

    @router.post("/tasks/{task_id}/confirm-payment", response_model=TaskStateOut)
    def confirm_payment(task_id: str, body: ConfirmPaymentRequest) -> TaskStateOut:
        """Proceed gate (FR-05): mark a task's payment PAID, unlocking it LOCKED -> PENDING."""
        try:
            confirmed_by = UUID(body.confirmedBy)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid confirmedBy id") from exc

        task = _run_task_action(
            "confirm_payment",
            task_id,
            {
                "actor_role": body.actorRole or _DEFAULT_PAYMENT_ROLE,
                "confirmed_by": confirmed_by,
            },
        )
        return TaskStateOut(
            taskId=str(task.id),
            executionStatus=task.execution_status.value,
            paymentStatus=task.payment_status.value,
        )

    @router.post("/tasks/{task_id}/scan", response_model=TaskStateOut)
    def scan(task_id: str, body: ScanRequest) -> TaskStateOut:
        """Patient-code scan (FR-17): the owner scans the patient in, PENDING -> IN_PROGRESS."""
        try:
            scanned_by = UUID(body.scannedBy)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid scannedBy id") from exc

        task = _run_task_action(
            "scan_patient",
            task_id,
            {"scanned_by": scanned_by, "patient_code": body.patientCode},
        )
        return TaskStateOut(
            taskId=str(task.id),
            executionStatus=task.execution_status.value,
            paymentStatus=task.payment_status.value,
        )

    @router.post("/tasks/{task_id}/complete", response_model=TaskStateOut)
    def complete_task(task_id: str, body: CompleteTaskRequest) -> TaskStateOut:
        """Finish a task at its station (FR-06): the owner reports it done, IN_PROGRESS -> DONE."""
        try:
            completed_by = UUID(body.completedBy)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid completedBy id") from exc

        task = _run_task_action("complete_task", task_id, {"completed_by": completed_by})
        return TaskStateOut(
            taskId=str(task.id),
            executionStatus=task.execution_status.value,
            paymentStatus=task.payment_status.value,
        )

    return router

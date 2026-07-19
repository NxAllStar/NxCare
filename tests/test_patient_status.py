"""Tests for patient status derivation and consult-ticket issuance.

Covers the four status branches (`derive_patient_status`), the ticket-numbering rules
(`issue_consult_ticket`), the department-wide queue overview (`consult_queue_overview`), and the
per-task status list (`list_patient_tasks`) - all against `InMemoryRepository`, no network involved.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from vaic.agents.intake.patient_status import (
    AVERAGE_CONSULT_MINUTES,
    PatientStatus,
    consult_queue_overview,
    derive_patient_status,
    issue_consult_ticket,
    list_patient_tasks,
)
from vaic.models import (
    CarePlan,
    CarePlanStatus,
    Department,
    Diagnosis,
    ExecutionStatus,
    PaymentStatus,
    PriorityLevel,
    QueueSubjectType,
    QueueTicketStatus,
    ServiceOrder,
    ServiceType,
    Task,
)
from vaic.state import InMemoryRepository

ANCHOR = datetime(2026, 7, 20, 8, 0, tzinfo=UTC)


def _department(repo: InMemoryRepository, code: str = "DepA") -> Department:
    return repo.save(Department(code=code, display_label="General Medicine"))


def _service_order(repo, patient_id, diagnosis_id, *, code="BLOOD_TEST", label="Blood Test"):
    service_type = repo.save(ServiceType(code=code, display_label=label))
    return repo.save(
        ServiceOrder(
            patient_id=patient_id,
            diagnosis_id=diagnosis_id,
            service_type_id=service_type.id,
            ordered_by=uuid4(),
        )
    )


def _task(
    repo,
    care_plan_id,
    owner_id,
    *,
    sequence_index,
    execution_status,
    payment_status,
    duration=0,
    service_order_id=None,
):
    return repo.save(
        Task(
            care_plan_id=care_plan_id,
            service_order_id=service_order_id or uuid4(),
            owner_id=owner_id,
            execution_status=execution_status,
            payment_status=payment_status,
            estimated_duration_min=duration,
            sequence_index=sequence_index,
        )
    )


# ---- derive_patient_status: PRE_DIAGNOSIS --------------------------------------------------------


def test_pre_diagnosis_when_no_diagnosis_and_no_ticket():
    repo = InMemoryRepository()
    patient_id = uuid4()

    result = derive_patient_status(repo, patient_id)

    assert result.status is PatientStatus.PRE_DIAGNOSIS
    assert result.queue is None


# ---- derive_patient_status: AWAITING_CONSULT -----------------------------------------------------


def test_awaiting_consult_when_ticket_waiting():
    repo = InMemoryRepository()
    dept = _department(repo)
    patient_id = uuid4()
    ticket = issue_consult_ticket(
        repo, dept, uuid4(), patient_id, PriorityLevel.ROUTINE, issued_at=ANCHOR
    )

    result = derive_patient_status(repo, patient_id)

    assert result.status is PatientStatus.AWAITING_CONSULT
    assert result.queue is not None
    assert result.queue.label == ticket.ticket_label
    assert result.queue.people_ahead == 0
    assert result.queue.eta_minutes == 0


def test_awaiting_consult_counts_only_earlier_same_department_tickets():
    repo = InMemoryRepository()
    dept = _department(repo)
    patient_id = uuid4()
    # two routine tickets ahead in the same department, issued earlier
    issue_consult_ticket(repo, dept, uuid4(), uuid4(), PriorityLevel.ROUTINE, issued_at=ANCHOR)
    issue_consult_ticket(
        repo, dept, uuid4(), uuid4(), PriorityLevel.ROUTINE, issued_at=ANCHOR + timedelta(minutes=1)
    )
    issue_consult_ticket(
        repo,
        dept,
        uuid4(),
        patient_id,
        PriorityLevel.ROUTINE,
        issued_at=ANCHOR + timedelta(minutes=2),
    )
    # a ticket in a different department must not count
    other_dept = _department(repo, code="DepB")
    issue_consult_ticket(
        repo, other_dept, uuid4(), uuid4(), PriorityLevel.ROUTINE, issued_at=ANCHOR
    )

    result = derive_patient_status(repo, patient_id)

    assert result.queue.people_ahead == 2
    assert result.queue.eta_minutes == 2 * AVERAGE_CONSULT_MINUTES


def test_awaiting_consult_higher_priority_counts_ahead_even_if_issued_later():
    repo = InMemoryRepository()
    dept = _department(repo)
    patient_id = uuid4()
    issue_consult_ticket(
        repo, dept, uuid4(), patient_id, PriorityLevel.ROUTINE, issued_at=ANCHOR
    )
    issue_consult_ticket(
        repo, dept, uuid4(), uuid4(), PriorityLevel.EMERGENCY, issued_at=ANCHOR + timedelta(hours=1)
    )

    result = derive_patient_status(repo, patient_id)

    assert result.queue.people_ahead == 1


def test_awaiting_consult_ignores_done_and_skipped_tickets():
    repo = InMemoryRepository()
    dept = _department(repo)
    patient_id = uuid4()
    done = issue_consult_ticket(
        repo, dept, uuid4(), uuid4(), PriorityLevel.ROUTINE, issued_at=ANCHOR
    )
    repo.save(done.model_copy(update={"status": QueueTicketStatus.DONE}))
    skipped = issue_consult_ticket(
        repo,
        dept,
        uuid4(),
        uuid4(),
        PriorityLevel.ROUTINE,
        issued_at=ANCHOR + timedelta(minutes=1),
    )
    repo.save(skipped.model_copy(update={"status": QueueTicketStatus.SKIPPED}))
    issue_consult_ticket(
        repo,
        dept,
        uuid4(),
        patient_id,
        PriorityLevel.ROUTINE,
        issued_at=ANCHOR + timedelta(minutes=2),
    )

    result = derive_patient_status(repo, patient_id)

    assert result.queue.people_ahead == 0


# ---- derive_patient_status: PLAN_NOT_QUEUED ------------------------------------------------------


def test_plan_not_queued_when_all_tasks_locked():
    repo = InMemoryRepository()
    patient_id = uuid4()
    diagnosis = repo.save(
        Diagnosis(patient_id=patient_id, appointment_id=uuid4(), diagnosed_by=uuid4())
    )
    plan = repo.save(
        CarePlan(patient_id=patient_id, diagnosis_id=diagnosis.id, status=CarePlanStatus.ACTIVE)
    )
    t2 = _task(
        repo, plan.id, uuid4(), sequence_index=2,
        execution_status=ExecutionStatus.LOCKED, payment_status=PaymentStatus.UNPAID,
    )
    t1 = _task(
        repo, plan.id, uuid4(), sequence_index=1,
        execution_status=ExecutionStatus.LOCKED, payment_status=PaymentStatus.UNPAID,
    )

    result = derive_patient_status(repo, patient_id)

    assert result.status is PatientStatus.PLAN_NOT_QUEUED
    assert [pt.task_id for pt in result.plan_tasks] == [t1.id, t2.id]  # ordered by sequence_index


def test_plan_not_queued_when_no_tasks_reached_queue_because_done():
    repo = InMemoryRepository()
    patient_id = uuid4()
    diagnosis = repo.save(
        Diagnosis(patient_id=patient_id, appointment_id=uuid4(), diagnosed_by=uuid4())
    )
    plan = repo.save(
        CarePlan(patient_id=patient_id, diagnosis_id=diagnosis.id, status=CarePlanStatus.ACTIVE)
    )
    _task(
        repo, plan.id, uuid4(), sequence_index=1,
        execution_status=ExecutionStatus.DONE, payment_status=PaymentStatus.PAID,
    )

    result = derive_patient_status(repo, patient_id)

    assert result.status is PatientStatus.PLAN_NOT_QUEUED


# ---- derive_patient_status: TASK_IN_QUEUE --------------------------------------------------------


def test_task_in_queue_reports_position_and_eta_from_owner_queue():
    repo = InMemoryRepository()
    patient_id = uuid4()
    owner_id = uuid4()
    diagnosis = repo.save(
        Diagnosis(patient_id=patient_id, appointment_id=uuid4(), diagnosed_by=uuid4())
    )
    plan = repo.save(
        CarePlan(patient_id=patient_id, diagnosis_id=diagnosis.id, status=CarePlanStatus.ACTIVE)
    )
    # a different patient's task, same owner, sequenced ahead - this is who is "ahead in line"
    other_diagnosis = repo.save(
        Diagnosis(patient_id=uuid4(), appointment_id=uuid4(), diagnosed_by=uuid4())
    )
    other_plan = repo.save(
        CarePlan(
            patient_id=other_diagnosis.patient_id,
            diagnosis_id=other_diagnosis.id,
            status=CarePlanStatus.ACTIVE,
        )
    )
    _task(
        repo, other_plan.id, owner_id, sequence_index=0,
        execution_status=ExecutionStatus.PENDING, payment_status=PaymentStatus.PAID, duration=10,
    )
    _task(
        repo, plan.id, owner_id, sequence_index=1,
        execution_status=ExecutionStatus.PENDING, payment_status=PaymentStatus.PAID, duration=20,
    )

    result = derive_patient_status(repo, patient_id)

    assert result.status is PatientStatus.TASK_IN_QUEUE
    assert result.queue.people_ahead == 1
    assert result.queue.eta_minutes == 10
    assert result.queue.label is None


def test_task_in_queue_excludes_locked_tasks_from_position():
    repo = InMemoryRepository()
    patient_id = uuid4()
    owner_id = uuid4()
    diagnosis = repo.save(
        Diagnosis(patient_id=patient_id, appointment_id=uuid4(), diagnosed_by=uuid4())
    )
    plan = repo.save(
        CarePlan(patient_id=patient_id, diagnosis_id=diagnosis.id, status=CarePlanStatus.ACTIVE)
    )
    # unpaid task ahead in sequence must not count toward the queue position (BR-10)
    _task(
        repo, plan.id, owner_id, sequence_index=1,
        execution_status=ExecutionStatus.LOCKED, payment_status=PaymentStatus.UNPAID, duration=99,
    )
    _task(
        repo, plan.id, owner_id, sequence_index=2,
        execution_status=ExecutionStatus.PENDING, payment_status=PaymentStatus.PAID, duration=15,
    )

    result = derive_patient_status(repo, patient_id)

    assert result.status is PatientStatus.TASK_IN_QUEUE
    assert result.queue.people_ahead == 0
    assert result.queue.eta_minutes == 0


# ---- issue_consult_ticket -------------------------------------------------------------------


def test_issue_consult_ticket_numbers_sequentially_within_day_and_priority():
    repo = InMemoryRepository()
    dept = _department(repo)

    first = issue_consult_ticket(
        repo, dept, uuid4(), uuid4(), PriorityLevel.ROUTINE, issued_at=ANCHOR
    )
    second = issue_consult_ticket(
        repo, dept, uuid4(), uuid4(), PriorityLevel.ROUTINE, issued_at=ANCHOR + timedelta(hours=1)
    )
    next_day = issue_consult_ticket(
        repo, dept, uuid4(), uuid4(), PriorityLevel.ROUTINE, issued_at=ANCHOR + timedelta(days=1)
    )

    assert first.ticket_seq == 1
    assert first.ticket_label == "DepA-00001"
    assert second.ticket_seq == 2
    assert second.ticket_label == "DepA-00002"
    assert next_day.ticket_seq == 1  # resets the next day


def test_issue_consult_ticket_uses_separate_sequence_per_priority_band():
    repo = InMemoryRepository()
    dept = _department(repo)

    routine = issue_consult_ticket(
        repo, dept, uuid4(), uuid4(), PriorityLevel.ROUTINE, issued_at=ANCHOR
    )
    emergency = issue_consult_ticket(
        repo, dept, uuid4(), uuid4(), PriorityLevel.EMERGENCY, issued_at=ANCHOR
    )

    assert routine.ticket_label == "DepA-00001"
    assert emergency.ticket_label == "DepA-E-00001"


def test_issue_consult_ticket_sets_subject_and_status():
    repo = InMemoryRepository()
    dept = _department(repo)
    appointment_id = uuid4()
    patient_id = uuid4()

    ticket = issue_consult_ticket(
        repo, dept, appointment_id, patient_id, PriorityLevel.ROUTINE, issued_at=ANCHOR
    )

    assert ticket.subject_type is QueueSubjectType.CONSULT
    assert ticket.subject_id == appointment_id
    assert ticket.patient_id == patient_id
    assert ticket.status is QueueTicketStatus.WAITING


# ---- consult_queue_overview ---------------------------------------------------------------------


def test_queue_overview_counts_only_active_tickets_in_department():
    repo = InMemoryRepository()
    dept = _department(repo)
    other_dept = _department(repo, code="DepB")
    issue_consult_ticket(repo, dept, uuid4(), uuid4(), PriorityLevel.ROUTINE, issued_at=ANCHOR)
    issue_consult_ticket(
        repo, dept, uuid4(), uuid4(), PriorityLevel.ROUTINE, issued_at=ANCHOR + timedelta(minutes=1)
    )
    done = issue_consult_ticket(
        repo, dept, uuid4(), uuid4(), PriorityLevel.ROUTINE, issued_at=ANCHOR + timedelta(minutes=2)
    )
    repo.save(done.model_copy(update={"status": QueueTicketStatus.DONE}))
    issue_consult_ticket(  # different department - must not count
        repo, other_dept, uuid4(), uuid4(), PriorityLevel.ROUTINE, issued_at=ANCHOR
    )

    overview = consult_queue_overview(repo, dept.id)

    assert overview.people_waiting == 2
    assert overview.eta_minutes == 2 * AVERAGE_CONSULT_MINUTES


def test_queue_overview_is_zero_for_an_empty_queue():
    repo = InMemoryRepository()
    dept = _department(repo)

    overview = consult_queue_overview(repo, dept.id)

    assert overview.people_waiting == 0
    assert overview.eta_minutes == 0


# ---- list_patient_tasks ----------------------------------------------------------------------


def test_list_patient_tasks_empty_when_no_care_plan():
    repo = InMemoryRepository()

    assert list_patient_tasks(repo, uuid4()) == []


def test_list_patient_tasks_returns_every_task_in_sequence_order_with_service_type():
    repo = InMemoryRepository()
    patient_id = uuid4()
    diagnosis = repo.save(
        Diagnosis(patient_id=patient_id, appointment_id=uuid4(), diagnosed_by=uuid4())
    )
    plan = repo.save(
        CarePlan(patient_id=patient_id, diagnosis_id=diagnosis.id, status=CarePlanStatus.ACTIVE)
    )
    xray_order = _service_order(repo, patient_id, diagnosis.id, code="XRAY", label="X-Ray")
    blood_order = _service_order(
        repo, patient_id, diagnosis.id, code="BLOOD_TEST", label="Blood Test"
    )
    _task(
        repo, plan.id, uuid4(), sequence_index=1,
        execution_status=ExecutionStatus.DONE, payment_status=PaymentStatus.PAID,
        service_order_id=xray_order.id,
    )
    _task(
        repo, plan.id, uuid4(), sequence_index=0,
        execution_status=ExecutionStatus.LOCKED, payment_status=PaymentStatus.UNPAID,
        service_order_id=blood_order.id,
    )

    details = list_patient_tasks(repo, patient_id)

    assert [d.service_type_code for d in details] == ["BLOOD_TEST", "XRAY"]  # sequence_index order
    assert details[0].service_type_label == "Blood Test"
    assert details[0].execution_status is ExecutionStatus.LOCKED
    assert details[1].execution_status is ExecutionStatus.DONE


def test_list_patient_tasks_sets_queue_only_for_in_queue_tasks():
    repo = InMemoryRepository()
    patient_id = uuid4()
    owner_id = uuid4()
    diagnosis = repo.save(
        Diagnosis(patient_id=patient_id, appointment_id=uuid4(), diagnosed_by=uuid4())
    )
    plan = repo.save(
        CarePlan(patient_id=patient_id, diagnosis_id=diagnosis.id, status=CarePlanStatus.ACTIVE)
    )
    # someone else ahead in the same owner's queue
    other_diagnosis = repo.save(
        Diagnosis(patient_id=uuid4(), appointment_id=uuid4(), diagnosed_by=uuid4())
    )
    other_plan = repo.save(
        CarePlan(
            patient_id=other_diagnosis.patient_id,
            diagnosis_id=other_diagnosis.id,
            status=CarePlanStatus.ACTIVE,
        )
    )
    _task(
        repo, other_plan.id, owner_id, sequence_index=0,
        execution_status=ExecutionStatus.PENDING, payment_status=PaymentStatus.PAID, duration=12,
    )
    _task(
        repo, plan.id, uuid4(), sequence_index=0,
        execution_status=ExecutionStatus.LOCKED, payment_status=PaymentStatus.UNPAID,
    )
    _task(
        repo, plan.id, owner_id, sequence_index=1,
        execution_status=ExecutionStatus.PENDING, payment_status=PaymentStatus.PAID, duration=20,
    )

    details = list_patient_tasks(repo, patient_id)

    assert details[0].queue is None  # LOCKED - not in_queue
    assert details[1].queue is not None
    assert details[1].queue.people_ahead == 1
    assert details[1].queue.eta_minutes == 12

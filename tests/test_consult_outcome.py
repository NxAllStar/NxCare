"""Tests for recording a finished consult's outcome: diagnosis + orders + (unslotted) tasks.

Composes FR-03 (`capture_diagnosis_and_orders`) and FR-04 (`generate_care_plan`) via
`record_consult_outcome`. Lightweight path: tasks are created LOCKED, plan stays DRAFT (no slots).
All against `InMemoryRepository`, no network.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from vaic.agents.careplan.consult_outcome import (
    ConsultOutcomeError,
    build_consult_outcome_executor,
    record_consult_outcome,
)
from vaic.agents.intake.patient_status import (
    PatientStatus,
    derive_patient_status,
    list_patient_tasks,
)
from vaic.models import (
    Appointment,
    AppointmentStatus,
    CarePlan,
    CarePlanStatus,
    Diagnosis,
    ExecutionStatus,
    PaymentStatus,
    ServiceType,
    Task,
)
from vaic.state import InMemoryRepository


def _appointment(repo: InMemoryRepository) -> Appointment:
    return repo.save(
        Appointment(
            patient_id=uuid4(),
            specialty="NOI_TONG_QUAT",
            status=AppointmentStatus.CHECKED_IN,
            owner_id=uuid4(),
        )
    )


def _service_type(repo, code, label, *, duration=10) -> ServiceType:
    return repo.save(ServiceType(code=code, display_label=label, default_duration_min=duration))


def test_record_consult_outcome_creates_diagnosis_and_one_task_per_order():
    repo = InMemoryRepository()
    executor = build_consult_outcome_executor(repo)
    appt = _appointment(repo)
    doctor = uuid4()
    blood = _service_type(repo, "BLOOD_TEST", "Blood Test", duration=15)
    xray = _service_type(repo, "XRAY", "X-Ray", duration=20)

    outcome = record_consult_outcome(
        repo,
        executor,
        appointment_id=appt.id,
        conditions=["hypertension"],
        diagnosed_by=doctor,
        service_type_ids=[blood.id, xray.id],
    )

    diagnosis = repo.get(Diagnosis, outcome.diagnosis_id)
    assert diagnosis is not None
    assert diagnosis.patient_id == appt.patient_id
    assert diagnosis.conditions == ["hypertension"]

    assert len(outcome.task_ids) == 2
    tasks = repo.list(Task, care_plan_id=outcome.care_plan_id)
    assert len(tasks) == 2
    for task in tasks:  # lightweight: LOCKED/UNPAID, not slotted
        assert task.execution_status is ExecutionStatus.LOCKED
        assert task.payment_status is PaymentStatus.UNPAID


def test_record_consult_outcome_leaves_plan_draft_without_slots():
    repo = InMemoryRepository()
    executor = build_consult_outcome_executor(repo)
    appt = _appointment(repo)
    blood = _service_type(repo, "BLOOD_TEST", "Blood Test")

    outcome = record_consult_outcome(
        repo,
        executor,
        appointment_id=appt.id,
        conditions=["anemia"],
        diagnosed_by=uuid4(),
        service_type_ids=[blood.id],
    )

    plan = repo.get(CarePlan, outcome.care_plan_id)
    assert plan.status is CarePlanStatus.DRAFT  # no slots allocated -> never promoted to ACTIVE


def test_record_consult_outcome_moves_patient_status_to_plan_not_queued():
    repo = InMemoryRepository()
    executor = build_consult_outcome_executor(repo)
    appt = _appointment(repo)
    blood = _service_type(repo, "BLOOD_TEST", "Blood Test")

    # before: no diagnosis -> PRE_DIAGNOSIS
    assert derive_patient_status(repo, appt.patient_id).status is PatientStatus.PRE_DIAGNOSIS

    record_consult_outcome(
        repo,
        executor,
        appointment_id=appt.id,
        conditions=["flu"],
        diagnosed_by=uuid4(),
        service_type_ids=[blood.id],
    )

    # after: has diagnosis + tasks not queued -> PLAN_NOT_QUEUED, tasks visible on /tasks
    result = derive_patient_status(repo, appt.patient_id)
    assert result.status is PatientStatus.PLAN_NOT_QUEUED
    assert len(result.plan_tasks) == 1
    details = list_patient_tasks(repo, appt.patient_id)
    assert [d.service_type_code for d in details] == ["BLOOD_TEST"]


def test_record_consult_outcome_allows_diagnosis_with_no_orders():
    repo = InMemoryRepository()
    executor = build_consult_outcome_executor(repo)
    appt = _appointment(repo)

    outcome = record_consult_outcome(
        repo,
        executor,
        appointment_id=appt.id,
        conditions=["healthy, no further tests"],
        diagnosed_by=uuid4(),
        service_type_ids=[],
    )

    assert repo.get(Diagnosis, outcome.diagnosis_id) is not None
    assert outcome.task_ids == []


def test_record_consult_outcome_raises_for_unknown_appointment():
    repo = InMemoryRepository()
    executor = build_consult_outcome_executor(repo)

    with pytest.raises(ConsultOutcomeError):
        record_consult_outcome(
            repo,
            executor,
            appointment_id=uuid4(),
            conditions=["x"],
            diagnosed_by=uuid4(),
            service_type_ids=[],
        )


def test_record_consult_outcome_raises_for_unknown_service_type():
    repo = InMemoryRepository()
    executor = build_consult_outcome_executor(repo)
    appt = _appointment(repo)

    with pytest.raises(ConsultOutcomeError):
        record_consult_outcome(
            repo,
            executor,
            appointment_id=appt.id,
            conditions=["x"],
            diagnosed_by=uuid4(),
            service_type_ids=[uuid4()],  # not a real ServiceType
        )


def test_record_consult_outcome_refuses_non_doctor_actor():
    repo = InMemoryRepository()
    executor = build_consult_outcome_executor(repo)
    appt = _appointment(repo)
    blood = _service_type(repo, "BLOOD_TEST", "Blood Test")

    with pytest.raises(ConsultOutcomeError):
        record_consult_outcome(
            repo,
            executor,
            appointment_id=appt.id,
            conditions=["x"],
            diagnosed_by=uuid4(),
            service_type_ids=[blood.id],
            actor_role="role_nurse",  # not role_doctor -> BR-05 refuses the service order
        )

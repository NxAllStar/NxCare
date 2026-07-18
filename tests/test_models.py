"""Model and enum invariants (TASK-003). Values trace to docs/specs/03-glossary.md and 08."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from vaic.models import (
    ExecutionStatus,
    Patient,
    Payment,
    PaymentStatus,
    PaymentSubjectType,
    PriorityLevel,
    ServiceType,
    Task,
)


def test_enum_values_are_english_upper_snake():
    assert ExecutionStatus.IN_PROGRESS.value == "IN_PROGRESS"
    assert PaymentStatus.PAID.value == "PAID"
    assert PriorityLevel.EMERGENCY.value == "EMERGENCY"


def test_patient_requires_patient_code_and_defaults_routine():
    p = Patient(full_name="Nguyen Van A", patient_code="VAIC-7F3A2")
    assert p.priority_level is PriorityLevel.ROUTINE
    with pytest.raises(ValidationError):
        Patient(full_name="No Code")  # patient_code is required (FR-17)


def test_payment_is_a_flag_amount_optional():
    pay = Payment(patient_id=uuid4(), subject_type=PaymentSubjectType.TASK, subject_id=uuid4())
    assert pay.amount is None  # app processes no money (AS-02)
    assert pay.status is PaymentStatus.UNPAID


def test_service_type_defaults():
    st = ServiceType(code="BLOOD_TEST", display_label="Xet nghiem mau", requires_fasting=True,
                     turnaround_minutes=45)
    assert st.requires_fasting is True
    assert st.default_duration_min == 10


def _task(**kw) -> Task:
    base = dict(care_plan_id=uuid4(), service_order_id=uuid4(), owner_id=uuid4())
    base.update(kw)
    return Task(**base)


def test_unpaid_task_is_locked_and_not_in_queue():
    t = _task(payment_status=PaymentStatus.UNPAID, execution_status=ExecutionStatus.LOCKED)
    assert t.is_locked is True
    assert t.in_queue is False  # BR-10: excluded from queue/load


def test_paid_pending_task_is_in_queue():
    t = _task(payment_status=PaymentStatus.PAID, execution_status=ExecutionStatus.PENDING)
    assert t.is_locked is False
    assert t.in_queue is True


def test_extra_fields_are_forbidden():
    with pytest.raises(ValidationError):
        Patient(full_name="X", patient_code="C", nonsense=1)

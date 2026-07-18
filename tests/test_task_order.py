"""Tests for service-queue load and the task-order suggestion (grounded, deterministic fallback).

Covers `service_queue_overview` (per-service-type queue load) and `suggest_task_order` (the
retrieve -> reason -> validate order suggestion). The reasoner is the deterministic
`RuleBasedTaskOrderLLM` or a fake - no network (testing.md).
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from vaic.agents.intake.patient_status import service_queue_overview
from vaic.agents.intake.task_order import (
    RuleBasedTaskOrderLLM,
    suggest_task_order,
)
from vaic.models import (
    CarePlan,
    CarePlanStatus,
    Diagnosis,
    ExecutionStatus,
    PaymentStatus,
    ServiceOrder,
    ServiceType,
    Task,
)
from vaic.state import InMemoryRepository


def _service_type(repo, code, *, duration=10) -> ServiceType:
    return repo.save(ServiceType(code=code, display_label=code, default_duration_min=duration))


def _task_for(repo, plan_id, service_type, patient_id, *, status, paid, duration, seq=0) -> Task:
    order = repo.save(
        ServiceOrder(
            patient_id=patient_id,
            diagnosis_id=uuid4(),
            service_type_id=service_type.id,
            ordered_by=uuid4(),
        )
    )
    return repo.save(
        Task(
            care_plan_id=plan_id,
            service_order_id=order.id,
            owner_id=uuid4(),
            execution_status=status,
            payment_status=PaymentStatus.PAID if paid else PaymentStatus.UNPAID,
            estimated_duration_min=duration,
            sequence_index=seq,
        )
    )


# ---- service_queue_overview -------------------------------------------------------------------


def test_service_queue_counts_only_in_queue_tasks_of_that_type():
    repo = InMemoryRepository()
    plan_id = uuid4()
    blood = _service_type(repo, "BLOOD_TEST")
    xray = _service_type(repo, "XRAY")
    # two blood tasks in queue (paid, PENDING), one blood locked (unpaid -> not in queue)
    _task_for(repo, plan_id, blood, uuid4(), status=ExecutionStatus.PENDING, paid=True, duration=10)
    _task_for(
        repo, plan_id, blood, uuid4(), status=ExecutionStatus.IN_PROGRESS, paid=True, duration=5
    )
    _task_for(repo, plan_id, blood, uuid4(), status=ExecutionStatus.LOCKED, paid=False, duration=99)
    # an xray task must not count toward the blood queue
    _task_for(repo, plan_id, xray, uuid4(), status=ExecutionStatus.PENDING, paid=True, duration=20)

    overview = service_queue_overview(repo, blood.id)

    assert overview.people_waiting == 2
    assert overview.eta_minutes == 15  # 10 + 5, the unpaid one excluded


def test_service_queue_is_zero_when_no_tasks():
    repo = InMemoryRepository()
    blood = _service_type(repo, "BLOOD_TEST")

    overview = service_queue_overview(repo, blood.id)

    assert overview.people_waiting == 0
    assert overview.eta_minutes == 0


# ---- suggest_task_order -----------------------------------------------------------------------


def _patient_with_two_services(repo) -> tuple[Any, Task, Task]:
    """A patient with a blood task (busy queue) and an ECG task (quiet queue)."""
    patient_id = uuid4()
    diagnosis = repo.save(
        Diagnosis(patient_id=patient_id, appointment_id=uuid4(), diagnosed_by=uuid4())
    )
    plan = repo.save(
        CarePlan(patient_id=patient_id, diagnosis_id=diagnosis.id, status=CarePlanStatus.DRAFT)
    )
    blood = _service_type(repo, "BLOOD_TEST")
    ecg = _service_type(repo, "ECG")
    # the patient's own remaining tasks (LOCKED)
    blood_task = _task_for(
        repo, plan.id, blood, patient_id,
        status=ExecutionStatus.LOCKED, paid=False, duration=15, seq=0,
    )
    ecg_task = _task_for(
        repo, plan.id, ecg, patient_id,
        status=ExecutionStatus.LOCKED, paid=False, duration=10, seq=1,
    )
    # OTHER patients queued: blood is busy (30 min), ECG is quiet (5 min)
    _task_for(repo, uuid4(), blood, uuid4(), status=ExecutionStatus.PENDING, paid=True, duration=30)
    _task_for(repo, uuid4(), ecg, uuid4(), status=ExecutionStatus.PENDING, paid=True, duration=5)
    return patient_id, blood_task, ecg_task


def test_suggest_task_order_deterministic_puts_shortest_wait_first():
    repo = InMemoryRepository()
    patient_id, blood_task, ecg_task = _patient_with_two_services(repo)

    suggestion = suggest_task_order(repo, patient_id, RuleBasedTaskOrderLLM())

    order_ids = [entry.task_id for entry in suggestion.order]
    assert order_ids == [str(ecg_task.id), str(blood_task.id)]  # ECG (5min) before blood (30min)
    assert suggestion.message


def test_suggest_task_order_empty_when_no_remaining_tasks():
    repo = InMemoryRepository()

    suggestion = suggest_task_order(repo, uuid4(), RuleBasedTaskOrderLLM())

    assert suggestion.order == []


class _FakeLLM:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def reply(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        return self._payload


def test_suggest_task_order_uses_valid_model_output():
    repo = InMemoryRepository()
    patient_id, blood_task, ecg_task = _patient_with_two_services(repo)
    # model returns a valid permutation (blood first, its own choice)
    payload = {
        "message": "do blood first",
        "order": [
            {"task_id": str(blood_task.id), "service_type_code": "BLOOD_TEST", "reason": "x"},
            {"task_id": str(ecg_task.id), "service_type_code": "ECG", "reason": "y"},
        ],
    }

    suggestion = suggest_task_order(repo, patient_id, _FakeLLM(payload))

    assert [e.task_id for e in suggestion.order] == [str(blood_task.id), str(ecg_task.id)]


def test_suggest_task_order_falls_back_when_model_output_not_a_permutation():
    repo = InMemoryRepository()
    patient_id, blood_task, ecg_task = _patient_with_two_services(repo)
    # model drops a task -> not a permutation -> deterministic fallback used instead
    payload = {
        "message": "partial",
        "order": [{"task_id": str(blood_task.id), "service_type_code": "BLOOD_TEST"}],
    }

    suggestion = suggest_task_order(repo, patient_id, _FakeLLM(payload))

    order_ids = [entry.task_id for entry in suggestion.order]
    assert order_ids == [str(ecg_task.id), str(blood_task.id)]  # fallback: shortest wait first

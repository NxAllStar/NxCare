"""FR-05 proceed gate HTTP route (TASK-034): `POST /care-plans/{id}/tasks/{id}/proceed` must bind
`actor_role`/`confirmed_by` to the authenticated FR-18 principal, never to caller-supplied body
fields, and must audit the PAID flip via `ActionExecutor` (FR-13).

Calls `confirm_proceed` directly (bypassing FastAPI's TestClient/dependency-injection layer, which
would require a live Postgres-backed `PostgresRepositorySyncAdapter`) with an `InMemoryRepository`
standing in for the adapter - `_build_executor` only needs the `Repository` interface, not the real
adapter type.
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from fastapi import HTTPException

from vaic.api.careplan_routes import confirm_proceed
from vaic.auth import Account, Role
from vaic.models import CarePlan, ExecutionStatus, Payment, PaymentStatus, Task
from vaic.state import InMemoryRepository
from vaic.tools import AuditLog


def _locked_task(repo, owner_id=None) -> Task:
    care_plan = repo.save(CarePlan(patient_id=uuid4(), diagnosis_id=uuid4()))
    return repo.save(
        Task(
            care_plan_id=care_plan.id,
            service_order_id=uuid4(),
            owner_id=owner_id or uuid4(),
            execution_status=ExecutionStatus.LOCKED,
            payment_status=PaymentStatus.UNPAID,
            estimated_duration_min=15,
        )
    )


def _run(coro):
    return asyncio.run(coro)


def test_authorised_account_confirms_payment_and_it_is_audited():
    repo = InMemoryRepository()
    task = _locked_task(repo)
    account = Account(username="test_coordinator", role=Role.COORDINATOR)
    audit_before = len(AuditLog(repo).entries())

    result = _run(
        confirm_proceed(
            care_plan_id=task.care_plan_id, task_id=task.id, account=account, adapter=repo
        )
    )

    assert result["task_id"] == str(task.id)
    updated = repo.get(Task, task.id)
    assert updated.execution_status is ExecutionStatus.PENDING
    assert updated.payment_status is PaymentStatus.PAID

    payments = repo.list(Payment, subject_id=task.id)
    assert len(payments) == 1
    assert payments[0].confirmed_by == account.id  # bound to the authenticated principal

    assert len(AuditLog(repo).entries()) == audit_before + 1  # the flip left a trace (FR-13)


def test_confirmed_by_binds_to_the_accounts_resource_id_when_present():
    repo = InMemoryRepository()
    task = _locked_task(repo)
    resource_id = uuid4()
    account = Account(username="test_coordinator", role=Role.COORDINATOR, resource_id=resource_id)

    _run(
        confirm_proceed(
            care_plan_id=task.care_plan_id, task_id=task.id, account=account, adapter=repo
        )
    )

    payments = repo.list(Payment, subject_id=task.id)
    assert payments[0].confirmed_by == resource_id


def test_unauthorised_role_cannot_flip_paid_and_it_is_audited_as_failed():
    repo = InMemoryRepository()
    task = _locked_task(repo)
    account = Account(username="test_patient", role=Role.PATIENT)  # not authorised (BR-11)
    audit_before = len(AuditLog(repo).entries())

    with pytest.raises(HTTPException) as exc_info:
        _run(
            confirm_proceed(
                care_plan_id=task.care_plan_id, task_id=task.id, account=account, adapter=repo
            )
        )

    assert exc_info.value.status_code == 422
    assert repo.get(Task, task.id).execution_status is ExecutionStatus.LOCKED
    assert repo.list(Payment, subject_id=task.id) == []
    entries = AuditLog(repo).entries()
    assert len(entries) == audit_before + 1
    assert entries[-1].action == "FAILED:confirm_payment"


def test_no_way_to_supply_actor_role_or_confirmed_by_from_the_request():
    """Structural regression guard for TASK-034: the handler signature has no body parameter for
    `actor_role`/`confirmed_by` at all, so there is nothing in the request a caller could spoof."""
    import inspect

    params = inspect.signature(confirm_proceed).parameters
    assert "body" not in params
    assert "actor_role" not in params
    assert "confirmed_by" not in params

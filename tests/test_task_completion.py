"""Tests for the complete_task tool (FR-06): a task's final hop IN_PROGRESS -> DONE.

Exercises the tool through the guarded ActionExecutor spine, same as the other task-station tools.
"""

from __future__ import annotations

from uuid import uuid4

from vaic.agents.core import ActionExecutor
from vaic.agents.journey.task_completion import build_complete_task_tool
from vaic.models import ExecutionStatus, PaymentStatus, Task
from vaic.state import InMemoryRepository
from vaic.tools import Action, AuditLog, ConstraintChecker, ToolRegistry


def _executor(repo: InMemoryRepository) -> ActionExecutor:
    registry = ToolRegistry()
    registry.register(build_complete_task_tool())
    return ActionExecutor(repo, registry, ConstraintChecker(repo), AuditLog(repo))


def _task(repo, owner_id, *, status) -> Task:
    return repo.save(
        Task(
            care_plan_id=uuid4(),
            service_order_id=uuid4(),
            owner_id=owner_id,
            execution_status=status,
            payment_status=PaymentStatus.PAID,
        )
    )


def _run(executor, task_id, completed_by):
    return executor.execute(
        Action(
            tool="complete_task",
            actor="tech",
            reasoning="",
            params={"task_id": task_id, "completed_by": completed_by},
        )
    )


def test_complete_task_marks_in_progress_task_done():
    repo = InMemoryRepository()
    executor = _executor(repo)
    owner = uuid4()
    task = _task(repo, owner, status=ExecutionStatus.IN_PROGRESS)

    result = _run(executor, task.id, owner)

    assert result.ok
    assert repo.get(Task, task.id).execution_status is ExecutionStatus.DONE


def test_complete_task_rejects_non_owner():
    repo = InMemoryRepository()
    executor = _executor(repo)
    task = _task(repo, uuid4(), status=ExecutionStatus.IN_PROGRESS)

    result = _run(executor, task.id, uuid4())  # not the owner

    assert not result.ok
    assert repo.get(Task, task.id).execution_status is ExecutionStatus.IN_PROGRESS


def test_complete_task_rejects_task_not_in_progress():
    repo = InMemoryRepository()
    executor = _executor(repo)
    owner = uuid4()
    task = _task(repo, owner, status=ExecutionStatus.PENDING)  # scanned in not done yet

    result = _run(executor, task.id, owner)

    assert not result.ok
    assert repo.get(Task, task.id).execution_status is ExecutionStatus.PENDING


def test_complete_task_rejects_unknown_task():
    repo = InMemoryRepository()
    executor = _executor(repo)

    result = _run(executor, uuid4(), uuid4())

    assert not result.ok

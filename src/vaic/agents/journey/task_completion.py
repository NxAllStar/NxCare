"""Finish a task at its station (FR-06): the last hop of a task's life, `IN_PROGRESS -> DONE`.

The mirror of `scan.py`'s start-of-service scan: the same owner who scanned the patient in
(BR-26) reports the work finished. Deterministic code, no model call. Like `gate.py`'s
`confirm_payment`, there is no `constraint_checker.py` rule keyed `"complete_task"` (that is
agent-core-dev's file, out of scope here), so ownership and the state-machine guard are enforced
INSIDE this handler - a wrong owner or a task that is not `IN_PROGRESS` is refused as a `ToolError`,
which the `ActionExecutor` records as an audited `FAILED:complete_task`, never a silent no-op.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ...models import (
    TASK_TRANSITIONS,
    ExecutionStatus,
    InvalidTransition,
    Task,
    assert_transition,
)
from ...state import Repository
from ...tools import Tool, ToolError

COMPLETE_TASK_TOOL = "complete_task"


class CompleteTaskIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: UUID
    completed_by: UUID  # must be the task owner (BR-26) - the resource that performed the service


def _complete_task(params: CompleteTaskIn, repo: Repository) -> dict:
    task = repo.get(Task, params.task_id)
    if task is None:
        raise ToolError("unknown task")
    if params.completed_by != task.owner_id:  # BR-26: only the owner reports its own work done
        raise ToolError("only the task owner may complete it - BR-26")

    try:
        # TASK_TRANSITIONS[IN_PROGRESS] = {DONE, CANCELLED}: this rejects anything not IN_PROGRESS
        # from one place, so a paid-but-not-started (PENDING) or already-DONE task cannot be closed.
        assert_transition(TASK_TRANSITIONS, task.execution_status, ExecutionStatus.DONE)
    except InvalidTransition as exc:
        raise ToolError(
            f"task is {task.execution_status.value}, expected IN_PROGRESS"
        ) from exc

    task.execution_status = ExecutionStatus.DONE
    task = repo.save(task)
    return {"task_id": str(task.id), "execution_status": task.execution_status.value}


def build_complete_task_tool() -> Tool:
    return Tool(COMPLETE_TASK_TOOL, CompleteTaskIn, _complete_task)

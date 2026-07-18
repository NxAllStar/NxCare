"""Deterministic constraint checker - runs before EVERY action (NFR-SEC-13).

This is code, never an LLM call. It enforces the guardrails the specs make load-bearing, so an
action that would violate one never executes. A tool with no specific rule is allowed (the closed
action space itself is the coarse gate; this adds the fine gates).
"""

from __future__ import annotations

from collections.abc import Callable

from ..models import ExecutionStatus, Resource, Task
from ..state import Repository
from .action import Action, Decision

# Interim default for the tiered-autonomy blast-radius threshold. NOT a policy - spec OI-03 is
# undecided; this is a wired default the Team lead overrides when OI-03 is answered.
DEFAULT_REPLAN_THRESHOLD = 5


class ConstraintChecker:
    def __init__(self, repo: Repository, replan_threshold: int = DEFAULT_REPLAN_THRESHOLD) -> None:
        self._repo = repo
        self._replan_threshold = replan_threshold
        self._rules: dict[str, Callable[[Action], Decision]] = {
            "start_task": self._check_start_task,
            "scan_patient": self._check_scan_patient,
            "allocate_slot": self._check_allocate_slot,
            "create_service_order": self._check_create_service_order,
            "execute_replan": self._check_execute_replan,
        }

    def check(self, action: Action) -> Decision:
        rule = self._rules.get(action.tool)
        return rule(action) if rule is not None else Decision(allowed=True)

    # ---- rules ---------------------------------------------------------------

    def _check_start_task(self, action: Action) -> Decision:
        task = self._repo.get(Task, action.params.get("task_id"))
        if task is None:
            return Decision(allowed=False, reason="unknown task")
        if task.is_locked:  # BR-10 / BR-27: unpaid task cannot start
            return Decision(allowed=False, reason="task is LOCKED (unpaid) - BR-10")
        if task.execution_status is not ExecutionStatus.PENDING:
            return Decision(
                allowed=False,
                reason=f"task is {task.execution_status.value}, not PENDING",
            )
        if action.params.get("actor_id") != task.owner_id:  # ownership
            return Decision(allowed=False, reason="actor is not the task owner")
        return Decision(allowed=True)

    def _check_scan_patient(self, action: Action) -> Decision:
        task = self._repo.get(Task, action.params.get("task_id"))
        if task is None:
            return Decision(allowed=False, reason="unknown task")
        if task.is_locked:  # BR-27
            return Decision(allowed=False, reason="cannot scan a LOCKED (unpaid) task - BR-27")
        if action.params.get("scanned_by") != task.owner_id:  # BR-26
            return Decision(allowed=False, reason="only the task owner may scan - BR-26")
        if task.execution_status is not ExecutionStatus.PENDING:
            return Decision(
                allowed=False,
                reason=f"task is {task.execution_status.value}, not PENDING",
            )
        return Decision(allowed=True)

    def _check_allocate_slot(self, action: Action) -> Decision:
        resource = self._repo.get(Resource, action.params.get("resource_id"))
        if resource is None:
            return Decision(allowed=False, reason="unknown resource")
        if not resource.is_available:  # BR-16
            return Decision(allowed=False, reason="resource is unavailable (closed room) - BR-16")
        return Decision(allowed=True)

    def _check_create_service_order(self, action: Action) -> Decision:
        if action.params.get("actor_role") != "role_doctor":  # BR-05 / CO-02
            return Decision(
                allowed=False, reason="only a doctor may create a service order - BR-05"
            )
        return Decision(allowed=True)

    def _check_execute_replan(self, action: Action) -> Decision:
        blast_radius = int(action.params.get("blast_radius", 0))
        approved = bool(action.params.get("approved", False))
        if blast_radius > self._replan_threshold and not approved:  # FR-09 tiered autonomy
            return Decision(
                allowed=False,
                reason=(
                    f"blast radius {blast_radius} > threshold {self._replan_threshold}: "
                    "coordinator approval required (FR-09)"
                ),
            )
        return Decision(allowed=True)

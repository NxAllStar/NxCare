"""The action spine: closed-action-space check -> constraint checker -> tool -> audit.

Every action an agent takes goes through here, so the guardrails cannot be bypassed and every
decision (allowed, blocked, or failed) is audited (FR-13). Framework-agnostic: no LangGraph import.
"""

from __future__ import annotations

from ...state import Repository
from ...tools import Action, ActionResult, AuditLog, ConstraintChecker, ToolError, ToolRegistry


class ActionExecutor:
    def __init__(
        self,
        repo: Repository,
        registry: ToolRegistry,
        checker: ConstraintChecker,
        audit: AuditLog,
    ) -> None:
        self._repo = repo
        self._registry = registry
        self._checker = checker
        self._audit = audit

    def execute(self, action: Action) -> ActionResult:
        # 1. Closed action space (BR-19): unknown tool never runs.
        if not self._registry.has(action.tool):
            entry = self._audit.record(action.actor, f"BLOCKED:{action.tool}",
                                       "outside the action space")
            return ActionResult(allowed=False, ok=False, reason="outside the action space",
                                audit_id=entry.id)

        # 2. Deterministic constraint checker (NFR-SEC-13) before any effect.
        decision = self._checker.check(action)
        if not decision.allowed:
            entry = self._audit.record(action.actor, f"BLOCKED:{action.tool}", decision.reason)
            return ActionResult(allowed=False, ok=False, reason=decision.reason, audit_id=entry.id)

        # 3. Run the tool (input schema-validated inside the tool).
        tool = self._registry.get(action.tool)
        try:
            output = tool.run(action.params, self._repo)
        except ToolError as exc:
            entry = self._audit.record(action.actor, f"FAILED:{action.tool}", str(exc))
            return ActionResult(allowed=True, ok=False, reason=str(exc), audit_id=entry.id)

        # 4. Record the successful decision with its reasoning.
        entry = self._audit.record(action.actor, action.tool, action.reasoning)
        return ActionResult(allowed=True, ok=True, output=output, audit_id=entry.id)

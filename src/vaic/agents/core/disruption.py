"""The Disruption Agent (FR-09): re-plan around an abnormal event with tiered autonomy.

Flow: assess the blast radius (distinct patients affected), then propose a re-plan through the
guarded spine. The constraint checker's `execute_replan` rule is the tier gate: a blast radius at
or below the threshold auto-executes (no human step); above it, the action is BLOCKED and the event
is parked as `PENDING_APPROVAL` for one-tap coordinator approval. Approval re-issues the same action
with `approved=True` (which passes the gate); rejection leaves the original plan untouched and
records the decision on the append-only audit log (BR-18). The agent never bypasses the gate - it
routes every state change through the `ActionExecutor`, so autonomy is enforced by code, not trust.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ...models import (
    CarePlan,
    DisruptionEvent,
    DisruptionEventType,
    DisruptionStatus,
    Task,
)
from ...tools import Action, AuditLog
from .agent import Agent
from .executor import ActionExecutor
from .replan import EXECUTE_REPLAN_TOOL, affected_tasks

if TYPE_CHECKING:  # keep core free of a journey import at load time (Notifier is injected)
    from ..journey.notifications import Notifier


class DisruptionError(Exception):
    """Raised when an approve/reject targets a disruption that is not awaiting a decision."""


class DisruptionOutcome(BaseModel):
    """The result of handling (or deciding) a disruption - what the console and tests read."""

    model_config = ConfigDict(extra="forbid")

    disruption_id: UUID
    blast_radius: int
    tier: str  # "auto" | "approval_required" | "approved" | "rejected"
    executed: bool
    status: str  # the DisruptionStatus value
    reassigned: int = 0


class DisruptionAgent(Agent):
    def __init__(
        self,
        executor: ActionExecutor,
        repo: Any,
        notifier: Notifier,
        audit: AuditLog,
        *,
        name: str = "disruption",
    ) -> None:
        super().__init__(name, executor)
        self._repo = repo
        self._notifier = notifier
        self._audit = audit

    # ---- Agent base ---------------------------------------------------------------------------

    def perceive(self, event: Any) -> UUID:
        """Reduce the event to the failed resource id (the thing the re-plan routes around)."""
        return event if isinstance(event, UUID) else event.resource_id

    def reason(self, perception: UUID) -> list[Action]:
        radius = self._distinct_patients(affected_tasks(self._repo, perception))
        return [self._replan_action(perception, radius, approved=False)]

    # ---- FR-09 entry points -------------------------------------------------------------------

    def handle(
        self,
        resource_id: UUID,
        *,
        event_type: DisruptionEventType = DisruptionEventType.EQUIPMENT_FAILURE,
    ) -> DisruptionOutcome:
        """Assess and either auto-execute (<= N) or propose for approval (> N)."""
        tasks = affected_tasks(self._repo, resource_id)
        radius = self._distinct_patients(tasks)
        event = self._repo.save(
            DisruptionEvent(
                event_type=event_type,
                blast_radius=radius,
                resource_id=resource_id,
                status=DisruptionStatus.DETECTED,
            )
        )
        action = self._replan_action(resource_id, radius, approved=False, disruption_id=event.id)
        result = self.act(action)

        if result.allowed and result.ok:  # at or below threshold: auto-resolved by the tool
            event = self._repo.get(DisruptionEvent, event.id)
            self._notify(tasks, event_type)
            return DisruptionOutcome(
                disruption_id=event.id, blast_radius=radius, tier="auto", executed=True,
                status=event.status.value, reassigned=len(tasks),
            )

        # blocked by the tiered-autonomy gate: park for one-tap approval, execute nothing
        event.status = DisruptionStatus.PENDING_APPROVAL
        self._repo.save(event)
        return DisruptionOutcome(
            disruption_id=event.id, blast_radius=radius, tier="approval_required", executed=False,
            status=event.status.value, reassigned=0,
        )

    def approve(self, disruption_id: UUID, *, decided_by: UUID) -> DisruptionOutcome:
        """Execute a parked re-plan on a coordinator's one-tap approval (FR-09 AC-09.2 tail)."""
        event = self._pending(disruption_id)
        tasks = affected_tasks(self._repo, event.resource_id)
        action = self._replan_action(
            event.resource_id, event.blast_radius, approved=True,
            disruption_id=event.id, actor="role_coordinator",
            reasoning="coordinator approved the re-plan (one-tap, FR-09)",
        )
        result = self.act(action)
        event = self._repo.get(DisruptionEvent, event.id)
        event.decided_by = decided_by
        self._repo.save(event)
        self._notify(tasks, event.event_type)
        return DisruptionOutcome(
            disruption_id=event.id, blast_radius=event.blast_radius, tier="approved",
            executed=result.ok, status=event.status.value, reassigned=len(tasks),
        )

    def reject(self, disruption_id: UUID, *, decided_by: UUID) -> DisruptionOutcome:
        """Reject a parked re-plan: keep the original plan, audit the decision (FR-09 AC-09.3)."""
        event = self._pending(disruption_id)
        event.status = DisruptionStatus.REJECTED
        event.decided_by = decided_by
        self._repo.save(event)
        self._audit.record(
            "role_coordinator",
            "REJECTED:execute_replan",
            "coordinator rejected the re-plan; original plan kept (FR-09 AC-09.3)",
            target_id=event.id,
        )
        return DisruptionOutcome(
            disruption_id=event.id, blast_radius=event.blast_radius, tier="rejected",
            executed=False, status=event.status.value, reassigned=0,
        )

    # ---- internals ----------------------------------------------------------------------------

    def _pending(self, disruption_id: UUID) -> DisruptionEvent:
        event = self._repo.get(DisruptionEvent, disruption_id)
        if event is None or event.status is not DisruptionStatus.PENDING_APPROVAL:
            raise DisruptionError("no re-plan awaiting a decision for this disruption")
        return event

    def _replan_action(
        self,
        resource_id: UUID,
        blast_radius: int,
        *,
        approved: bool,
        disruption_id: UUID | None = None,
        actor: str | None = None,
        reasoning: str | None = None,
    ) -> Action:
        params: dict[str, Any] = {
            "resource_id": resource_id,
            "blast_radius": blast_radius,
            "approved": approved,
        }
        if disruption_id is not None:
            params["disruption_id"] = disruption_id
        return Action(
            tool=EXECUTE_REPLAN_TOOL,
            actor=actor or self.name,
            params=params,
            reasoning=reasoning or f"re-plan proposed for {blast_radius} affected patient(s)",
        )

    def _distinct_patients(self, tasks: list[Task]) -> int:
        patients: set[UUID] = set()
        for task in tasks:
            care_plan = self._repo.get(CarePlan, task.care_plan_id)
            if care_plan is not None:
                patients.add(care_plan.patient_id)
        return len(patients)

    def _notify(self, tasks: list[Task], event_type: DisruptionEventType) -> None:
        by_patient: dict[UUID, list[UUID]] = {}
        for task in tasks:
            care_plan = self._repo.get(CarePlan, task.care_plan_id)
            if care_plan is not None:
                by_patient.setdefault(care_plan.patient_id, []).append(task.id)
        reason = f"{event_type.value.replace('_', ' ').lower()} re-plan"
        for patient_id, task_ids in by_patient.items():
            self._notifier.notify(
                patient_id,
                body="Your schedule was adjusted after an equipment issue; "
                "your next step was kept as early as possible.",
                reason=reason,
                about_task_ids=task_ids,
            )

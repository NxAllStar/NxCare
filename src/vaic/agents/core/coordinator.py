"""The Coordinator Agent (FR-10): the central perceive -> reason -> act loop.

The Coordinator consumes a batch of events (BR-20: batched to control cost/latency), reads a
deterministic hospital-wide snapshot (FR-10 "snapshot built by code"), and for each event decides
whether to delegate to the Disruption agent, call a tool itself, or simply observe. Every decision
records its reasoning to the append-only audit log before it acts (BR-18 / AC-10.1). It acts only
through the guarded `ActionExecutor`, so an action outside the closed tool set is rejected by the
spine, never executed (AC-10.2) - the coordinator does not get to widen its own action space.

The reasoning step is a swappable `CoordinatorBrain`. The default is rule-based and deterministic
(cheap, testable, no provider dependency); an LLM-backed brain drops in behind the same interface
via `run_reason_flow` (`flow.py`) without any change to this loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ...tools import (
    Action,
    ActionResult,
    AuditLog,
    ConstraintChecker,
    ToolRegistry,
)
from ...tools.constraint_checker import DEFAULT_REPLAN_THRESHOLD
from .agent import Agent
from .disruption import DisruptionAgent, DisruptionOutcome
from .executor import ActionExecutor
from .replan import build_execute_replan_tool
from .snapshot import HospitalSnapshot, build_snapshot

if TYPE_CHECKING:  # Notifier is injected; core must not import the journey package at load time
    from ..journey.notifications import Notifier

# Above this many queued minutes, a check-in onto an already-loaded owner is worth a rebalance
# (interim default; the real threshold is a policy dial, like OI-03's blast-radius N).
CHECK_IN_OVERLOAD_MINUTES = 90


class CoordinatorEvent(BaseModel):
    """One event on the coordinator's bus. `kind` names it; the ids are the subjects it concerns."""

    model_config = ConfigDict(extra="forbid")

    kind: str  # "check_in" | "equipment_failure" | "overload" | ...
    resource_id: UUID | None = None
    patient_id: UUID | None = None


class CoordinatorDecision(BaseModel):
    """What the brain decided for one event: reasoning plus at most one way to act."""

    model_config = ConfigDict(extra="forbid")

    reasoning: str
    action: Action | None = None  # act through the guarded spine (closed action space)
    delegate_resource_id: UUID | None = None  # hand off to the Disruption agent


class CoordinatorResult(BaseModel):
    """The outcome the coordinator recorded for one event."""

    model_config = ConfigDict(extra="forbid")

    event_kind: str
    audit_id: UUID | None = None
    delegated: bool = False
    disruption: DisruptionOutcome | None = None
    action_result: ActionResult | None = None


class CoordinatorBrain(Protocol):
    def decide(
        self, event: CoordinatorEvent, snapshot: HospitalSnapshot
    ) -> CoordinatorDecision: ...


class RuleBasedCoordinatorBrain:
    """Deterministic routing: disruptions delegate; overloaded check-in rebalances; else idle."""

    def decide(self, event: CoordinatorEvent, snapshot: HospitalSnapshot) -> CoordinatorDecision:
        if event.kind in ("equipment_failure", "overload") and event.resource_id is not None:
            return CoordinatorDecision(
                reasoning=f"{event.kind} on a resource; delegating re-plan to the Disruption agent",
                delegate_resource_id=event.resource_id,
            )
        if event.kind == "check_in":
            owner = snapshot.for_owner(event.resource_id) if event.resource_id else None
            if owner is not None and owner.load_minutes > CHECK_IN_OVERLOAD_MINUTES:
                return CoordinatorDecision(
                    reasoning=(
                        f"check-in onto an owner carrying {owner.load_minutes} queued minutes; "
                        "delegating a rebalance"
                    ),
                    delegate_resource_id=event.resource_id,
                )
            load = owner.load_minutes if owner is not None else 0
            return CoordinatorDecision(
                reasoning=f"check-in perceived; owner load {load} min nominal; no re-plan needed",
            )
        return CoordinatorDecision(reasoning=f"event '{event.kind}' observed; no action taken")


class CoordinatorAgent(Agent):
    def __init__(
        self,
        executor: ActionExecutor,
        repo: Any,
        audit: AuditLog,
        disruption: DisruptionAgent,
        *,
        brain: CoordinatorBrain | None = None,
        name: str = "coordinator",
    ) -> None:
        super().__init__(name, executor)
        self._repo = repo
        self._audit = audit
        self._disruption = disruption
        self._brain: CoordinatorBrain = brain or RuleBasedCoordinatorBrain()

    # ---- Agent base ---------------------------------------------------------------------------

    def perceive(self, event: Any) -> Any:
        return event

    def reason(self, perception: Any) -> list[Action]:
        decision = self._brain.decide(perception, build_snapshot(self._repo))
        return [decision.action] if decision.action is not None else []

    # ---- FR-10 loop ---------------------------------------------------------------------------

    def handle(self, events: list[CoordinatorEvent]) -> list[CoordinatorResult]:
        """Perceive one snapshot, then reason -> act over the whole batch (BR-20)."""
        snapshot = build_snapshot(self._repo)  # perceive (deterministic)
        results: list[CoordinatorResult] = []
        for event in events:
            decision = self._brain.decide(event, snapshot)  # reason
            entry = self._audit.record(self.name, f"coordinate:{event.kind}", decision.reasoning)
            if decision.delegate_resource_id is not None:
                outcome = self._disruption.handle(decision.delegate_resource_id)
                results.append(
                    CoordinatorResult(
                        event_kind=event.kind, audit_id=entry.id, delegated=True, disruption=outcome
                    )
                )
            elif decision.action is not None:
                result = self.act(decision.action)  # closed action space enforced here (AC-10.2)
                results.append(
                    CoordinatorResult(
                        event_kind=event.kind, audit_id=entry.id, action_result=result
                    )
                )
            else:
                results.append(CoordinatorResult(event_kind=event.kind, audit_id=entry.id))
        return results


# ---- wiring ------------------------------------------------------------------------------------

@dataclass(frozen=True)
class CoordinatorStack:
    """The assembled FR-09/FR-10 stack, sharing one executor, checker, and audit log."""

    coordinator: CoordinatorAgent
    disruption: DisruptionAgent
    executor: ActionExecutor
    audit: AuditLog
    registry: ToolRegistry
    repo: Any


def build_coordinator_stack(
    repo: Any,
    *,
    threshold: int = DEFAULT_REPLAN_THRESHOLD,
    notifier: Notifier | None = None,
) -> CoordinatorStack:
    """Assemble the Coordinator + Disruption agents over one guarded spine (FR-09 / FR-10)."""
    from ..journey.notifications import Notifier  # local import: keep core free of journey at load

    registry = ToolRegistry()
    registry.register(build_execute_replan_tool())
    checker = ConstraintChecker(repo, replan_threshold=threshold)
    audit = AuditLog(repo)
    executor = ActionExecutor(repo, registry, checker, audit)
    disruption = DisruptionAgent(executor, repo, notifier or Notifier(repo), audit)
    coordinator = CoordinatorAgent(executor, repo, audit, disruption)
    return CoordinatorStack(
        coordinator=coordinator,
        disruption=disruption,
        executor=executor,
        audit=audit,
        registry=registry,
        repo=repo,
    )

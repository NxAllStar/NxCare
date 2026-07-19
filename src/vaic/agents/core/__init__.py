"""Agent core: the framework-agnostic spine (executor + Agent base) and the coordination loop."""

from __future__ import annotations

from .agent import Agent
from .coordinator import (
    CoordinatorAgent,
    CoordinatorDecision,
    CoordinatorEvent,
    CoordinatorResult,
    CoordinatorStack,
    RuleBasedCoordinatorBrain,
    build_coordinator_stack,
)
from .disruption import DisruptionAgent, DisruptionError, DisruptionOutcome
from .executor import ActionExecutor
from .flow import run_reason_flow
from .replan import (
    affected_tasks,
    available_alternates,
    build_execute_replan_tool,
    compute_blast_radius,
)
from .snapshot import HospitalSnapshot, OwnerLoad, build_snapshot

__all__ = [
    "Agent",
    "ActionExecutor",
    "run_reason_flow",
    "build_snapshot",
    "HospitalSnapshot",
    "OwnerLoad",
    "compute_blast_radius",
    "affected_tasks",
    "available_alternates",
    "build_execute_replan_tool",
    "DisruptionAgent",
    "DisruptionError",
    "DisruptionOutcome",
    "CoordinatorAgent",
    "CoordinatorEvent",
    "CoordinatorDecision",
    "CoordinatorResult",
    "CoordinatorStack",
    "RuleBasedCoordinatorBrain",
    "build_coordinator_stack",
]

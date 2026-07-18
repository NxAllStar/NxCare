"""Framework-agnostic Agent base: perceive -> reason -> act.

An agent perceives an event, reasons to a list of proposed Actions, and acts through the shared
ActionExecutor so every action is checked and audited. If LangGraph is accepted (ADR-001), it wraps
this shape; it does not replace it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ...tools import Action, ActionResult
from .executor import ActionExecutor


class Agent(ABC):
    def __init__(self, name: str, executor: ActionExecutor) -> None:
        self.name = name
        self._executor = executor

    @abstractmethod
    def perceive(self, event: Any) -> Any:
        """Turn a raw event into the state this agent reasons over."""

    @abstractmethod
    def reason(self, perception: Any) -> list[Action]:
        """Decide the actions to take. Model output here is a proposal, never executed directly."""

    def act(self, action: Action) -> ActionResult:
        """Execute one proposed action through the guarded spine."""
        return self._executor.execute(action)

    def run(self, event: Any) -> list[ActionResult]:
        return [self.act(action) for action in self.reason(self.perceive(event))]

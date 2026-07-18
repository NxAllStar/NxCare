"""Tool framework - the closed action space.

Agents act ONLY through registered tools (BR-19). Each tool validates its input against a schema
before running, and a tool's return is treated as untrusted until validated (NFR-SEC-12).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ValidationError

from ..state import Repository


class ToolError(Exception):
    """Raised when a tool is unknown, its input is invalid, or its execution fails."""


class Tool:
    """A named action with a Pydantic input schema and a handler.

    `run` validates raw params against the schema (rejecting, never coercing, malformed input) and
    then calls the handler with the typed model.
    """

    def __init__(
        self,
        name: str,
        input_model: type[BaseModel],
        handler: Callable[[BaseModel, Repository], dict[str, Any]],
    ) -> None:
        self.name = name
        self.input_model = input_model
        self._handler = handler

    def run(self, params: dict[str, Any], repo: Repository) -> dict[str, Any]:
        try:
            typed = self.input_model.model_validate(params)
        except ValidationError as exc:  # NFR-SEC-12: schema-validate before use
            msg = f"invalid params for tool '{self.name}': {exc.error_count()} error(s)"
            raise ToolError(msg) from exc
        return self._handler(typed, repo)


class ToolRegistry:
    """The set of tools an agent may call. Anything not registered is outside the action space."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ToolError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def has(self, name: str) -> bool:
        return name in self._tools

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise ToolError(f"tool outside the action space: {name}")
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools)

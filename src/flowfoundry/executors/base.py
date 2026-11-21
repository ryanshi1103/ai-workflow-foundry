"""The deliberately small contract that external execution systems map into."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ExecutorRequest:
    goal: str
    context: str
    constraints: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExecutorResult:
    status: str
    output: str
    artifacts: tuple[str, ...] = ()
    usage: dict[str, Any] | None = None
    evidence: tuple[dict[str, Any], ...] = ()
    errors: tuple[str, ...] = ()
    # The responsible provider's final answer, preserved independently from
    # evaluator status and evidence. ``output`` remains for API compatibility.
    agent_response: str = ""


class Executor(Protocol):
    id: str
    capabilities: frozenset[str]

    def execute(self, request: ExecutorRequest) -> ExecutorResult: ...

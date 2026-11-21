"""Task-to-agent routing."""

from __future__ import annotations

from .models import AgentSpec, TaskSpec
from .registry import AgentRegistry


class TaskRouter:
    def __init__(
        self,
        registry: AgentRegistry,
        history_scores: dict[str, float] | None = None,
    ) -> None:
        self.registry = registry
        self.history_scores = history_scores or {}

    def route(
        self,
        task: TaskSpec,
        running_counts: dict[str, int] | None = None,
        excluded_agent_ids: set[str] | frozenset[str] | None = None,
    ) -> AgentSpec:
        return self.registry.match(
            task,
            running_counts,
            self.history_scores,
            excluded_agent_ids,
        )

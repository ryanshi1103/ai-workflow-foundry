"""Task-to-agent routing."""

from __future__ import annotations

from .models import AgentSpec, TaskSpec
from .registry import AgentRegistry


class TaskRouter:
    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry

    def route(
        self,
        task: TaskSpec,
        running_counts: dict[str, int] | None = None,
    ) -> AgentSpec:
        return self.registry.match(task, running_counts)

"""Agent registry and deterministic capability matching."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .models import AgentSpec, TaskSpec

_COST_ORDER = {"free": 0, "low": 1, "medium": 2, "high": 3}


class AgentRegistry:
    def __init__(self, agents: Iterable[AgentSpec] = ()) -> None:
        self._agents = {agent.id: agent for agent in agents}

    def register(self, agent: AgentSpec) -> None:
        if agent.id in self._agents:
            raise ValueError(f"agent already registered: {agent.id}")
        if agent.concurrency_limit < 1:
            raise ValueError("concurrency_limit must be positive")
        self._agents[agent.id] = agent

    def get(self, agent_id: str) -> AgentSpec:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise KeyError(f"unknown agent: {agent_id}") from exc

    def list(self) -> tuple[AgentSpec, ...]:
        return tuple(self._agents[key] for key in sorted(self._agents))

    def match(
        self,
        task: TaskSpec,
        running_counts: dict[str, int] | None = None,
    ) -> AgentSpec:
        running = running_counts or {}
        required = set(task.required_capabilities)
        permissions = set(task.required_permissions)
        preferred = set(task.preferred_capabilities)
        candidates: list[AgentSpec] = []
        for agent in self._agents.values():
            if not agent.enabled or not agent.availability or agent.role != task.role:
                continue
            if running.get(agent.id, 0) >= agent.concurrency_limit:
                continue
            if not required.issubset(agent.capabilities):
                continue
            if not permissions.issubset(agent.permission_profile):
                continue
            candidates.append(agent)

        if not candidates and task.fallback_agent:
            fallback = self.get(task.fallback_agent)
            if (
                fallback.enabled
                and fallback.availability
                and running.get(fallback.id, 0) < fallback.concurrency_limit
                and permissions.issubset(fallback.permission_profile)
            ):
                return fallback
        if not candidates:
            raise LookupError(f"no eligible agent for task: {task.id}")

        return min(
            candidates,
            key=lambda agent: (
                -len(preferred.intersection(agent.capabilities)),
                _COST_ORDER.get(agent.cost_class, 99),
                agent.id,
            ),
        )

    def synthetic(self) -> AgentRegistry:
        """Return a registry enabled for fake/offline provider execution."""

        return AgentRegistry(
            replace(agent, availability=True, enabled=True)
            for agent in self._agents.values()
        )


def default_registry() -> AgentRegistry:
    common_read = ("read_workspace",)
    write = ("read_workspace", "write_workspace")
    return AgentRegistry(
        (
            AgentSpec(
                id="codex-builder",
                display_name="Codex Builder",
                provider="codex",
                role="builder",
                capabilities=("implementation", "python", "shell", "documentation"),
                command_template=("codex", "exec", "{task_file}"),
                cost_class="medium",
                concurrency_limit=2,
                permission_profile=write,
                context_limit=200_000,
                availability=False,
                workspace_mode="isolated_worktree",
            ),
            AgentSpec(
                id="deepseek-reviewer",
                display_name="DeepSeek Reviewer",
                provider="deepseek",
                role="reviewer",
                capabilities=("review", "security_review", "python"),
                command_template=("deepseek", "review", "{task_file}"),
                cost_class="low",
                concurrency_limit=2,
                permission_profile=common_read,
                context_limit=128_000,
                availability=False,
                workspace_mode="read_only_worktree",
            ),
            AgentSpec(
                id="claude-architect",
                display_name="Claude Architect",
                provider="claude",
                role="architect",
                capabilities=("architecture", "planning", "documentation"),
                command_template=("claude", "--print", "{task_file}"),
                cost_class="high",
                concurrency_limit=1,
                permission_profile=common_read,
                context_limit=200_000,
                availability=False,
                workspace_mode="read_only_worktree",
            ),
            AgentSpec(
                id="local-tester",
                display_name="Local Tester",
                provider="local",
                role="tester",
                capabilities=("testing", "python", "shell"),
                command_template=("python", "-m", "pytest"),
                cost_class="free",
                concurrency_limit=2,
                permission_profile=write,
                context_limit=32_000,
                availability=False,
                workspace_mode="isolated_worktree",
            ),
        )
    )

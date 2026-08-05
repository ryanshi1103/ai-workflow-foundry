"""Provider adapters. Real command execution is disabled unless explicitly enabled."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .models import AgentSpec, ProviderResult, ReviewDecision, TaskSpec


class Provider(Protocol):
    def execute(self, task: TaskSpec, agent: AgentSpec, task_dir: Path) -> ProviderResult: ...


@dataclass
class FakeProvider:
    """Deterministic provider used by tests and the public example."""

    failures_before_success: dict[str, int] = field(default_factory=dict)
    reviews: dict[str, ReviewDecision] = field(default_factory=dict)
    calls: dict[str, int] = field(default_factory=dict)

    def execute(self, task: TaskSpec, agent: AgentSpec, task_dir: Path) -> ProviderResult:
        count = self.calls.get(task.id, 0) + 1
        self.calls[task.id] = count
        if count <= self.failures_before_success.get(task.id, 0):
            return ProviderResult(False, f"synthetic failure {count}")
        review = self.reviews.get(task.id)
        if agent.role == "reviewer" and review is None:
            review = ReviewDecision.APPROVED
        return ProviderResult(
            True,
            f"synthetic {agent.role} completed {task.id}",
            outputs={"task_id": task.id, "agent_id": agent.id, "synthetic": True},
            review=review,
        )


class DryRunProvider(FakeProvider):
    """Alias with explicit intent for CLI dry-run execution."""


class LocalCommandProvider:
    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled

    def execute(self, task: TaskSpec, agent: AgentSpec, task_dir: Path) -> ProviderResult:
        if not self.enabled:
            return ProviderResult(False, "real provider execution is disabled")
        command = [part.replace("{task_file}", str(task_dir / "task.json")) for part in agent.command_template]
        completed = subprocess.run(
            command,
            cwd=task_dir,
            capture_output=True,
            check=False,
            text=True,
            timeout=task.timeout_seconds,
        )
        return ProviderResult(
            completed.returncode == 0,
            f"local command exited {completed.returncode}",
            outputs={"stdout": completed.stdout, "stderr": completed.stderr},
        )

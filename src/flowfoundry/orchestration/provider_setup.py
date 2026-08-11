"""Persist an actionable provider-setup request only when routing needs it."""

from __future__ import annotations

from typing import Any

from .discovery import credential_sources
from .models import TaskSpec
from .registry import AgentRegistry
from .workspace import RunWorkspace, atomic_write_json, utc_now


class ProviderSetupFlow:
    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry

    def record(self, workspace: RunWorkspace, task: TaskSpec, reason: str) -> dict[str, Any]:
        candidates = []
        for agent in self.registry.compatible(task):
            candidates.append(
                {
                    "agent_id": agent.id,
                    "provider": agent.provider,
                    "model": agent.model,
                    "executable": agent.command_template[0] if agent.command_template else None,
                    "availability": "available" if agent.availability else "unavailable",
                    "readiness": agent.readiness,
                    "authentication_state": agent.authentication_state,
                    "credential_sources": list(credential_sources(agent.provider)),
                }
            )
        record = {
            "schema_version": 1,
            "status": "setup_required",
            "task_id": task.id,
            "required_role": task.role,
            "required_capabilities": list(task.required_capabilities),
            "reason": reason,
            "candidates": candidates,
            "next_step": "run `flowfoundry team providers`, then configure one compatible runtime",
            "created_at": utc_now(),
        }
        atomic_write_json(
            workspace.contained("provider-setup", f"{task.id}.json"),
            record,
        )
        workspace.append_human_action(
            task.id,
            "provider setup required; run `flowfoundry team providers` for credential names and runtime state",
        )
        return record

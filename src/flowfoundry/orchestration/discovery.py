"""Provider/runtime discovery without credential value access or network probes."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, replace
from typing import Callable, Mapping

from .models import AgentSpec
from .registry import AgentRegistry

_AUTH_ENV = {
    "codex": ("OPENAI_API_KEY",),
    "claude": ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"),
    "deepseek": ("DEEPSEEK_API_KEY",),
}


def credential_sources(provider: str) -> tuple[str, ...]:
    """Return credential variable names only, never their values."""

    return _AUTH_ENV.get(provider, ())


@dataclass(frozen=True)
class ProviderStatus:
    agent_id: str
    provider: str
    model: str
    executable: str
    installed: bool
    availability: str
    authentication_state: str
    credential_sources: tuple[str, ...]
    setup_action: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "agent_id": self.agent_id,
            "provider": self.provider,
            "model": self.model,
            "executable": self.executable,
            "installed": self.installed,
            "availability": self.availability,
            "authentication_state": self.authentication_state,
            "credential_sources": list(self.credential_sources),
            "setup_action": self.setup_action,
        }


class ProviderDiscovery:
    def __init__(
        self,
        registry: AgentRegistry,
        *,
        executable_lookup: Callable[[str], str | None] = shutil.which,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self.source = registry
        self.executable_lookup = executable_lookup
        self.environ = os.environ if environ is None else environ

    def inspect(self) -> tuple[ProviderStatus, ...]:
        return tuple(self._status(agent) for agent in self.source.list())

    def registry(self) -> AgentRegistry:
        statuses = {status.agent_id: status for status in self.inspect()}
        return AgentRegistry(
            replace(
                agent,
                availability=statuses[agent.id].installed,
                authentication_state=statuses[agent.id].authentication_state,
            )
            for agent in self.source.list()
        )

    def _status(self, agent: AgentSpec) -> ProviderStatus:
        executable = agent.command_template[0] if agent.command_template else ""
        installed = bool(executable and self.executable_lookup(executable))
        sources = credential_sources(agent.provider)
        if agent.local:
            authentication_state = "not_required"
        elif agent.provider in {"claude", "deepseek"} and installed:
            # The shared cc runtime intentionally isolates these providers in
            # provider-specific config directories. Do not inspect those files
            # or infer their auth state from the parent process environment.
            authentication_state = "unverified"
        elif any(name in self.environ and bool(self.environ[name]) for name in sources):
            authentication_state = "configured"
        elif installed:
            authentication_state = "unverified"
        else:
            authentication_state = "unconfigured"

        if not installed:
            setup_action = f"install or configure the {executable or agent.provider} runtime"
            availability = "unavailable"
        elif authentication_state == "unverified":
            setup_action = f"verify {agent.provider} CLI authentication when first needed"
            availability = "available_unverified"
        else:
            setup_action = None
            availability = "available"
        return ProviderStatus(
            agent_id=agent.id,
            provider=agent.provider,
            model=agent.model,
            executable=executable,
            installed=installed,
            availability=availability,
            authentication_state=authentication_state,
            credential_sources=sources,
            setup_action=setup_action,
        )

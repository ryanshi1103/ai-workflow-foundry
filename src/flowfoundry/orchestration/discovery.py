"""Provider/runtime discovery without credential value access or network probes."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, replace
from typing import Callable, Mapping

from .models import AgentSpec
from .registry import AgentRegistry

_AUTH_ENV = {
    "codex": ("OPENAI_API_KEY",),
    "claude": ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"),
    "deepseek": ("DEEPSEEK_API_KEY",),
}

_CODEX_AUTH_TIMEOUT_SECONDS = 3.0
_AUTH_OUTPUT_LIMIT = 4_096

CommandRunner = Callable[[tuple[str, ...], float], subprocess.CompletedProcess[str]]


def _run_command(
    command: tuple[str, ...], timeout_seconds: float
) -> subprocess.CompletedProcess[str]:
    """Run one fixed discovery command without a shell or inherited stdin."""

    return subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


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
    readiness: str
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
            "readiness": self.readiness,
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
        command_runner: CommandRunner | None = None,
        auth_timeout_seconds: float = _CODEX_AUTH_TIMEOUT_SECONDS,
    ) -> None:
        self.source = registry
        self.executable_lookup = executable_lookup
        self.environ = os.environ if environ is None else environ
        self.command_runner = command_runner or _run_command
        self.auth_timeout_seconds = max(0.1, auth_timeout_seconds)

    def inspect(self) -> tuple[ProviderStatus, ...]:
        return tuple(self._status(agent) for agent in self.source.list())

    def registry(self) -> AgentRegistry:
        statuses = {status.agent_id: status for status in self.inspect()}
        return AgentRegistry(
            replace(
                agent,
                availability=statuses[agent.id].installed,
                readiness=statuses[agent.id].readiness,
                authentication_state=statuses[agent.id].authentication_state,
            )
            for agent in self.source.list()
        )

    def _status(self, agent: AgentSpec) -> ProviderStatus:
        executable = agent.command_template[0] if agent.command_template else ""
        resolved_executable = self.executable_lookup(executable) if executable else None
        installed = bool(resolved_executable)
        sources = credential_sources(agent.provider)
        if agent.local:
            authentication_state = "not_required"
        elif agent.provider == "codex" and installed:
            authentication_state = self._codex_authentication_state(
                str(resolved_executable)
            )
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
            readiness = "UNAVAILABLE"
        elif authentication_state in {"verified", "not_required"}:
            setup_action = None
            availability = "available"
            readiness = "READY"
        else:
            setup_action = (
                "run `codex login` to authenticate"
                if agent.provider == "codex"
                and authentication_state == "not_authenticated"
                else f"verify {agent.provider} CLI authentication when first needed"
            )
            availability = "available_unverified"
            readiness = "AVAILABLE_UNVERIFIED"
        return ProviderStatus(
            agent_id=agent.id,
            provider=agent.provider,
            model=agent.model,
            executable=executable,
            installed=installed,
            availability=availability,
            readiness=readiness,
            authentication_state=authentication_state,
            credential_sources=sources,
            setup_action=setup_action,
        )

    def _codex_authentication_state(self, executable: str) -> str:
        """Classify only the documented, non-inference Codex login status."""

        try:
            completed = self.command_runner(
                (executable, "login", "status"), self.auth_timeout_seconds
            )
        except (subprocess.TimeoutExpired, OSError):
            return "unverified"

        output = " ".join(
            f"{completed.stdout or ''}\n{completed.stderr or ''}".casefold().split()
        )[:_AUTH_OUTPUT_LIMIT]
        not_authenticated = (
            "not logged in",
            "not authenticated",
            "unauthenticated",
            "login required",
        )
        if any(pattern in output for pattern in not_authenticated):
            return "not_authenticated"
        if completed.returncode == 0 and any(
            pattern in output for pattern in ("logged in", "authenticated")
        ):
            return "verified"
        return "unverified"

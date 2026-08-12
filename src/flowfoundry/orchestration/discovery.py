"""Provider/runtime discovery without credential value access or network probes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, replace
from typing import Callable, Mapping

from ..workspace.providers.config import (
    claude_profile_provider,
    prepare_claude_profile_environment,
)
from .models import AgentSpec
from .registry import AgentRegistry

_AUTH_ENV = {
    "codex": ("OPENAI_API_KEY",),
    "claude": ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"),
    "deepseek": ("DEEPSEEK_API_KEY",),
}

_CODEX_AUTH_TIMEOUT_SECONDS = 3.0
_AUTH_OUTPUT_LIMIT = 4_096

CommandRunner = Callable[
    [tuple[str, ...], float, Mapping[str, str] | None],
    subprocess.CompletedProcess[str],
]


def _run_command(
    command: tuple[str, ...],
    timeout_seconds: float,
    environment: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one fixed discovery command without a shell or inherited stdin."""

    return subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
        env=dict(environment) if environment is not None else None,
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
    runtime_profile: str | None
    provider_identity_state: str
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
            "runtime_profile": self.runtime_profile,
            "provider_identity_state": self.provider_identity_state,
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
                provider_identity_state=statuses[agent.id].provider_identity_state,
            )
            for agent in self.source.list()
        )

    def _status(self, agent: AgentSpec) -> ProviderStatus:
        executable = agent.command_template[0] if agent.command_template else ""
        resolved_executable = self.executable_lookup(executable) if executable else None
        installed = bool(resolved_executable)
        sources = credential_sources(agent.provider)
        provider_identity_state = self._provider_identity_state(agent)
        if agent.local:
            authentication_state = "not_required"
        elif (
            agent.provider == "codex"
            and installed
            and provider_identity_state == "verified"
        ):
            authentication_state = self._codex_authentication_state(
                str(resolved_executable)
            )
        elif (
            agent.provider in {"claude", "deepseek"}
            and installed
            and provider_identity_state == "verified"
        ):
            authentication_state = self._claude_profile_authentication_state(
                str(resolved_executable), agent.runtime_profile
            )
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
        elif (
            authentication_state in {"verified", "not_required"}
            and provider_identity_state in {"verified", "not_required"}
        ):
            setup_action = None
            availability = "available"
            readiness = "READY"
        else:
            setup_action = (
                "run `codex login` to authenticate"
                if agent.provider == "codex"
                and authentication_state == "not_authenticated"
                else (
                    "run `claude auth login` to authenticate"
                    if agent.provider == "claude"
                    and authentication_state == "not_authenticated"
                    else (
                        "authenticate the DeepSeek-compatible profile"
                        if agent.provider == "deepseek"
                        and authentication_state == "not_authenticated"
                        else f"verify {agent.provider} CLI authentication when first needed"
                    )
                )
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
            runtime_profile=agent.runtime_profile,
            provider_identity_state=provider_identity_state,
            credential_sources=sources,
            setup_action=setup_action,
        )

    @staticmethod
    def _provider_identity_state(agent: AgentSpec) -> str:
        """Verify that an agent is bound to the declared provider profile."""

        if agent.local:
            return "not_required"
        if agent.provider == "codex":
            return (
                "verified"
                if agent.runtime_profile == "codex_native"
                else "unverified"
            )
        if agent.provider in {"claude", "deepseek"}:
            return (
                "verified"
                if agent.runtime_profile is not None
                and claude_profile_provider(agent.runtime_profile) == agent.provider
                else "unverified"
            )
        return "unverified"

    def _codex_authentication_state(self, executable: str) -> str:
        """Classify only the documented, non-inference Codex login status."""

        completed = self._bounded_auth_status(
            (executable, "login", "status"), environment=None
        )
        if completed is None:
            return "unverified"

        output = " ".join(
            f"{completed.stdout or ''}\n{completed.stderr or ''}".casefold().split()
        )
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

    def _claude_profile_authentication_state(
        self,
        executable: str,
        runtime_profile: str | None,
    ) -> str:
        """Probe Claude-compatible auth in the real provider profile context."""

        if runtime_profile is None:
            return "unverified"
        environment = dict(self.environ)
        try:
            prepare_claude_profile_environment(runtime_profile, environment)
        except ValueError:
            return "unverified"

        completed = self._bounded_auth_status(
            (executable, "auth", "status", "--json"),
            environment=environment,
        )
        if completed is None:
            return "unverified"
        try:
            status = json.loads(completed.stdout or "")
        except (json.JSONDecodeError, TypeError):
            return "unverified"
        if not isinstance(status, dict):
            return "unverified"
        logged_in = status.get("loggedIn")
        if type(logged_in) is not bool:
            return "unverified"
        if not logged_in:
            return "not_authenticated"
        return "verified" if completed.returncode == 0 else "unverified"

    def _bounded_auth_status(
        self,
        command: tuple[str, ...],
        *,
        environment: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str] | None:
        """Run one internal fixed-argv status probe and reject oversized output."""

        try:
            completed = self.command_runner(
                command,
                self.auth_timeout_seconds,
                environment,
            )
        except (subprocess.TimeoutExpired, OSError):
            return None
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        if len(stdout) + len(stderr) > _AUTH_OUTPUT_LIMIT:
            return None
        return completed

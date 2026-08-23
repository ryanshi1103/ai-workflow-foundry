"""Provider-specific workspace checks performed before a provider attempt."""

from __future__ import annotations

import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from .models import AgentSpec
from .workspace import RunWorkspace, atomic_write_json, utc_now

_GIT_TIMEOUT_SECONDS = 2.0
_OUTPUT_LIMIT = 4_096

CommandRunner = Callable[
    [tuple[str, ...], Path, float], subprocess.CompletedProcess[str]
]


def _run_command(
    command: tuple[str, ...], cwd: Path, timeout_seconds: float
) -> subprocess.CompletedProcess[str]:
    environment = {
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(cwd),
        "PATH": os.environ.get("PATH", ""),
    }
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


@dataclass(frozen=True)
class WorkspacePreflightResult:
    provider: str
    workspace: str
    workspace_origin: str
    provider_readiness: str
    compatible: bool
    checks: dict[str, object]
    remediation: str
    provider_attempt_allowed: bool
    error_code: str | None = None
    reason: str | None = None
    created_at: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class WorkspaceCompatibilityPreflight:
    """Generic preflight hook with one conservative Codex Git rule."""

    def __init__(
        self,
        *,
        command_runner: CommandRunner | None = None,
        timeout_seconds: float = _GIT_TIMEOUT_SECONDS,
    ) -> None:
        self.command_runner = command_runner or _run_command
        self.timeout_seconds = max(0.1, timeout_seconds)

    def check(
        self,
        agent: AgentSpec,
        workspace: RunWorkspace,
        execution_workspace: Path,
    ) -> WorkspacePreflightResult:
        path = execution_workspace.resolve()
        origin = workspace.workspace_origin
        base = {
            "provider": agent.provider,
            "workspace": str(path),
            "workspace_origin": origin,
            "provider_readiness": agent.readiness,
            "created_at": utc_now(),
        }
        if agent.provider != "codex":
            return WorkspacePreflightResult(
                **base,
                compatible=True,
                checks={"provider_workspace_rule": "not_required"},
                remediation="none",
                provider_attempt_allowed=True,
            )
        if not path.exists():
            return self._blocked(
                base,
                checks={"exists": False, "directory": False, "accessible": False},
                error_code="CODEX_WORKSPACE_MISSING",
                reason="Codex execution workspace does not exist",
            )
        if not path.is_dir():
            return self._blocked(
                base,
                checks={"exists": True, "directory": False, "accessible": False},
                error_code="CODEX_WORKSPACE_NOT_DIRECTORY",
                reason="Codex execution workspace is not a directory",
            )
        accessible = os.access(path, os.R_OK | os.X_OK)
        if not accessible:
            return self._blocked(
                base,
                checks={"exists": True, "directory": True, "accessible": False},
                error_code="CODEX_WORKSPACE_INACCESSIBLE",
                reason="Codex execution workspace is not accessible",
            )

        git_state, git_detail = self._git_state(path)
        checks: dict[str, object] = {
            "exists": True,
            "directory": True,
            "accessible": True,
            "git_worktree": git_state == "inside",
            "git_check": git_state,
        }
        if git_state == "inside":
            return WorkspacePreflightResult(
                **base,
                compatible=True,
                checks=checks,
                remediation="none",
                provider_attempt_allowed=True,
            )
        if git_state != "outside":
            return self._blocked(
                base,
                checks=checks,
                error_code=(
                    "CODEX_WORKSPACE_GIT_CHECK_TIMEOUT"
                    if git_state == "timeout"
                    else "CODEX_WORKSPACE_GIT_CHECK_FAILED"
                ),
                reason=git_detail,
            )

        disposable_owned = (
            origin == "flowfoundry_disposable"
            and workspace.workspace_owned_by_flowfoundry
            and workspace.workspace_disposable
            and path == workspace.project_root_path
        )
        if not disposable_owned:
            return self._blocked(
                base,
                checks=checks,
                error_code="CODEX_WORKSPACE_NOT_GIT",
                reason="Codex execution requires a compatible Git workspace",
            )

        init_state, init_detail = self._git_init(path)
        checks["git_init"] = init_state
        if init_state != "initialized":
            return self._blocked(
                base,
                checks=checks,
                error_code=(
                    "CODEX_WORKSPACE_GIT_INIT_TIMEOUT"
                    if init_state == "timeout"
                    else "CODEX_WORKSPACE_GIT_INIT_FAILED"
                ),
                reason=init_detail,
            )
        final_state, final_detail = self._git_state(path)
        checks["git_worktree"] = final_state == "inside"
        checks["git_recheck"] = final_state
        if final_state != "inside":
            return self._blocked(
                base,
                checks=checks,
                error_code="CODEX_WORKSPACE_GIT_INIT_FAILED",
                reason=final_detail,
            )
        return WorkspacePreflightResult(
            **base,
            compatible=True,
            checks=checks,
            remediation="auto_initialized_disposable_git",
            provider_attempt_allowed=True,
        )

    def persist(
        self,
        workspace: RunWorkspace,
        task_id: str,
        result: WorkspacePreflightResult,
    ) -> str:
        ref = f"provider-setup/{task_id}-workspace-preflight.json"
        atomic_write_json(workspace.contained(ref), result.to_dict())
        return ref

    def _git_state(self, path: Path) -> tuple[str, str]:
        try:
            completed = self.command_runner(
                ("git", "rev-parse", "--is-inside-work-tree"),
                path,
                self.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return "timeout", "Git workspace compatibility check timed out"
        except OSError as exc:
            return "failed", f"Git workspace compatibility check failed: {type(exc).__name__}"
        stdout, stderr = self._output(completed)
        if completed.returncode == 0 and stdout.strip().casefold() == "true":
            return "inside", "Git worktree detected"
        if completed.returncode == 128 and "not a git repository" in stderr.casefold():
            return "outside", "Workspace is not a Git worktree"
        return "failed", "Git workspace compatibility could not be determined safely"

    def _git_init(self, path: Path) -> tuple[str, str]:
        try:
            completed = self.command_runner(
                ("git", "init", "--quiet"), path, self.timeout_seconds
            )
        except subprocess.TimeoutExpired:
            return "timeout", "Disposable Git initialization timed out"
        except OSError as exc:
            return "failed", f"Disposable Git initialization failed: {type(exc).__name__}"
        if completed.returncode == 0:
            return "initialized", "Disposable Git workspace initialized"
        return "failed", "Disposable Git initialization failed"

    @staticmethod
    def _output(completed: subprocess.CompletedProcess[str]) -> tuple[str, str]:
        return (
            (completed.stdout or "")[-_OUTPUT_LIMIT:],
            (completed.stderr or "")[-_OUTPUT_LIMIT:],
        )

    @staticmethod
    def _blocked(
        base: dict[str, str],
        *,
        checks: dict[str, object],
        error_code: str,
        reason: str,
    ) -> WorkspacePreflightResult:
        return WorkspacePreflightResult(
            **base,
            compatible=False,
            checks=checks,
            remediation="user_action_required",
            provider_attempt_allowed=False,
            error_code=error_code,
            reason=reason,
        )

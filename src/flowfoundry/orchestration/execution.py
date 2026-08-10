"""Durable native process handles shared by provider adapters and cancellation."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .workspace import atomic_write_json, secure_file_lock, utc_now


_ACTIVE_STATES = {"running", "cancel_requested", "terminating", "killing"}
_TERMINAL_STATES = {
    "cancelled",
    "cancel_unverified",
    "completed",
    "failed",
    "timed_out",
}


@dataclass(frozen=True)
class ManagedProcessResult:
    returncode: int | None
    stdout: str
    stderr: str
    execution_ref: str
    state: str
    timed_out: bool
    cancelled: bool
    partial_result: bool
    termination: dict[str, Any]


@dataclass(frozen=True)
class CancellationOutcome:
    execution_id: str
    provider: str
    task_id: str
    participant_id: str
    state: str
    action: str
    graceful: bool | None
    forced: bool
    partial_result: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "provider": self.provider,
            "task_id": self.task_id,
            "participant_id": self.participant_id,
            "state": self.state,
            "action": self.action,
            "graceful": self.graceful,
            "forced": self.forced,
            "partial_result": self.partial_result,
        }


class ProviderExecutionHandle:
    """One provider process plus the durable identity needed by another CLI."""

    def __init__(
        self,
        path: Path,
        *,
        process: subprocess.Popen[str] | None = None,
    ) -> None:
        self.path = path.resolve()
        self.process = process

    @classmethod
    def start(
        cls,
        command: list[str],
        *,
        provider: str,
        task_id: str,
        participant_id: str,
        task_dir: Path,
        project_root: Path,
        env: dict[str, str] | None = None,
    ) -> ProviderExecutionHandle:
        run_root = cls._run_root(task_dir)
        execution_id = uuid.uuid4().hex
        execution_dir = run_root / "executions" / execution_id
        execution_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
        process = subprocess.Popen(
            command,
            cwd=project_root,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=os.name == "posix",
        )
        identity = _process_identity(process.pid)
        metadata = {
            "schema_version": 1,
            "execution_id": execution_id,
            "run_id": cls._run_id(run_root),
            "provider": provider,
            "task_id": task_id,
            "participant_id": participant_id,
            "pid": process.pid,
            "process_group_id": identity.get(
                "process_group_id",
                process.pid if os.name == "posix" else None,
            ),
            "session_id": identity.get(
                "session_id",
                process.pid if os.name == "posix" else None,
            ),
            "process_start_ticks": identity.get("process_start_ticks"),
            "command_fingerprint": identity.get("command_fingerprint"),
            "command_identity": Path(command[0]).name,
            "cancel_capability": (
                "verified_process_group" if identity.get("verified") else "unverified"
            ),
            "state": "running",
            "started_at": utc_now(),
            "partial_result": False,
        }
        atomic_write_json(execution_dir / "execution.json", metadata)
        return cls(execution_dir / "execution.json", process=process)

    @classmethod
    def active_for_run(cls, run_path: Path) -> list[ProviderExecutionHandle]:
        handles: list[ProviderExecutionHandle] = []
        for path in sorted((run_path / "executions").glob("*/execution.json")):
            try:
                record = _read_json(path)
            except (OSError, json.JSONDecodeError, ValueError):
                continue
            if record.get("state") in _ACTIVE_STATES:
                handles.append(cls(path))
        return handles

    @classmethod
    def status_for_run(cls, run_path: Path) -> list[dict[str, Any]]:
        statuses: list[dict[str, Any]] = []
        for path in sorted((run_path / "executions").glob("*/execution.json")):
            try:
                record = _read_json(path)
            except (OSError, json.JSONDecodeError, ValueError):
                continue
            statuses.append(cls._safe_status(record))
        return statuses

    @classmethod
    def recovery_status_for_run(cls, run_path: Path) -> list[dict[str, Any]]:
        """Include verified native-process liveness for worktree reconciliation."""

        statuses: list[dict[str, Any]] = []
        for path in sorted((run_path / "executions").glob("*/execution.json")):
            try:
                record = _read_json(path)
            except (OSError, json.JSONDecodeError, ValueError):
                continue
            status = cls._safe_status(record)
            if record.get("state") in _ACTIVE_STATES:
                status["liveness"] = _verify_process(record)
            else:
                status["liveness"] = "terminal"
            statuses.append(status)
        return statuses

    @classmethod
    def cancel_active(
        cls,
        run_path: Path,
        *,
        grace_seconds: float = 2.0,
    ) -> list[CancellationOutcome]:
        outcomes: list[CancellationOutcome] = []
        for handle in cls.active_for_run(run_path):
            outcomes.append(handle.cancel(grace_seconds=grace_seconds))
        return outcomes

    def communicate(self, input_text: str | None, *, timeout_seconds: int) -> ManagedProcessResult:
        if self.process is None:
            raise RuntimeError("only the owning provider can collect process output")
        timed_out = False
        local_termination: dict[str, Any] = {}
        try:
            stdout, stderr = self.process.communicate(input=input_text, timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            local_termination = self._terminate_owned(grace_seconds=1.0)
            stdout, stderr = self.process.communicate()

        record = self.read()
        cancel_unverified = record.get("state") == "cancel_unverified"
        cancelled = bool(record.get("cancellation_requested_at")) and not cancel_unverified
        if cancel_unverified:
            state = "cancel_unverified"
        elif cancelled:
            state = "cancelled"
        elif timed_out:
            state = "timed_out"
        elif self.process.returncode == 0:
            state = "completed"
        else:
            state = "failed"
        partial_result = bool((stdout or stderr).strip()) and state in {
            "cancelled",
            "cancel_unverified",
            "timed_out",
        }
        partial_ref = None
        if partial_result:
            partial_ref = str(
                (self.path.parent / "partial-output.json").relative_to(
                    self._run_root_from_path()
                )
            )
            atomic_write_json(
                self.path.parent / "partial-output.json",
                {
                    "schema_version": 1,
                    "execution_id": record["execution_id"],
                    "partial_result": True,
                    "stdout": stdout[-40_000:],
                    "stderr": stderr[-40_000:],
                    "created_at": utc_now(),
                },
            )

        def finish(current: dict[str, Any]) -> dict[str, Any]:
            termination = dict(current.get("termination", {}))
            termination.update(local_termination)
            termination.setdefault("exit_code", self.process.returncode)
            termination["status"] = state
            current.update(
                {
                    "state": state,
                    "returncode": self.process.returncode,
                    "finished_at": utc_now(),
                    "partial_result": partial_result,
                    "partial_output_ref": partial_ref,
                    "termination": termination,
                }
            )
            return current

        record = self._update(finish)
        termination = dict(record.get("termination", {}))
        termination["status"] = state
        return ManagedProcessResult(
            returncode=self.process.returncode,
            stdout=stdout,
            stderr=stderr,
            execution_ref=str(self.path.relative_to(self._run_root_from_path())),
            state=state,
            timed_out=timed_out,
            cancelled=cancelled,
            partial_result=partial_result,
            termination=termination,
        )

    def cancel(self, *, grace_seconds: float = 2.0) -> CancellationOutcome:
        grace_seconds = max(0.0, grace_seconds)
        record = self.read()
        if record.get("state") in _TERMINAL_STATES:
            return self._outcome(record, action="no_op")

        verification = _verify_process(record)
        if verification == "missing":
            return self._outcome(record, action="already_exited")
        if verification != "verified":
            def unverified(current: dict[str, Any]) -> dict[str, Any]:
                current.update(
                    {
                        "state": "cancel_unverified",
                        "cancellation_requested_at": current.get("cancellation_requested_at")
                        or utc_now(),
                        "finished_at": utc_now(),
                        "termination": {
                            "status": "cancel_unverified",
                            "reason": "persisted process identity could not be verified",
                            "graceful": None,
                            "forced": False,
                        },
                    }
                )
                return current

            return self._outcome(self._update(unverified), action="refused_unverified")

        def requested(current: dict[str, Any]) -> dict[str, Any]:
            if current.get("state") in _TERMINAL_STATES:
                return current
            current["state"] = "cancel_requested"
            current["cancellation_requested_at"] = (
                current.get("cancellation_requested_at") or utc_now()
            )
            return current

        record = self._update(requested)
        if record.get("state") in _TERMINAL_STATES:
            return self._outcome(record, action="no_op")

        pgid = int(record["process_group_id"])
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            return self._outcome(record, action="already_exited")
        terminated_at = utc_now()
        deadline = time.monotonic() + grace_seconds
        while time.monotonic() < deadline and _verified_group_exists(record):
            time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
        group_exists = _verified_group_exists(record)
        forced = False
        if group_exists:
            forced = True
            try:
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                group_exists = False
            else:
                kill_deadline = time.monotonic() + 1.0
                while time.monotonic() < kill_deadline and _verified_group_exists(record):
                    time.sleep(0.05)
                group_exists = _verified_group_exists(record)

        def terminated(current: dict[str, Any]) -> dict[str, Any]:
            terminal_state = (
                current.get("state")
                if current.get("state") in _TERMINAL_STATES
                else None
            )
            current["termination"] = {
                "status": (
                    str(terminal_state)
                    if terminal_state is not None
                    else ("termination_failed" if group_exists else "cancel_requested")
                ),
                "method": "sigkill" if forced else "sigterm",
                "signal_sent_at": terminated_at,
                "graceful": not forced and not group_exists,
                "forced": forced,
                "process_group_gone": not group_exists,
            }
            if group_exists:
                current["state"] = "cancel_unverified"
                current["finished_at"] = utc_now()
            return current

        record = self._update(terminated)
        if not group_exists:
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                record = self.read()
                if record.get("state") in _TERMINAL_STATES:
                    break
                time.sleep(0.05)
        return self._outcome(record, action="forced" if forced else "terminated")

    def read(self) -> dict[str, Any]:
        return _read_json(self.path)

    def _terminate_owned(self, *, grace_seconds: float) -> dict[str, Any]:
        assert self.process is not None
        forced = False
        record = self.read()
        pgid = record.get("process_group_id")
        if self.process.poll() is None:
            if os.name == "posix":
                try:
                    os.killpg(int(pgid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
            else:
                self.process.terminate()
            try:
                self.process.wait(timeout=grace_seconds)
            except subprocess.TimeoutExpired:
                forced = True
        if os.name == "posix" and _verified_group_exists(record):
            forced = True
            try:
                os.killpg(int(pgid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif forced and self.process.poll() is None:
            self.process.kill()
        return {
            "method": "sigkill" if forced else "sigterm",
            "graceful": not forced,
            "forced": forced,
            "reason": "timeout",
        }

    def _update(self, mutator: Any) -> dict[str, Any]:
        with secure_file_lock(self.path.with_suffix(".lock")):
            current = self.read()
            updated = mutator(current) or current
            atomic_write_json(self.path, updated)
            return updated

    def _run_root_from_path(self) -> Path:
        return self.path.parents[2]

    @staticmethod
    def _run_root(task_dir: Path) -> Path:
        resolved = task_dir.resolve()
        if resolved.parent.name == "tasks":
            return resolved.parents[1]
        return resolved.parent

    @staticmethod
    def _run_id(run_root: Path) -> str:
        manifest = run_root / "manifest.json"
        try:
            return str(_read_json(manifest).get("run_id", run_root.name))
        except (OSError, json.JSONDecodeError, ValueError):
            return run_root.name

    @classmethod
    def _outcome(cls, record: dict[str, Any], *, action: str) -> CancellationOutcome:
        termination = record.get("termination")
        termination = termination if isinstance(termination, dict) else {}
        return CancellationOutcome(
            execution_id=str(record.get("execution_id", "unknown")),
            provider=str(record.get("provider", "unknown")),
            task_id=str(record.get("task_id", "unknown")),
            participant_id=str(record.get("participant_id", "unknown")),
            state=str(record.get("state", "unknown")),
            action=action,
            graceful=(
                termination.get("graceful")
                if isinstance(termination.get("graceful"), bool)
                else None
            ),
            forced=bool(termination.get("forced", False)),
            partial_result=bool(record.get("partial_result", False)),
        )

    @staticmethod
    def _safe_status(record: dict[str, Any]) -> dict[str, Any]:
        termination = record.get("termination")
        termination = termination if isinstance(termination, dict) else {}
        return {
            "execution_id": record.get("execution_id"),
            "provider": record.get("provider"),
            "task_id": record.get("task_id"),
            "participant_id": record.get("participant_id"),
            "pid": record.get("pid"),
            "state": record.get("state"),
            "started_at": record.get("started_at"),
            "finished_at": record.get("finished_at"),
            "cancel_requested": bool(record.get("cancellation_requested_at")),
            "termination_status": termination.get("status"),
            "graceful_termination": termination.get("graceful"),
            "forced_termination": bool(termination.get("forced", False)),
            "partial_result": bool(record.get("partial_result", False)),
        }


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def _process_identity(pid: int) -> dict[str, Any]:
    if os.name != "posix" or not Path("/proc").is_dir():
        return {"verified": False}
    try:
        stat = (Path("/proc") / str(pid) / "stat").read_text(encoding="utf-8")
        fields = stat[stat.rfind(")") + 2 :].split()
        cmdline = (Path("/proc") / str(pid) / "cmdline").read_bytes()
        return {
            "verified": True,
            "process_state": fields[0],
            "process_group_id": int(fields[2]),
            "session_id": int(fields[3]),
            "process_start_ticks": int(fields[19]),
            "command_fingerprint": hashlib.sha256(cmdline).hexdigest(),
        }
    except (FileNotFoundError, PermissionError, OSError, ValueError, IndexError):
        return {"verified": False}


def _verify_process(record: dict[str, Any]) -> str:
    pid = record.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return "unverified"
    identity = _process_identity(pid)
    if not identity.get("verified"):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return "missing"
        except (PermissionError, OSError):
            pass
        return "unverified"
    if identity.get("process_state") == "Z":
        return "missing"
    expected = (
        record.get("process_group_id"),
        record.get("session_id"),
        record.get("process_start_ticks"),
        record.get("command_fingerprint"),
    )
    actual = (
        identity.get("process_group_id"),
        identity.get("session_id"),
        identity.get("process_start_ticks"),
        identity.get("command_fingerprint"),
    )
    return "verified" if expected == actual else "unverified"


def _verified_group_exists(record: dict[str, Any]) -> bool:
    if os.name != "posix" or not Path("/proc").is_dir():
        return _verify_process(record) == "verified"
    pgid = record.get("process_group_id")
    session_id = record.get("session_id")
    if not isinstance(pgid, int) or not isinstance(session_id, int):
        return False
    for stat_path in Path("/proc").glob("[0-9]*/stat"):
        try:
            stat = stat_path.read_text(encoding="utf-8")
            fields = stat[stat.rfind(")") + 2 :].split()
            if fields[0] != "Z" and int(fields[2]) == pgid and int(fields[3]) == session_id:
                return True
        except (FileNotFoundError, PermissionError, OSError, ValueError, IndexError):
            continue
    return False

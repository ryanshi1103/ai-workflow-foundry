"""Crash-safe local run workspace with containment, locking, and redaction."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from ..workspace.policy.redact import redact_text
from .models import MeetingState, TaskPlan, TaskStatus

SCHEMA_VERSION = 1
RUN_DIRECTORIES = (
    "tasks",
    "artifacts",
    "messages",
    "reviews",
    "logs",
    "approvals",
    "provider-setup",
    "executions",
    "final",
)
_SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)[0]
    if isinstance(value, dict):
        return {str(key): redact_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_value(item) for item in value]
    return value


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


@contextmanager
def secure_file_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        os.chmod(path, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        os.chmod(path, 0o600)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def atomic_write_json(path: Path, value: Any) -> None:
    safe_value = redact_value(value)
    atomic_write_text(path, json.dumps(safe_value, indent=2, ensure_ascii=False, default=str) + "\n")


class RunWorkspace:
    def __init__(self, root: Path | str, run_id: str) -> None:
        if not _SAFE_ID.fullmatch(run_id):
            raise ValueError("run id must contain only safe portable characters")
        self.root = Path(root).resolve()
        self.run_id = run_id
        self.path = (self.root / run_id).resolve()
        if self.path.parent != self.root:
            raise ValueError("run path escapes configured root")

    @classmethod
    def create(
        cls,
        root: Path | str,
        run_id: str,
        plan: TaskPlan,
        *,
        project_root: Path | str | None = None,
    ) -> RunWorkspace:
        workspace = cls(root, run_id)
        resolved_project = Path.cwd().resolve() if project_root is None else Path(project_root).resolve()
        if not resolved_project.is_dir():
            raise ValueError(f"project workspace does not exist or is not a directory: {resolved_project}")
        workspace.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(workspace.root, 0o700)
        try:
            workspace.path.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise FileExistsError(f"run already exists: {run_id}") from exc
        for name in RUN_DIRECTORIES:
            (workspace.path / name).mkdir(mode=0o700)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "goal": plan.goal,
            "project_root": str(resolved_project),
            "plan": plan.to_dict(),
            "input_hash": stable_hash(plan.to_dict()),
            "status": "running",
            "cancel_requested": False,
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "tasks": {
                task.id: {
                    "status": TaskStatus.PENDING.value,
                    "attempts": 0,
                    "agent_id": None,
                    "input_hash": stable_hash(task.to_dict()),
                }
                for task in plan.tasks
            },
        }
        if plan.meeting_plan is not None:
            manifest["meeting"] = {
                "state": MeetingState.PLANNED.value,
                "plan": plan.meeting_plan.to_dict(),
                "participants": {
                    task_id: {
                        "status": TaskStatus.PENDING.value,
                        "agent_id": None,
                        "attempted_agents": [],
                        "call_ids": [],
                    }
                    for task_id in plan.meeting_plan.participant_task_ids
                },
                "validation": {
                    task_id: {"status": TaskStatus.PENDING.value}
                    for task_id in plan.meeting_plan.validation_task_ids
                },
                "context_pack_ref": None,
                "conflicts": [],
                "cross_reviews": {},
                "rounds_executed": [],
                "early_stopped": False,
                "early_stop_reason": None,
                "dissent": [],
                "result_ref": None,
                "cancel_requested": False,
                "cancellation": None,
                "attempt": 1,
                "budget_status": "active",
                "budget_exhaustion_reason": None,
                "budget_consumed": {
                    "agent_calls": 0,
                    "known_input_tokens": 0,
                    "known_output_tokens": 0,
                    "known_total_tokens": 0,
                    "known_cost_usd": 0.0,
                    "known_latency_ms": 0,
                    "token_measurement_complete": True,
                    "cost_measurement_complete": True,
                    "latency_measurement_complete": True,
                    "accounted_call_ids": [],
                },
                "started_at": utc_now(),
            }
        atomic_write_json(workspace.path / "manifest.json", manifest)
        for task in plan.tasks:
            task_dir = workspace.task_dir(task.id)
            task_dir.mkdir(mode=0o700)
            atomic_write_json(task_dir / "task.json", task.to_dict())
        return workspace

    def contained(self, *parts: str) -> Path:
        candidate = self.path.joinpath(*parts).resolve()
        if candidate != self.path and self.path not in candidate.parents:
            raise ValueError("path escapes run workspace")
        return candidate

    def task_dir(self, task_id: str) -> Path:
        if not _SAFE_ID.fullmatch(task_id):
            raise ValueError("invalid task id")
        return self.contained("tasks", task_id)

    def read_json(self, relative_path: str) -> dict[str, Any]:
        path = self.contained(relative_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"expected JSON object: {relative_path}")
        return data

    def manifest(self) -> dict[str, Any]:
        return self.read_json("manifest.json")

    def update_manifest(self, mutator: Any) -> dict[str, Any]:
        with secure_file_lock(self.contained(".manifest.lock")):
            manifest = self.manifest()
            updated = mutator(manifest) or manifest
            updated["updated_at"] = utc_now()
            atomic_write_json(self.contained("manifest.json"), updated)
            return updated

    def update_task(self, task_id: str, **changes: Any) -> dict[str, Any]:
        def apply(manifest: dict[str, Any]) -> dict[str, Any]:
            manifest["tasks"][task_id].update(redact_value(changes))
            return manifest

        return self.update_manifest(apply)

    def write_task_result(self, task_id: str, result: dict[str, Any]) -> Path:
        path = self.task_dir(task_id) / "result.json"
        atomic_write_json(path, result)
        return path

    def append_human_action(self, task_id: str, reason: str) -> None:
        path = self.contained("HUMAN_ACTIONS_REQUIRED.md")
        with secure_file_lock(self.contained(".human-actions.lock")):
            previous = path.read_text(encoding="utf-8") if path.exists() else "# Human Actions Required\n\n"
            atomic_write_text(path, previous + f"- `{task_id}`: {redact_text(reason)[0]}\n")

    def plan(self) -> TaskPlan:
        return TaskPlan.from_dict(self.manifest()["plan"])

    @property
    def project_root(self) -> Path:
        manifest = self.manifest()
        configured = manifest.get("project_root")
        if configured is None:
            return self.path
        project_root = Path(str(configured)).resolve()
        if not project_root.is_dir():
            raise ValueError(f"persisted project workspace is unavailable: {project_root}")
        return project_root

    @property
    def performance_memory_path(self) -> Path:
        return self.root.parent / "agent-performance.json"

    @property
    def meeting_experience_path(self) -> Path:
        return self.root.parent / "meeting-experience.json"

    @classmethod
    def open(cls, root: Path | str, run_id: str) -> RunWorkspace:
        workspace = cls(root, run_id)
        manifest = workspace.manifest()
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported run schema")
        return workspace

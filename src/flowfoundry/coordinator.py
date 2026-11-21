"""Small durable coordinator for detached local worker tasks.

This is intentionally a task board, not a second agent runtime.  Each worker
gets its own goal-runner process and task file; shared project truth remains in
the existing PROJECT_STATE, decisions, artifacts, and evidence files.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from secrets import token_hex
from typing import Any

from .core import assess_authority, build_goal_context, select_path
from .runtime import resolve_project_execution_environment
from .permissions import normalize_level, worker_level


class TaskStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_HUMAN = "WAITING_HUMAN"
    WAITING_DEPENDENCY = "WAITING_DEPENDENCY"
    VERIFYING = "VERIFYING"
    PROCESS_LOST = "PROCESS_LOST"
    TIMED_OUT = "TIMED_OUT"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class CoordinatorTask:
    task_id: str
    parent_goal: str
    worker_capability: str
    instruction: str
    context_refs: tuple[str, ...]
    dependencies: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    expected_artifact: str
    acceptance_criteria: str
    priority: str = "NORMAL"
    status: str = TaskStatus.QUEUED.value
    result_ref: str | None = None
    evidence_ref: str | None = None
    pid: int | None = None
    started_at: str | None = None
    phase: str = "QUEUED"
    timeout_seconds: int = 1800
    exit_code: int | None = None
    stdout_ref: str | None = None
    stderr_ref: str | None = None
    last_output_at: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: str | None = None
    read_only: bool = False
    session_permission_ceiling: int = 2
    effective_permission: int = 2

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CoordinatorTask":
        value = dict(value)
        for key in ("context_refs", "dependencies", "allowed_actions"):
            value[key] = tuple(value.get(key, ()))
        return cls(**value)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for key in ("context_refs", "dependencies", "allowed_actions"):
            value[key] = list(value[key])
        return value


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def tasks_root(root: Path) -> Path:
    return root / ".flowfoundry" / "coordinator" / "tasks"


def _task_path(root: Path, task_id: str) -> Path:
    if not task_id or Path(task_id).name != task_id or task_id.startswith("."):
        raise ValueError("invalid task id")
    return tasks_root(root) / f"{task_id}.json"


def load_task(root: Path, task_id: str) -> CoordinatorTask:
    path = _task_path(root, task_id)
    try:
        return CoordinatorTask.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except FileNotFoundError as exc:
        raise ValueError(f"unknown task: {task_id}") from exc


def save_task(root: Path, task: CoordinatorTask) -> CoordinatorTask:
    task.updated_at = datetime.now(timezone.utc).isoformat()
    _atomic_json(_task_path(root, task.task_id), task.to_dict())
    return task


def list_tasks(root: Path) -> list[CoordinatorTask]:
    found: list[CoordinatorTask] = []
    for path in sorted(tasks_root(root).glob("task-*.json")):
        try:
            found.append(CoordinatorTask.from_dict(json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
    return sorted(found, key=lambda task: task.created_at, reverse=True)


def _pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def reconcile_task(root: Path, task: CoordinatorTask) -> CoordinatorTask:
    if task.status == TaskStatus.RUNNING.value:
        if task.started_at and task.timeout_seconds:
            try:
                elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(task.started_at)).total_seconds()
            except ValueError:
                elapsed = 0
            if elapsed > task.timeout_seconds and _pid_alive(task.pid):
                try:
                    os.killpg(task.pid, signal.SIGTERM)
                except (ProcessLookupError, PermissionError, AttributeError):
                    pass
                task.status = TaskStatus.TIMED_OUT.value
                task.phase = TaskStatus.TIMED_OUT.value
                task.error = f"TIMED_OUT: runtime exceeded {task.timeout_seconds}s"
                save_task(root, task)
                return task
        if not _pid_alive(task.pid):
            task.status = TaskStatus.PROCESS_LOST.value
            task.phase = TaskStatus.PROCESS_LOST.value
            task.error = "PROCESS_LOST: worker process is no longer running"
            save_task(root, task)
    elif task.status == TaskStatus.VERIFYING.value and not task.result_ref:
        if _pid_alive(task.pid):
            task.status = TaskStatus.RUNNING.value
            task.phase = TaskStatus.RUNNING.value
            task.error = "Recovered invalid VERIFYING state: candidate result not yet persisted"
        else:
            task.status = TaskStatus.PROCESS_LOST.value
            task.phase = TaskStatus.PROCESS_LOST.value
            task.error = "PROCESS_LOST: verifying task has no persisted candidate result"
        save_task(root, task)
    return task


def reconcile_all(root: Path) -> list[CoordinatorTask]:
    return [reconcile_task(root, task) for task in list_tasks(root)]


def _worker_command(root: Path, task_id: str) -> list[str]:
    runtime = resolve_project_execution_environment(root)
    interpreter = runtime["python"] or sys.executable
    return [interpreter, "-m", "flowfoundry", "_coordinator-worker", task_id, "--workspace", str(root)]


def _spawn(root: Path, task: CoordinatorTask) -> CoordinatorTask:
    process = subprocess.Popen(
        _worker_command(root, task.task_id),
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    task.pid = process.pid
    task.status = TaskStatus.RUNNING.value
    task.phase = TaskStatus.RUNNING.value
    task.started_at = datetime.now(timezone.utc).isoformat()
    return save_task(root, task)


def create_task(
    root: Path, goal: str, *, priority: str = "NORMAL", start: bool = True,
    read_only: bool = False, permission_level: int | str | None = None,
) -> CoordinatorTask:
    clean_goal = goal.strip()
    if not clean_goal:
        raise ValueError("goal must not be empty")
    priority = priority.upper()
    if priority not in {"HIGH", "NORMAL", "LOW"}:
        raise ValueError("priority must be HIGH, NORMAL, or LOW")
    selection = select_path(clean_goal)
    ceiling = normalize_level(1 if read_only else permission_level)
    effective = worker_level(ceiling, selection.task_kind.value)
    authority = assess_authority(clean_goal)
    context = build_goal_context(root, clean_goal)
    task = CoordinatorTask(
        task_id=f"task-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{token_hex(3)}",
        parent_goal=clean_goal,
        worker_capability=selection.task_kind.value,
        instruction=clean_goal,
        context_refs=tuple(context.instruction_files) + tuple(item.id for item in context.decisions),
        dependencies=(),
        allowed_actions=("local",) if not authority.human_required else ("prepare-only",),
        expected_artifact=selection.expected_result,
        acceptance_criteria=selection.verification_hint,
        priority=priority,
        read_only=read_only or ceiling == 1,
        session_permission_ceiling=ceiling,
        effective_permission=effective,
        status=(TaskStatus.WAITING_HUMAN.value if authority.human_required else TaskStatus.QUEUED.value),
        error=("Human approval required: " + ", ".join(authority.human_actions)) if authority.human_required else None,
    )
    save_task(root, task)
    if start and task.status == TaskStatus.QUEUED.value:
        return _spawn(root, task)
    return task


def approve_task(root: Path, task_id: str) -> CoordinatorTask:
    task = load_task(root, task_id)
    if task.status != TaskStatus.WAITING_HUMAN.value:
        raise ValueError(f"task is not waiting for human approval: {task_id}")
    task.status = TaskStatus.QUEUED.value
    task.error = None
    return _spawn(root, task)


def cancel_task(root: Path, task_id: str) -> CoordinatorTask:
    task = load_task(root, task_id)
    if task.status in {TaskStatus.COMPLETED.value, TaskStatus.PARTIAL.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value}:
        return task
    if task.pid and _pid_alive(task.pid):
        try:
            os.killpg(task.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, AttributeError):
            pass
    task.status = TaskStatus.CANCELLED.value
    task.error = "Cancelled by human."
    return save_task(root, task)


def worker_main(root: Path, task_id: str) -> int:
    """Run exactly one detached task; this is an internal process entrypoint."""
    task = load_task(root, task_id)
    if task.status == TaskStatus.CANCELLED.value:
        return 0
    task.status = TaskStatus.RUNNING.value
    task.phase = TaskStatus.RUNNING.value
    task.started_at = task.started_at or datetime.now(timezone.utc).isoformat()
    save_task(root, task)
    diagnostics = root / ".flowfoundry" / "coordinator" / "diagnostics"
    diagnostics.mkdir(parents=True, exist_ok=True)
    stdout_path = diagnostics / f"{task.task_id}.stdout.log"
    stderr_path = diagnostics / f"{task.task_id}.stderr.log"
    task.stdout_ref = str(stdout_path.relative_to(root))
    task.stderr_ref = str(stderr_path.relative_to(root))
    save_task(root, task)
    try:
        from .goal_runner import run_goal

        with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code, result = run_goal(
                    task.instruction,
                    root=root,
                    runs_root=root / ".flowfoundry" / "do",
                    read_only=task.read_only or task.effective_permission <= 1,
                    permission_level=task.effective_permission,
                    verbose=False,
                    timeout_seconds=task.timeout_seconds,
                )
        # A human cancellation remains authoritative if the executor returns late.
        current = load_task(root, task.task_id)
        if current.status == TaskStatus.CANCELLED.value:
            return code
        task.result_ref = str(Path(".flowfoundry") / "do" / result["run_id"] / "result.json")
        task.evidence_ref = task.result_ref
        task.exit_code = code
        task.phase = TaskStatus.VERIFYING.value
        save_task(root, task)
        status = result.get("status", "FAILED")
        task.status = {
            "PASS": TaskStatus.COMPLETED.value,
            "PARTIAL": TaskStatus.PARTIAL.value,
            "UNKNOWN": TaskStatus.PARTIAL.value,
        }.get(status, TaskStatus.FAILED.value)
        task.error = None if code == 0 else result.get("human", {}).get("needs_you")
        task.phase = task.status
        save_task(root, task)
        return code
    except Exception as exc:  # keep durable failure visible after process exit
        # Stopping an executor can raise instead of returning a result. Preserve
        # the human's durable cancellation in either completion path.
        current = load_task(root, task.task_id)
        if current.status == TaskStatus.CANCELLED.value:
            return 1
        task.status = TaskStatus.FAILED.value
        task.phase = TaskStatus.FAILED.value
        task.error = f"{type(exc).__name__}: {exc}"
        save_task(root, task)
        return 1


def task_summary(root: Path, task: CoordinatorTask) -> dict[str, Any]:
    task = reconcile_task(root, task)
    return {
        "task_id": task.task_id,
        "status": task.status,
        "priority": task.priority,
        "capability": task.worker_capability,
        "session_permission_ceiling": task.session_permission_ceiling,
        "effective_permission": task.effective_permission,
        "goal": task.parent_goal,
        "pid": task.pid,
        "result": task.result_ref,
        "error": task.error,
        "updated_at": task.updated_at,
        "phase": task.phase,
        "process_alive": _pid_alive(task.pid) if task.status in {TaskStatus.RUNNING.value, TaskStatus.VERIFYING.value} else False,
        "result_available": bool(task.result_ref),
        "started_at": task.started_at,
        "timeout_seconds": task.timeout_seconds,
    }


def result_for_task(root: Path, task_id: str) -> dict[str, Any]:
    task = reconcile_task(root, load_task(root, task_id))
    if not task.result_ref:
        return task_summary(root, task)
    result_path = (root / task.result_ref).resolve()
    if root.resolve() not in result_path.parents:
        raise ValueError("task result escapes project root")
    try:
        return json.loads(result_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return task_summary(root, task)

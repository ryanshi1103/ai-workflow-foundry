"""Small value-first path: hand one goal to an existing coding harness."""

from __future__ import annotations

import json
import os
import queue
import shlex
import shutil
import subprocess
import threading
import time
from contextlib import nullcontext
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from secrets import token_hex
from typing import Any, Callable, Sequence, TextIO

from .broker import broker_goal
from .core import assess_authority, build_goal_context, evaluate_result, select_path
from .instructions import CORE_INSTRUCTION
from .executors import ExecutorResult
from .runtime import resolve_project_execution_environment
from .permissions import normalize_level, worker_level


SAFETY_BOUNDARY = CORE_INSTRUCTION

ProgressCallback = Callable[[str], None]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def project_root(value: Path | None = None) -> Path:
    candidate = value or Path(os.environ.get("CC_ACTIVE_PROJECT", Path.cwd()))
    resolved = candidate.expanduser().resolve()
    if not resolved.is_dir():
        raise ValueError(f"project root does not exist: {resolved}")
    return resolved


def environment_status(root: Path) -> dict[str, Any]:
    codex = shutil.which("codex")
    git = shutil.which("git")
    version = None
    authenticated = False
    if codex:
        completed = subprocess.run(
            [codex, "--version"], text=True, capture_output=True, timeout=10
        )
        if completed.returncode == 0:
            version = completed.stdout.strip()
        completed = subprocess.run(
            [codex, "login", "status"], text=True, capture_output=True, timeout=10
        )
        authenticated = completed.returncode == 0
    is_git = False
    if git:
        completed = subprocess.run(
            [git, "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=10,
        )
        is_git = completed.returncode == 0 and completed.stdout.strip() == "true"
    return {
        "ready": bool(codex and authenticated and is_git),
        "project_root": str(root),
        "executor": "codex",
        "executor_path": codex,
        "executor_version": version,
        "executor_authenticated": authenticated,
        "git_workspace": is_git,
        "path": "goal -> codex -> deterministic evidence",
    }


def _git_status(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        timeout=20,
    )
    if completed.returncode:
        return []
    return sorted(
        item.decode("utf-8", "replace")
        for item in completed.stdout.split(b"\0")
        if item
    )


def _status_paths(status: Sequence[str]) -> dict[str, str]:
    """Map porcelain entries to paths without exposing Git's status prefix."""
    paths: dict[str, str] = {}
    for entry in status:
        if len(entry) < 4:
            continue
        code = entry[:2]
        if any(character not in " MADRCU?!T" for character in code):
            # Rename/copy source records in porcelain v1 -z have no prefix.
            continue
        path = entry[3:]
        if path:
            paths[path] = code
    return paths


def _git_head(root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=20,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _git_changed_between(root: Path, before: str | None, after: str | None) -> set[str]:
    if not before or not after or before == after:
        return set()
    completed = subprocess.run(
        ["git", "diff", "--name-only", "-z", before, after],
        cwd=root,
        capture_output=True,
        timeout=30,
    )
    if completed.returncode:
        return set()
    return {
        item.decode("utf-8", "replace")
        for item in completed.stdout.split(b"\0")
        if item
    }


def _working_file(root: Path, relative: str) -> bytes | None:
    path = (root / relative).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        return None
    try:
        return path.read_bytes()
    except OSError:
        return None


def _git_file(root: Path, revision: str | None, relative: str) -> bytes | None:
    if not revision:
        return None
    completed = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=root,
        capture_output=True,
        timeout=30,
    )
    return completed.stdout if completed.returncode == 0 else None


def _workspace_baseline(root: Path, status: Sequence[str]) -> dict[str, bytes | None]:
    """Keep only pre-existing dirty files so Founder work can be subtracted."""
    return {path: _working_file(root, path) for path in _status_paths(status)}


def _decode_diff_lines(value: bytes | None) -> list[str] | None:
    if value is None:
        return []
    if b"\0" in value:
        return None
    return value.decode("utf-8", "replace").splitlines(keepends=True)


def _generated_change(path: str) -> bool:
    parts = Path(path).parts
    return (
        "__pycache__" in parts
        or path.endswith((".pyc", ".pyo"))
        or any(part in {"node_modules", ".pytest_cache"} for part in parts)
    )


def _repository_changes(
    root: Path,
    *,
    before_status: Sequence[str],
    before_head: str | None,
    before_dirty: dict[str, bytes | None],
    after_status: Sequence[str],
    after_head: str | None,
    max_diff_chars: int = 12_000,
) -> tuple[list[str], str, bool]:
    """Return Worker-owned paths and a bounded diff against the exact pre-run state."""
    before_paths = _status_paths(before_status)
    after_paths = _status_paths(after_status)
    candidates = set(before_paths) | set(after_paths)
    candidates.update(_git_changed_between(root, before_head, after_head))

    changed: list[tuple[str, bytes | None, bytes | None]] = []
    for path in sorted(candidates):
        before = (
            before_dirty[path]
            if path in before_dirty
            else _git_file(root, before_head, path)
        )
        after = _working_file(root, path)
        if before != after:
            changed.append((path, before, after))

    changed.sort(key=lambda item: (_generated_change(item[0]), item[0]))
    parts: list[str] = []
    truncated = False
    for path, before, after in changed:
        before_lines = _decode_diff_lines(before)
        after_lines = _decode_diff_lines(after)
        if before_lines is None or after_lines is None:
            # Binary/build artifacts stay in the honest changed-file list but
            # do not displace useful source hunks in the compact code section.
            continue
        addition = "".join(
            unified_diff(
                before_lines,
                after_lines,
                fromfile=(f"a/{path}" if before is not None else "/dev/null"),
                tofile=(f"b/{path}" if after is not None else "/dev/null"),
                n=3,
            )
        )
        remaining = max_diff_chars - sum(len(part) for part in parts)
        if remaining <= 0:
            truncated = True
            break
        if len(addition) > remaining:
            parts.append(addition[:remaining].rstrip() + "\n… diff truncated …\n")
            truncated = True
            break
        parts.append(addition)
    return [path for path, _, _ in changed], "".join(parts).strip(), truncated


def _read_previous(runs_root: Path, run_id: str) -> dict[str, Any]:
    result_path = (runs_root / run_id / "result.json").resolve()
    if runs_root.resolve() not in result_path.parents:
        raise ValueError("resume run id escapes the runs root")
    try:
        value = json.loads(result_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"unknown run id: {run_id}") from exc
    if not isinstance(value, dict) or not value.get("thread_id"):
        raise ValueError(f"run has no resumable Codex thread: {run_id}")
    return value


def _command(root: Path, *, read_only: bool, thread_id: str | None) -> list[str]:
    runtime = resolve_project_execution_environment(root)
    codex = shutil.which("codex", path=runtime["env"].get("PATH"))
    if not codex:
        raise ValueError("Codex CLI is not installed")
    if thread_id:
        return [
            codex,
            "exec",
            "resume",
            "--json",
            "-c",
            'approval_policy="never"',
            "-c",
            f'sandbox_mode="{"read-only" if read_only else "workspace-write"}"',
            thread_id,
            "-",
        ]
    return [
        codex,
        "exec",
        "--json",
        "--color",
        "never",
        "--sandbox",
        "read-only" if read_only else "workspace-write",
        "-c",
        'approval_policy="never"',
        "-C",
        str(root),
        "-",
    ]


def _parse_events(text: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    events: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "thread_id": None,
        "final_message": "",
        "usage": None,
        "commands": [],
    }
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        events.append(event)
        event_type = event.get("type")
        if event_type == "thread.started":
            summary["thread_id"] = event.get("thread_id")
        elif event_type == "turn.completed":
            summary["usage"] = event.get("usage")
        elif event_type == "item.completed" and isinstance(event.get("item"), dict):
            item = event["item"]
            if item.get("type") == "agent_message":
                summary["final_message"] = str(item.get("text", ""))
            elif item.get("type") == "command_execution":
                summary["commands"].append(
                    {
                        key: item.get(key)
                        for key in ("command", "status", "exit_code")
                        if key in item
                    }
                )
    return events, summary


def _compact_text(value: object, limit: int = 120) -> str:
    printable = "".join(character if character.isprintable() else " " for character in str(value))
    compact = " ".join(printable.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _event_progress(event: dict[str, Any]) -> str | None:
    event_type = event.get("type")
    if event_type == "thread.started":
        return "executor session ready"
    if event_type == "turn.completed":
        usage = event.get("usage")
        if isinstance(usage, dict):
            input_tokens = usage.get("input_tokens")
            output_tokens = usage.get("output_tokens")
            if input_tokens is not None and output_tokens is not None:
                return (
                    "executor turn complete "
                    f"(input={input_tokens}, output={output_tokens} tokens)"
                )
        return "executor turn complete"
    if event_type not in {"item.started", "item.completed"}:
        return None
    item = event.get("item")
    if not isinstance(item, dict) or item.get("type") != "command_execution":
        return None
    command = _compact_text(item.get("command", ""))
    if event_type == "item.started":
        return f"running: {command}" if command else "running executor command"
    exit_code = item.get("exit_code")
    outcome = "passed" if exit_code == 0 else f"failed (exit {exit_code})"
    return f"command {outcome}: {command}" if command else f"command {outcome}"


def _emit_progress(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        try:
            progress(message)
        except Exception:
            # Progress is advisory and must not interrupt the executor or evidence capture.
            pass


def _drain_stream(
    kind: str,
    stream: TextIO,
    output: queue.Queue[tuple[str, str | None]],
) -> None:
    try:
        for line in stream:
            output.put((kind, line))
    finally:
        stream.close()
        output.put((kind, None))


def _stream_executor(
    command: Sequence[str],
    *,
    root: Path,
    prompt: str,
    timeout_seconds: int,
    events_path: Path | None,
    stderr_path: Path | None,
    progress: ProgressCallback | None,
    environment: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    process = subprocess.Popen(
        list(command),
        cwd=root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=environment,
    )
    if process.stdin is None or process.stdout is None or process.stderr is None:
        process.kill()
        raise OSError("could not open Codex process streams")
    process.stdin.write(prompt)
    process.stdin.close()

    output: queue.Queue[tuple[str, str | None]] = queue.Queue()
    readers = (
        threading.Thread(
            target=_drain_stream,
            args=("stdout", process.stdout, output),
            daemon=True,
        ),
        threading.Thread(
            target=_drain_stream,
            args=("stderr", process.stderr, output),
            daemon=True,
        ),
    )
    for reader in readers:
        reader.start()

    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    open_streams = {"stdout", "stderr"}
    deadline = time.monotonic() + timeout_seconds
    timed_out = False
    events_context = (
        events_path.open("w", encoding="utf-8") if events_path else nullcontext(None)
    )
    stderr_context = (
        stderr_path.open("w", encoding="utf-8") if stderr_path else nullcontext(None)
    )
    with events_context as events_file, stderr_context as stderr_file:
        while open_streams:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            try:
                kind, line = output.get(timeout=min(0.1, remaining))
            except queue.Empty:
                continue
            if line is None:
                open_streams.discard(kind)
                continue
            if kind == "stdout":
                stdout_parts.append(line)
                if events_file:
                    events_file.write(line)
                    events_file.flush()
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict):
                    message = _event_progress(event)
                    if message:
                        _emit_progress(progress, message)
            else:
                stderr_parts.append(line)
                if stderr_file:
                    stderr_file.write(line)
                    stderr_file.flush()

        if not timed_out:
            remaining = max(0.0, deadline - time.monotonic())
            try:
                return_code = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                timed_out = True

        if timed_out:
            process.kill()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            timeout_message = f"FlowFoundry timed out after {timeout_seconds}s\n"
            stderr_parts.append(timeout_message)
            if stderr_file:
                stderr_file.write(timeout_message)
                stderr_file.flush()
            return_code = 124

        for reader in readers:
            reader.join(timeout=1)
        while True:
            try:
                kind, line = output.get_nowait()
            except queue.Empty:
                break
            if line is None:
                continue
            if kind == "stdout":
                stdout_parts.append(line)
                if events_file:
                    events_file.write(line)
            else:
                stderr_parts.append(line)
                if stderr_file:
                    stderr_file.write(line)

    return return_code, "".join(stdout_parts), "".join(stderr_parts)


def _run_checks(
    root: Path,
    checks: Sequence[str],
    progress: ProgressCallback | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    environment = resolve_project_execution_environment(root)["env"]
    for check in checks:
        argv = shlex.split(check)
        if not argv:
            continue
        _emit_progress(progress, f"checking: {_compact_text(check)}")
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                argv,
                cwd=root,
                text=True,
                capture_output=True,
                timeout=300,
                env=environment,
            )
            result = {
                "command": check,
                "exit_code": completed.returncode,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "stdout_tail": completed.stdout[-4000:],
                "stderr_tail": completed.stderr[-4000:],
            }
            results.append(result)
            outcome = "passed" if completed.returncode == 0 else "failed"
            _emit_progress(
                progress,
                f"check {outcome} ({result['elapsed_seconds']}s): {_compact_text(check)}",
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            result = {
                "command": check,
                "exit_code": None,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "error": str(exc),
            }
            results.append(result)
            _emit_progress(
                progress,
                f"check error ({result['elapsed_seconds']}s): {_compact_text(check)}",
            )
    return results


def run_goal(
    goal: str,
    *,
    root: Path,
    runs_root: Path,
    read_only: bool = False,
    permission_level: int | str | None = None,
    resume: str | None = None,
    checks: Sequence[str] = (),
    timeout_seconds: int = 1800,
    dry_run: bool = False,
    verbose: bool = False,
    progress: ProgressCallback | None = None,
) -> tuple[int, dict[str, Any]]:
    clean_goal = goal.strip()
    if not clean_goal:
        raise ValueError("goal must not be empty")
    root = project_root(root)
    environment = resolve_project_execution_environment(root)
    runs_root = runs_root.resolve()
    previous = _read_previous(runs_root, resume) if resume else None
    if previous and Path(str(previous["project_root"])).resolve() != root:
        raise ValueError("a resumed run must use its original project root")
    thread_id = str(previous["thread_id"]) if previous else None
    context = build_goal_context(root, clean_goal)
    recorded_kind = (
        previous.get("selection", {}).get("task_kind")
        if isinstance(previous, dict)
        and isinstance(previous.get("selection"), dict)
        else None
    )
    previous_kind = recorded_kind if isinstance(recorded_kind, str) else None
    selection = select_path(clean_goal, requested_capability=previous_kind)
    ceiling = normalize_level(1 if read_only else permission_level)
    effective_permission = worker_level(ceiling, selection.task_kind.value)
    worker_read_only = effective_permission <= 1
    if worker_read_only and checks:
        raise ValueError("custom --check commands require workspace-write mode")
    command = _command(root, read_only=worker_read_only, thread_id=thread_id)
    authority = assess_authority(clean_goal)
    broker = broker_goal(
        goal=clean_goal,
        relevant_context=context.prompt_section(),
        capabilities=selection.required_capabilities,
        expected_result=selection.expected_result,
        verification_hint=selection.verification_hint,
        requested=selection.broker_requested,
    )
    authority_text = (
        "Prepare but do not perform these human-authorized actions: "
        + ", ".join(authority.human_actions)
        if authority.human_required
        else "No high-impact external action was requested."
    )
    prompt = (
        f"GOAL:\n{clean_goal}\n\n"
        f"CONTEXT:\n{context.prompt_section()}\n\n"
        f"CONSTRAINTS:\n{SAFETY_BOUNDARY}\n"
        f"DONE:\n{broker.decision.verification_hint or selection.verification_hint}\n"
        f"AUTHORITY:\n{authority_text}\n"
        f"CAPABILITY NOTE: {', '.join(broker.decision.selected_capabilities)}; {broker.decision.reason}\n"
        "\nFINAL RESPONSE CONTRACT:\n"
        "Your final response is shown directly to the Founder as the responsible "
        "Agent's report. Give the substantive answer and do not reduce it to a "
        "generic completion sentence. Report conclusions and useful rationale, not "
        "hidden chain-of-thought. For coding work, when relevant, explain what you "
        "inspected, the root cause, what changed, important files and implementation "
        "choices, compact code or diff excerpts, exact commands/tests and outcomes, "
        "remaining limitations, and what the Founder should know next. Omit headings "
        "that do not fit the task. Do not ask FlowFoundry or another model to rewrite "
        "your report.\n"
    )
    if dry_run:
        return 0, {
            "status": "dry_run",
            "goal": clean_goal,
            "project_root": str(root),
            "executor": "codex",
            "sandbox": "read-only" if worker_read_only else "workspace-write",
            "resume_of": resume,
            "command": command,
            "selection": {
                "task_kind": selection.task_kind.value,
                "capabilities": list(broker.decision.selected_capabilities),
                "reason": broker.decision.reason,
                "broker": broker.status,
                "session_permission_ceiling": ceiling,
                "effective_permission": effective_permission,
            },
            "relevant_decisions": [decision.id for decision in context.decisions],
            "human_actions": list(authority.human_actions),
        }

    run_id = f"goal-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{token_hex(3)}"
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    started_at = utc_now()
    before_status = _git_status(root)
    before_head = _git_head(root)
    before_dirty = _workspace_baseline(root, before_status)
    started = time.perf_counter()
    return_code, stdout, stderr = _stream_executor(
        command,
        root=root,
        prompt=prompt,
        timeout_seconds=timeout_seconds,
        events_path=run_dir / "events.jsonl" if verbose else None,
        stderr_path=run_dir / "stderr.log" if verbose else None,
        progress=progress,
        environment=environment["env"],
    )

    elapsed = round(time.perf_counter() - started, 3)
    _, parsed = _parse_events(stdout)
    executor_result = ExecutorResult(
        status=("completed" if return_code == 0 else "failed"),
        output=parsed["final_message"],
        agent_response=parsed["final_message"],
        usage=parsed["usage"],
        evidence=tuple(parsed["commands"]),
        errors=((stderr[-4000:],) if stderr.strip() else ()),
    )
    after_status = _git_status(root)
    after_head = _git_head(root)
    changed_paths, change_diff, diff_truncated = _repository_changes(
        root,
        before_status=before_status,
        before_head=before_head,
        before_dirty=before_dirty,
        after_status=after_status,
        after_head=after_head,
    )
    flowfoundry_checks = _run_checks(
        root, ("git diff --check", *checks), progress=progress
    )
    executor_succeeded = bool(return_code == 0 and executor_result.agent_response)
    evaluation = evaluate_result(
        task_kind=selection.task_kind,
        executor_succeeded=executor_succeeded,
        output=executor_result.agent_response,
        commands=executor_result.evidence,
        checks=flowfoundry_checks,
        changed_paths=changed_paths,
    )
    status = evaluation.status.value
    human_need = (
        "Human approval is required for: " + ", ".join(authority.human_actions)
        if authority.human_required
        else evaluation.needs_user
    )
    result = {
        "schema_version": 3,
        "run_id": run_id,
        "goal": clean_goal,
        "project_root": str(root),
        "executor": "codex",
        "responsible_agent": "Codex",
        "sandbox": "read-only" if worker_read_only else "workspace-write",
        "status": status,
        "execution_status": "completed" if executor_succeeded else "failed",
        "verification": evaluation.to_dict(),
        "return_code": return_code,
        "thread_id": parsed["thread_id"] or thread_id,
        "resume_of": resume,
        "started_at": started_at,
        "finished_at": utc_now(),
        "elapsed_seconds": elapsed,
        "agent_response": executor_result.agent_response,
        # Compatibility aliases for version 1/2 readers. New presentation code
        # must prefer agent_response and never replace it with evaluator prose.
        "result": executor_result.agent_response,
        # Kept for version-1 resume readers and callers during the transition.
        "final_message": executor_result.agent_response,
        "usage": executor_result.usage,
        "selection": {
            "task_kind": selection.task_kind.value,
            "capabilities": list(broker.decision.selected_capabilities),
            "reason": broker.decision.reason,
            "broker_status": broker.status,
            "broker_used": broker.used,
            "broker_reason": broker.reason,
            "needs_second_opinion": broker.decision.needs_second_opinion,
            "session_permission_ceiling": ceiling,
            "effective_permission": effective_permission,
        },
        "context": {
            "instruction_files": list(context.instruction_files),
            "decisions": [
                {
                    "id": decision.id,
                    "status": decision.status,
                    "provenance": decision.provenance,
                }
                for decision in context.decisions
            ],
        },
        "changes": {
            "paths": changed_paths,
            "diff": change_diff,
            "diff_truncated": diff_truncated,
            "candidate_not_truth": bool(changed_paths and not worker_read_only),
        },
        "human": {
            "decision_required": authority.human_required,
            "actions": list(authority.human_actions),
            "needs_you": human_need,
        },
        "evidence": {
            "result": "result.json",
        },
    }
    if verbose:
        result["debug"] = {
            "events": "events.jsonl",
            "stderr": "stderr.log",
            "commands": parsed["commands"],
            "working_tree_before": before_status,
            "working_tree_after": after_status,
            "stderr_tail": stderr[-4000:],
        }
    (run_dir / "result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return (1 if evaluation.status.value == "FAIL" else 0), result

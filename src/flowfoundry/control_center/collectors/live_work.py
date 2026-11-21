"""FlowFoundry Live Work from coordinator tasks and result.json. No Langfuse."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ...coordinator import list_tasks
from ..model import FailureState, Kind, Observation, Quality, SourceClass, isoformat

PROVIDER = "flowfoundry"
SOURCE = "flowfoundry.coordinator+result.json"


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None
    return value if isinstance(value, dict) else None


def _latest_result(root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    runs = root / ".flowfoundry" / "do"
    if not runs.is_dir():
        return None, None
    newest: tuple[float, Path] | None = None
    for path in runs.glob("goal-*/result.json"):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if newest is None or mtime > newest[0]:
            newest = (mtime, path)
    if newest is None:
        return None, None
    return newest[1], _load_json(newest[1])


def _operation_from_result(result: dict[str, Any]) -> str | None:
    verification = result.get("verification")
    if isinstance(verification, dict):
        evidence = verification.get("evidence")
        if isinstance(evidence, list):
            for item in reversed(evidence):
                if isinstance(item, dict) and item.get("kind") == "command":
                    command = item.get("command")
                    if command:
                        return str(command)[:240]
    return None


def _tokens(result: dict[str, Any]) -> dict[str, Any] | None:
    usage = result.get("usage")
    if not isinstance(usage, dict):
        return None
    return {
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "cached_input_tokens": usage.get("cached_input_tokens"),
        "cache_write_input_tokens": usage.get("cache_write_input_tokens"),
        "reasoning_output_tokens": usage.get("reasoning_output_tokens"),
    }


_HIDDEN_EVENT_KINDS = {
    "thought",
    "thinking",
    "reasoning",
    "agent_response",
    "hidden",
}


def _events_from_result(result: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Surface observable evidence only. Hidden model text stays out."""
    if not isinstance(result, dict):
        return []
    verification = result.get("verification")
    evidence = verification.get("evidence") if isinstance(verification, dict) else None
    if not isinstance(evidence, list):
        return []
    events: list[dict[str, Any]] = []
    for item in evidence[-12:]:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "evidence").strip().lower() or "evidence"
        if kind in _HIDDEN_EVENT_KINDS:
            continue
        detail = None
        for key in ("command", "path", "tool", "name", "file", "summary"):
            value = item.get(key)
            if value:
                detail = str(value)[:240]
                break
        events.append({"kind": kind, "detail": detail})
    return events


def collect_live_work(*, now: datetime, root: Path) -> Observation:
    task_payload: dict[str, Any] | None = None
    tasks = list_tasks(root)
    live = next(
        (
            task
            for task in tasks
            if task.status in {"RUNNING", "VERIFYING", "QUEUED", "WAITING_HUMAN"}
        ),
        tasks[0] if tasks else None,
    )
    result = None
    result_path = None
    if live is not None:
        task_payload = {
            "task_id": live.task_id,
            "goal": live.parent_goal,
            # Detached coordinator tasks currently execute through Codex. The
            # task's worker_capability is a task kind (for example "coding"),
            # not a provider identity.
            "responsible_worker": "Codex",
            "worker_capability": live.worker_capability,
            "specialist": None,
            "run_state": live.status,
            "phase": live.phase,
            "updated_at": live.updated_at,
            "error": live.error,
        }
        if live.result_ref:
            candidate = (root / live.result_ref).resolve()
            try:
                if root.resolve() in candidate.parents:
                    result = _load_json(candidate)
                    result_path = live.result_ref
            except OSError:
                result = None
    # Never overlay a currently running task with an unrelated older result.
    if result is None and live is None:
        result_path_obj, result = _latest_result(root)
        if result_path_obj is not None:
            try:
                result_path = str(result_path_obj.relative_to(root))
            except ValueError:
                result_path = str(result_path_obj)

    if live is None and result is None:
        return Observation.unknown(
            kind=Kind.WORK.value,
            provider=PROVIDER,
            source=SOURCE,
            now=now,
            failure_state=FailureState.AVAILABLE.value,
            last_error=None,
            source_class=SourceClass.LOCAL.value,
            payload={
                "goal": None,
                "responsible_worker": None,
                "specialist": None,
                "run_state": "IDLE",
                "operation": None,
                "model": None,
                "provider": None,
                "tokens": None,
                "latency_seconds": None,
                "evidence_path": None,
                "events": [],
                "updated_at": isoformat(now),
            },
        )

    goal = None
    worker = None
    specialist = None
    state = "IDLE"
    model = None
    provider = None
    latency = None
    updated_at = isoformat(now)
    if task_payload:
        goal = task_payload.get("goal")
        worker = task_payload.get("responsible_worker")
        state = str(task_payload.get("run_state") or "UNKNOWN")
        updated_at = task_payload.get("updated_at") or updated_at
    if isinstance(result, dict) and "run_id" in result:
        goal = result.get("goal") or goal
        worker = result.get("responsible_agent") or result.get("executor") or worker
        specialist = result.get("specialist")
        state = str(result.get("execution_status") or result.get("status") or state)
        model = result.get("model")
        provider = result.get("executor")
        latency = result.get("elapsed_seconds")
        updated_at = (
            result.get("finished_at")
            or result.get("completed_at")
            or result.get("generated_at")
            or updated_at
        )
        selection = result.get("selection")
        if isinstance(selection, dict) and not worker:
            worker = selection.get("task_kind")
    operation = _operation_from_result(result) if isinstance(result, dict) else None
    events = _events_from_result(result if isinstance(result, dict) else None)
    if task_payload and operation is None:
        # The durable status is authoritative. Older task records can retain
        # an initial phase even after moving to WAITING_HUMAN or another state.
        operation = f"FlowFoundry task state: {state}"
        events.insert(0, {"kind": "state_transition", "detail": state})
    tokens = _tokens(result) if isinstance(result, dict) else None
    if worker and str(worker).casefold() == "codex":
        worker = "Codex"
    return Observation(
        kind=Kind.WORK.value,
        provider=PROVIDER,
        account_label="local",
        quality=Quality.EXACT_LOCAL.value,
        source=SOURCE,
        observed_at=isoformat(now) or "",
        payload={
            "goal": goal,
            "responsible_worker": worker,
            "specialist": specialist,
            "run_state": state,
            "operation": operation,
            "model": model,
            "provider": provider,
            "tokens": tokens,
            "latency_seconds": latency,
            "evidence_path": result_path,
            "events": events,
            "updated_at": updated_at,
        },
        source_class=SourceClass.LOCAL.value,
        failure_state=FailureState.AVAILABLE.value,
    )

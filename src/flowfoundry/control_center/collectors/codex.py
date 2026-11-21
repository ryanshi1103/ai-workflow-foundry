"""Codex quota via the installed CLI app-server. Never reads auth.json."""

from __future__ import annotations

import json
import select
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from ..model import (
    FailureState,
    Kind,
    Observation,
    Quality,
    SourceClass,
    isoformat,
    parse_datetime,
    remaining_from_used_percent,
)

PROVIDER = "openai"
SOURCE = "codex.app-server.account/rateLimits/read"
APP_SERVER_TIMEOUT = 12


def _window_label(window: dict[str, Any], fallback: str) -> str:
    minutes = window.get("windowDurationMins")
    try:
        value = int(minutes)
    except (TypeError, ValueError):
        return fallback
    if 240 <= value <= 360:
        return "5h"
    if 9000 <= value <= 12000:
        return "weekly"
    return f"{value}m"


def parse_rate_limits(payload: Any, *, now: datetime) -> Observation:
    """Parse an `account/rateLimits/read` result object."""
    if not isinstance(payload, dict):
        return Observation.unknown(
            kind=Kind.QUOTA.value,
            provider=PROVIDER,
            source=SOURCE,
            now=now,
            failure_state=FailureState.PROVIDER_ERROR.value,
            last_error="malformed rate-limit payload",
            source_class=SourceClass.OFFICIAL_UNSTABLE.value,
        )
    snapshot = payload.get("rateLimits")
    if not isinstance(snapshot, dict):
        snapshot = {}
    windows: list[dict[str, Any]] = []
    for key, fallback in (("primary", "5h"), ("secondary", "weekly")):
        raw = snapshot.get(key)
        if not isinstance(raw, dict):
            windows.append(
                {
                    "id": fallback,
                    "used_percent": None,
                    "remaining_percent": None,
                    "resets_at": None,
                    "quality": Quality.UNKNOWN.value,
                }
            )
            continue
        used = raw.get("usedPercent")
        remaining = remaining_from_used_percent(used)
        windows.append(
            {
                "id": _window_label(raw, fallback),
                "used_percent": used if isinstance(used, int) else None,
                "remaining_percent": remaining,
                "resets_at": isoformat(parse_datetime(raw.get("resetsAt"))),
                "window_duration_mins": raw.get("windowDurationMins"),
                "quality": Quality.EXACT_OFFICIAL.value,
            }
        )
    reached = snapshot.get("rateLimitReachedType")
    ordinary = payload.get("ordinaryUsageAllowed")
    plan = snapshot.get("planType")
    failure = FailureState.AVAILABLE.value
    if reached in {"rate_limit_reached"}:
        failure = FailureState.RATE_LIMITED.value
    elif reached:
        failure = FailureState.QUOTA_EXHAUSTED.value
    elif any(item.get("remaining_percent") == 0 for item in windows if item.get("remaining_percent") is not None):
        failure = FailureState.QUOTA_EXHAUSTED.value
    if ordinary is False and not reached:
        failure = FailureState.UNSUPPORTED_ACCOUNT_TIER.value
    exact = any(item.get("remaining_percent") is not None for item in windows)
    if not exact and plan is None and not snapshot:
        return Observation.unknown(
            kind=Kind.QUOTA.value,
            provider=PROVIDER,
            source=SOURCE,
            now=now,
            failure_state=FailureState.UNSUPPORTED_ACCOUNT_TIER.value,
            last_error="no rate-limit windows in app-server response",
            source_class=SourceClass.OFFICIAL_UNSTABLE.value,
            payload={"windows": windows, "plan_type": plan},
        )
    return Observation(
        kind=Kind.QUOTA.value,
        provider=PROVIDER,
        account_label="default",
        quality=Quality.EXACT_OFFICIAL.value if exact else Quality.UNKNOWN.value,
        source=SOURCE,
        observed_at=isoformat(now) or "",
        payload={
            "display_name": "Codex",
            "windows": windows,
            "plan_type": plan,
            "rate_limit_reached_type": reached,
            "ordinary_usage_allowed": ordinary,
        },
        source_class=SourceClass.OFFICIAL_UNSTABLE.value,
        failure_state=failure,
        last_error=None,
    )


def _classify_app_server_error(message: str) -> str:
    text = message.casefold()
    if any(token in text for token in ("auth", "login", "unauthorized", "401", "not logged")):
        return FailureState.AUTH_REQUIRED.value
    if "timed out" in text or "timeout" in text:
        return FailureState.NETWORK_ERROR.value
    return FailureState.PROVIDER_ERROR.value


def _rpc(method: str, rpc_id: int | None, params: dict[str, Any] | None = None) -> dict[str, Any]:
    message: dict[str, Any] = {"method": method}
    if rpc_id is not None:
        message["id"] = rpc_id
    if params is not None:
        message["params"] = params
    return message


def read_app_server_rate_limits(
    stdout_lines: list[str],
) -> dict[str, Any] | None:
    for line in stdout_lines:
        text = line.strip()
        if not text:
            continue
        try:
            item = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        if item.get("id") == 2 and "result" in item:
            result = item.get("result")
            return result if isinstance(result, dict) else None
        if item.get("id") == 2 and "error" in item:
            error = item.get("error")
            message = ""
            if isinstance(error, dict):
                message = str(error.get("message") or error)
            else:
                message = str(error)
            raise RuntimeError(message)
    return None


def collect_codex(
    *,
    now: datetime,
    which: Callable[[str], str | None] = shutil.which,
    run_app_server: Callable[[list[dict[str, Any]], float], tuple[int, str, str]] | None = None,
) -> Observation:
    binary = which("codex")
    if not binary:
        return Observation.unknown(
            kind=Kind.QUOTA.value,
            provider=PROVIDER,
            source=SOURCE,
            now=now,
            failure_state=FailureState.PROVIDER_ERROR.value,
            last_error="codex CLI is not on PATH",
            source_class=SourceClass.OFFICIAL_UNSTABLE.value,
            payload={"display_name": "Codex", "windows": []},
        )

    requests = [
        _rpc(
            "initialize",
            1,
            {
                "clientInfo": {"name": "flowfoundry", "version": "0.2.0"},
                "capabilities": {"optOutNotificationMethods": ["thread/started", "turn/started"]},
            },
        ),
        _rpc("initialized", None),
        _rpc("account/rateLimits/read", 2, {}),
    ]
    runner = run_app_server or _run_codex_app_server
    try:
        code, stdout, stderr = runner(requests, APP_SERVER_TIMEOUT)
    except FileNotFoundError:
        return Observation.unknown(
            kind=Kind.QUOTA.value,
            provider=PROVIDER,
            source=SOURCE,
            now=now,
            failure_state=FailureState.PROVIDER_ERROR.value,
            last_error="codex CLI is not on PATH",
            source_class=SourceClass.OFFICIAL_UNSTABLE.value,
            payload={"display_name": "Codex", "windows": []},
        )
    except subprocess.TimeoutExpired:
        return Observation.unknown(
            kind=Kind.QUOTA.value,
            provider=PROVIDER,
            source=SOURCE,
            now=now,
            failure_state=FailureState.NETWORK_ERROR.value,
            last_error="codex app-server timed out",
            source_class=SourceClass.OFFICIAL_UNSTABLE.value,
            payload={"display_name": "Codex", "windows": []},
        )
    except RuntimeError as exc:
        message = str(exc)
        return Observation.unknown(
            kind=Kind.QUOTA.value,
            provider=PROVIDER,
            source=SOURCE,
            now=now,
            failure_state=_classify_app_server_error(message),
            last_error=message[:300],
            source_class=SourceClass.OFFICIAL_UNSTABLE.value,
            payload={"display_name": "Codex", "windows": []},
        )
    try:
        result = read_app_server_rate_limits(stdout.splitlines())
    except RuntimeError as exc:
        message = str(exc)
        return Observation.unknown(
            kind=Kind.QUOTA.value,
            provider=PROVIDER,
            source=SOURCE,
            now=now,
            failure_state=_classify_app_server_error(message),
            last_error=message[:300],
            source_class=SourceClass.OFFICIAL_UNSTABLE.value,
            payload={"display_name": "Codex", "windows": []},
        )
    if result is None:
        detail = (stderr or stdout or f"exit {code}")[:300]
        return Observation.unknown(
            kind=Kind.QUOTA.value,
            provider=PROVIDER,
            source=SOURCE,
            now=now,
            failure_state=_classify_app_server_error(detail),
            last_error=detail or "no account/rateLimits/read result",
            source_class=SourceClass.OFFICIAL_UNSTABLE.value,
            payload={"display_name": "Codex", "windows": []},
        )
    return parse_rate_limits(result, now=now)


def _write_rpc(proc: subprocess.Popen[str], message: dict[str, Any]) -> None:
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
    proc.stdin.flush()


def _read_until_id(proc: subprocess.Popen[str], rpc_id: int, collected: list[str], deadline: float) -> None:
    assert proc.stdout is not None
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        ready, _, _ = select.select([proc.stdout], [], [], remaining)
        if not ready:
            return
        line = proc.stdout.readline()
        if line == "":
            return
        collected.append(line)
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and item.get("id") == rpc_id:
            return


def _run_codex_app_server(messages: list[dict[str, Any]], timeout: float) -> tuple[int, str, str]:
    binary = shutil.which("codex")
    if not binary:
        raise FileNotFoundError("codex")
    proc = subprocess.Popen(
        [binary, "app-server", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(Path.home()),
    )
    collected: list[str] = []
    stderr = ""
    try:
        deadline = time.monotonic() + timeout
        by_id = {item["id"]: item for item in messages if "id" in item}
        initialized = next((item for item in messages if item.get("method") == "initialized"), None)
        if 1 in by_id:
            _write_rpc(proc, by_id[1])
            _read_until_id(proc, 1, collected, deadline)
        if initialized is not None:
            _write_rpc(proc, initialized)
        if 2 in by_id:
            _write_rpc(proc, by_id[2])
            _read_until_id(proc, 2, collected, deadline)
        if proc.stdin:
            proc.stdin.close()
        try:
            _, stderr = proc.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            proc.kill()
            _, stderr = proc.communicate(timeout=1)
        return proc.returncode or 0, "".join(collected), stderr or ""
    except Exception:
        proc.kill()
        raise

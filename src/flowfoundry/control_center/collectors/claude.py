"""Claude Code collector: local statusline/rate_limits first, then JSONL usage."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

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

PROVIDER = "anthropic"
SOURCE_STATUSLINE = "claude.statusline.rate_limits"
SOURCE_JSONL = "claude.local.jsonl.usage"


def _claude_roots(home: Path) -> list[Path]:
    roots = [home / ".claude", home / ".config" / "claude"]
    return [path for path in roots if path.is_dir()]


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None


def extract_rate_limits(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    for key in ("rate_limits", "rateLimits"):
        raw = value.get(key)
        if isinstance(raw, dict) and raw:
            return raw
    nested = value.get("payload")
    if isinstance(nested, dict):
        return extract_rate_limits(nested)
    message = value.get("message")
    if isinstance(message, dict):
        return extract_rate_limits(message)
    return None


def _window_from_limit(name: str, raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {
            "id": name,
            "used_percent": None,
            "remaining_percent": None,
            "resets_at": None,
            "quality": Quality.UNKNOWN.value,
        }
    used = (
        raw.get("used_percentage")
        or raw.get("usedPercent")
        or raw.get("utilization")
        or raw.get("used_percent")
    )
    remaining = raw.get("remaining_percentage") or raw.get("remainingPercent")
    if remaining is None:
        remaining = remaining_from_used_percent(used)
    try:
        used_n = int(used) if used is not None else None
    except (TypeError, ValueError):
        used_n = None
    try:
        remaining_n = int(remaining) if remaining is not None else None
    except (TypeError, ValueError):
        remaining_n = None
    resets = (
        raw.get("resets_at")
        or raw.get("resetsAt")
        or raw.get("reset_at")
        or raw.get("resetAt")
    )
    return {
        "id": name,
        "used_percent": used_n,
        "remaining_percent": remaining_n,
        "resets_at": isoformat(parse_datetime(resets)),
        "quality": Quality.EXACT_OFFICIAL.value,
    }


def parse_statusline_rate_limits(raw: dict[str, Any], *, now: datetime) -> Observation | None:
    windows: list[dict[str, Any]] = []
    mapping = (
        ("five_hour", "5h"),
        ("fiveHour", "5h"),
        ("5h", "5h"),
        ("session", "5h"),
        ("seven_day", "weekly"),
        ("sevenDay", "weekly"),
        ("7d", "weekly"),
        ("weekly", "weekly"),
    )
    seen: set[str] = set()
    for key, label in mapping:
        if key in raw and label not in seen:
            windows.append(_window_from_limit(label, raw[key]))
            seen.add(label)
    if not windows:
        return None
    exact = any(item.get("remaining_percent") is not None for item in windows)
    failure = FailureState.AVAILABLE.value
    if any(item.get("remaining_percent") == 0 for item in windows if item.get("remaining_percent") is not None):
        failure = FailureState.QUOTA_EXHAUSTED.value
    return Observation(
        kind=Kind.QUOTA.value,
        provider=PROVIDER,
        account_label="default",
        quality=Quality.EXACT_OFFICIAL.value if exact else Quality.UNKNOWN.value,
        source=SOURCE_STATUSLINE,
        observed_at=isoformat(now) or "",
        payload={"display_name": "Claude Code", "windows": windows},
        source_class=SourceClass.AUTHORITATIVE.value,
        failure_state=failure,
    )


def parse_jsonl_usage(lines: Iterable[str]) -> dict[str, int]:
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "messages": 0,
    }
    for line in lines:
        text = line.strip()
        if not text:
            continue
        try:
            item = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        usage = item.get("usage")
        if not isinstance(usage, dict):
            message = item.get("message")
            if isinstance(message, dict):
                usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        totals["messages"] += 1
        totals["input_tokens"] += int(usage.get("input_tokens") or 0)
        totals["output_tokens"] += int(usage.get("output_tokens") or 0)
        totals["cache_read_tokens"] += int(usage.get("cache_read_input_tokens") or 0)
        cache_write = usage.get("cache_creation_input_tokens")
        if cache_write is None:
            creation = usage.get("cache_creation")
            if isinstance(creation, dict):
                cache_write = creation.get("ephemeral_5m_input_tokens") or 0
        totals["cache_write_tokens"] += int(cache_write or 0)
    return totals


def _iter_statusline_candidates(roots: list[Path]) -> list[Any]:
    found: list[Any] = []
    names = (
        "stats-cache.json",
        "rate_limits.json",
        "statusline.json",
        "usage-cache.json",
    )
    for root in roots:
        for name in names:
            payload = _load_json(root / name)
            if payload is not None:
                found.append(payload)
        for path in root.glob("*.json"):
            if path.name in {"settings.json", "history.jsonl"}:
                continue
            payload = _load_json(path)
            if extract_rate_limits(payload) is not None:
                found.append(payload)
    return found


def collect_claude(
    *,
    now: datetime,
    home: Path,
    which: Callable[[str], str | None] = shutil.which,
) -> Observation:
    binary = which("claude")
    roots = _claude_roots(home)
    for candidate in _iter_statusline_candidates(roots):
        limits = extract_rate_limits(candidate) or (
            candidate if isinstance(candidate, dict) and any(
                key in candidate for key in ("five_hour", "seven_day", "5h", "weekly")
            )
            else None
        )
        if not isinstance(limits, dict):
            continue
        parsed = parse_statusline_rate_limits(limits, now=now)
        if parsed is not None:
            if not binary:
                parsed.failure_state = FailureState.PROVIDER_ERROR.value
                parsed.last_error = "claude CLI is not on PATH"
            return parsed

    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "messages": 0,
    }
    jsonl_seen = False
    for root in roots:
        projects = root / "projects"
        if not projects.is_dir():
            continue
        for path in projects.rglob("*.jsonl"):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            jsonl_seen = True
            chunk = parse_jsonl_usage(text.splitlines())
            for key, value in chunk.items():
                totals[key] += value

    if not binary:
        return Observation.unknown(
            kind=Kind.QUOTA.value,
            provider=PROVIDER,
            source=SOURCE_JSONL,
            now=now,
            failure_state=FailureState.PROVIDER_ERROR.value,
            last_error="claude CLI is not on PATH",
            source_class=SourceClass.LOCAL.value,
            payload={"display_name": "Claude Code", "windows": []},
        )

    windows = [
        {
            "id": "5h",
            "used_percent": None,
            "remaining_percent": None,
            "resets_at": None,
            "quality": Quality.UNKNOWN.value,
        },
        {
            "id": "weekly",
            "used_percent": None,
            "remaining_percent": None,
            "resets_at": None,
            "quality": Quality.UNKNOWN.value,
        },
    ]
    quality = Quality.EXACT_LOCAL.value if jsonl_seen else Quality.UNKNOWN.value
    return Observation(
        kind=Kind.QUOTA.value,
        provider=PROVIDER,
        account_label="default",
        quality=quality,
        source=SOURCE_JSONL,
        observed_at=isoformat(now) or "",
        payload={
            "display_name": "Claude Code",
            "windows": windows,
            "local_tokens": totals if jsonl_seen else None,
            "remaining_quota": Quality.UNKNOWN.value,
            "note": "Local token totals are not remaining subscription quota.",
        },
        source_class=SourceClass.LOCAL.value,
        failure_state=FailureState.AVAILABLE.value,
        last_error=None if jsonl_seen else "no statusline rate_limits; remaining quota UNKNOWN",
    )

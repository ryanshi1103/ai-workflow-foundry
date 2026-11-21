"""Grok Build collector: official local usage.json and inspect, no unofficial billing."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from ..model import FailureState, Kind, Observation, Quality, SourceClass, isoformat

PROVIDER = "xai"
SOURCE_USAGE = "grok.local.usage.json"
SOURCE_INSPECT = "grok.inspect"


def parse_usage_file(payload: Any) -> dict[str, int]:
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_read_tokens": 0,
        "cache_creation_tokens": 0,
        "reasoning_tokens": 0,
        "total_tokens": 0,
        "model_calls": 0,
    }
    if not isinstance(payload, dict):
        return totals
    session = payload.get("session")
    if not isinstance(session, dict):
        session = payload
    mapping = {
        "input_tokens": ("inputTokens", "input_tokens"),
        "output_tokens": ("outputTokens", "output_tokens"),
        "cached_read_tokens": ("cachedReadTokens", "cached_read_tokens"),
        "cache_creation_tokens": ("cacheCreationTokens", "cache_creation_tokens"),
        "reasoning_tokens": ("reasoningTokens", "reasoning_tokens"),
        "total_tokens": ("totalTokens", "total_tokens"),
        "model_calls": ("modelCalls", "model_calls"),
    }
    for dest, keys in mapping.items():
        for key in keys:
            if key in session:
                try:
                    totals[dest] = int(session[key] or 0)
                except (TypeError, ValueError):
                    totals[dest] = 0
                break
    return totals


def collect_grok(
    *,
    now: datetime,
    home: Path,
    which: Callable[[str], str | None] = shutil.which,
    inspect: Callable[[], dict[str, Any]] | None = None,
) -> Observation:
    binary = which("grok")
    grok_home = home / ".grok"
    sessions = grok_home / "sessions"
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_read_tokens": 0,
        "cache_creation_tokens": 0,
        "reasoning_tokens": 0,
        "total_tokens": 0,
        "model_calls": 0,
        "sessions": 0,
    }
    latest_update = None
    if sessions.is_dir():
        for path in sessions.rglob("usage.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, UnicodeError):
                continue
            chunk = parse_usage_file(payload)
            totals["sessions"] += 1
            for key in (
                "input_tokens",
                "output_tokens",
                "cached_read_tokens",
                "cache_creation_tokens",
                "reasoning_tokens",
                "total_tokens",
                "model_calls",
            ):
                totals[key] += chunk[key]
            stamp = None
            if isinstance(payload, dict):
                stamp = payload.get("updatedAt")
            if stamp:
                latest_update = stamp

    inspect_ok = False
    inspect_error = None
    version = None
    if inspect is not None:
        try:
            info = inspect()
            inspect_ok = isinstance(info, dict)
            if inspect_ok:
                version = info.get("grokVersion") or info.get("version")
        except Exception as exc:  # pragma: no cover - exercised via injected inspect
            inspect_error = str(exc)[:300]
    elif binary:
        inspect_ok = True

    windows = [
        {
            "id": "weekly",
            "used_percent": None,
            "remaining_percent": None,
            "resets_at": None,
            "quality": Quality.UNKNOWN.value,
        }
    ]
    if not binary:
        return Observation.unknown(
            kind=Kind.QUOTA.value,
            provider=PROVIDER,
            source=SOURCE_USAGE,
            now=now,
            failure_state=FailureState.PROVIDER_ERROR.value,
            last_error="grok CLI is not on PATH",
            source_class=SourceClass.LOCAL.value,
            payload={"display_name": "Grok Build", "windows": windows},
        )

    quality = Quality.EXACT_LOCAL.value if totals["sessions"] else Quality.UNKNOWN.value
    failure = FailureState.AVAILABLE.value
    if inspect_error:
        failure = FailureState.PROVIDER_ERROR.value
    return Observation(
        kind=Kind.QUOTA.value,
        provider=PROVIDER,
        account_label="default",
        quality=quality,
        source=SOURCE_USAGE if totals["sessions"] else SOURCE_INSPECT,
        observed_at=str(latest_update or isoformat(now) or ""),
        payload={
            "display_name": "Grok Build",
            "windows": windows,
            "session_usage": totals if totals["sessions"] else None,
            "weekly_remaining": Quality.UNKNOWN.value,
            "cli_version": version,
            "inspect_ok": inspect_ok,
            "note": "Weekly remaining quota is UNKNOWN unless the CLI exposes it.",
        },
        source_class=SourceClass.LOCAL.value,
        failure_state=failure,
        last_error=inspect_error,
    )

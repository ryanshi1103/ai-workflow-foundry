"""Assemble a redacted Control Center snapshot."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from .analytics import analyze_history
from .collectors.claude import collect_claude
from .collectors.codex import collect_codex
from .collectors.grok import collect_grok
from .collectors.live_work import collect_live_work
from .collectors.radar import collect_radar

try:
    from .collectors.gemini import collect_gemini
except ImportError:  # Gemini collector ships with provider integration
    collect_gemini = None
from .model import FailureState, Kind, Observation, Quality, isoformat, relabel_stale, utcnow
from .redact import redact_value
from .history import HistoryStore, default_history_path

QUOTA_MAX_AGE = timedelta(minutes=15)


def _card(observation: Observation) -> dict[str, Any]:
    payload = observation.payload if isinstance(observation.payload, dict) else {}
    return {
        "provider": observation.provider,
        "display_name": payload.get("display_name") or observation.provider,
        "account_label": observation.account_label,
        "health": observation.failure_state,
        "quality": observation.quality,
        "source": observation.source,
        "source_class": observation.source_class,
        "observed_at": observation.observed_at,
        "last_error": observation.last_error,
        "windows": payload.get("windows") or [],
        "payload": payload,
        "kind": observation.kind,
    }


def collect_snapshot(
    *,
    root: Path,
    home: Path | None = None,
    now: datetime | None = None,
    collectors: dict[str, Callable[..., Any]] | None = None,
    history_path: Path | None = None,
    persist_history: bool | None = None,
) -> dict[str, Any]:
    moment = now or utcnow()
    home_dir = home or Path.home()
    hooks = collectors or {}

    def _safe(name: str, fn: Callable[[], Any], kind: str, provider: str, source: str) -> Any:
        try:
            return fn()
        except Exception as exc:  # collector failure must not block the page
            return Observation.unknown(
                kind=kind,
                provider=provider,
                source=source,
                now=moment,
                failure_state=FailureState.PROVIDER_ERROR.value,
                last_error=str(exc)[:300],
            )

    jobs = {
        "codex": (
            lambda: hooks.get("codex", collect_codex)(now=moment),
            Kind.QUOTA.value,
            "openai",
            "codex.app-server.account/rateLimits/read",
        ),
        "claude": (
            lambda: hooks.get("claude", collect_claude)(now=moment, home=home_dir),
            Kind.QUOTA.value,
            "anthropic",
            "claude.statusline.rate_limits",
        ),
        "grok": (
            lambda: hooks.get("grok", collect_grok)(now=moment, home=home_dir),
            Kind.QUOTA.value,
            "xai",
            "grok.local.usage.json",
        ),
        "gemini": (
            lambda: (hooks.get("gemini") or collect_gemini)(now=moment, home=home_dir)
            if (hooks.get("gemini") or collect_gemini)
            else Observation.unknown(
                kind=Kind.HEALTH.value,
                provider="google",
                source="gemini.cli.capability",
                now=moment,
                payload={"display_name": "Gemini CLI", "windows": []},
            ),
            Kind.HEALTH.value,
            "google",
            "gemini.cli.capability",
        ),
        "live_work": (
            lambda: hooks.get("live_work", collect_live_work)(now=moment, root=root),
            Kind.WORK.value,
            "flowfoundry",
            "flowfoundry.coordinator+result.json",
        ),
        "radar": (
            lambda: hooks.get("radar", collect_radar)(now=moment, home=home_dir),
            Kind.RADAR.value,
            "radar",
            "radar",
        ),
    }
    results: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            name: pool.submit(_safe, name, spec[0], spec[1], spec[2], spec[3])
            for name, spec in jobs.items()
        }
        for name, future in futures.items():
            results[name] = future.result()
    codex = results["codex"]
    claude = results["claude"]
    grok = results["grok"]
    gemini = results["gemini"]
    work = results["live_work"]
    radar = results["radar"]
    if not isinstance(radar, list):
        radar = [radar] if isinstance(radar, Observation) else []
    overview = [
        relabel_stale(codex, now=moment, max_age=QUOTA_MAX_AGE),
        relabel_stale(claude, now=moment, max_age=QUOTA_MAX_AGE),
        relabel_stale(grok, now=moment, max_age=QUOTA_MAX_AGE),
        relabel_stale(gemini, now=moment, max_age=QUOTA_MAX_AGE),
    ]
    cards = [_card(item) for item in overview]
    history_enabled = persist_history if persist_history is not None else now is None
    analytics = analyze_history([], now=moment)
    if history_enabled:
        try:
            store = HistoryStore(history_path or default_history_path(root))
            store.record_cards(cards, sampled_at=moment)
            records = store.read(since=moment - timedelta(days=180), limit=4_000)
            analytics = analyze_history(records, now=moment)
        except (OSError, ValueError, sqlite3.Error) as exc:
            analytics["history"]["status"] = "UNAVAILABLE"
            analytics["history"]["error"] = str(exc)[:200]
    else:
        analytics["history"]["status"] = "DISABLED_FOR_DETERMINISTIC_SNAPSHOT"
    snapshot = {
        "generated_at": isoformat(moment),
        "bind": "127.0.0.1",
        "overview": cards,
        "live_work": _card(work)["payload"] | {
            "quality": work.quality,
            "source": work.source,
            "observed_at": work.observed_at,
            "health": work.failure_state,
        },
        "radar": [
            {
                "provider": item.provider,
                "quality": item.quality,
                "source": item.source,
                "source_class": item.source_class,
                "observed_at": item.observed_at,
                "published_at": (item.payload or {}).get("published_at"),
                "version": (item.payload or {}).get("version"),
                "change_kind": (item.payload or {}).get("change_kind"),
                "title": (item.payload or {}).get("title"),
                "last_error": item.last_error,
            }
            for item in radar
        ],
        "analytics": analytics,
        "notes": [
            "Remaining quota is shown only when a provider actually reports it.",
            "UNKNOWN means the field was not observed; it is not zero.",
            "models.dev is a catalog cross-check, not release authority.",
        ],
    }
    return redact_value(snapshot)


def unknown_field(value: Any) -> bool:
    return value in (None, "", Quality.UNKNOWN.value, "UNKNOWN")

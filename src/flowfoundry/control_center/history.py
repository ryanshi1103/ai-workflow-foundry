"""Bounded local history for Control Center observations.

Only normalized operational measurements are stored.  Credentials, prompts,
transcripts, and model text never enter this database.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from .model import parse_datetime

SCHEMA_VERSION = 1
RETENTION_DAYS = 180
MAX_ROWS = 50_000


def default_history_path(root: Path) -> Path:
    return root.resolve() / ".flowfoundry" / "control-center" / "history.sqlite3"


class HistoryStore:
    """SQLite-backed observation history with deterministic bounded retention."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY,
                sampled_at TEXT NOT NULL,
                source_observed_at TEXT,
                provider TEXT NOT NULL,
                metric TEXT NOT NULL,
                window_id TEXT NOT NULL,
                value REAL,
                quality TEXT NOT NULL,
                source TEXT NOT NULL,
                reset_at TEXT,
                stale INTEGER NOT NULL CHECK (stale IN (0, 1)),
                collector_status TEXT NOT NULL,
                schema_version INTEGER NOT NULL,
                UNIQUE(sampled_at, provider, metric, window_id)
            );
            CREATE INDEX IF NOT EXISTS observations_series_time
                ON observations(provider, metric, window_id, sampled_at);
            CREATE INDEX IF NOT EXISTS observations_sampled_at
                ON observations(sampled_at);
            """
        )
        connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass
        return connection

    def record_cards(self, cards: Iterable[dict[str, Any]], *, sampled_at: datetime) -> int:
        moment = _utc(sampled_at)
        stamp = moment.isoformat()
        rows: list[tuple[Any, ...]] = []
        for card in cards:
            if not isinstance(card, dict):
                continue
            provider = str(card.get("provider") or "unknown")[:80]
            quality = str(card.get("quality") or "UNKNOWN")[:80]
            source = str(card.get("source") or "unknown")[:300]
            status = str(card.get("health") or "UNKNOWN")[:80]
            source_observed_at = _safe_timestamp(card.get("observed_at"))
            payload = card.get("payload") if isinstance(card.get("payload"), dict) else {}
            stale = bool(payload.get("stale"))
            windows = card.get("windows") if isinstance(card.get("windows"), list) else []
            if not windows:
                windows = [{"id": "provider", "remaining_percent": None, "resets_at": None}]
            for window in windows:
                if not isinstance(window, dict):
                    continue
                value = _safe_percentage(window.get("remaining_percent"))
                window_quality = str(window.get("quality") or quality)[:80]
                rows.append(
                    (
                        stamp,
                        source_observed_at,
                        provider,
                        "remaining_percent",
                        str(window.get("id") or "unknown")[:80],
                        value,
                        window_quality,
                        source,
                        _safe_timestamp(window.get("resets_at")),
                        1 if stale else 0,
                        status,
                        SCHEMA_VERSION,
                    )
                )
        if not rows:
            return 0
        with closing(self._connect()) as connection:
            with connection:
                before = connection.total_changes
                connection.executemany(
                    """
                    INSERT OR IGNORE INTO observations (
                        sampled_at, source_observed_at, provider, metric, window_id,
                        value, quality, source, reset_at, stale, collector_status,
                        schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                cutoff = (moment - timedelta(days=RETENTION_DAYS)).isoformat()
                connection.execute("DELETE FROM observations WHERE sampled_at < ?", (cutoff,))
                connection.execute(
                    """
                    DELETE FROM observations
                    WHERE id IN (
                        SELECT id FROM observations
                        ORDER BY sampled_at DESC, id DESC
                        LIMIT -1 OFFSET ?
                    )
                    """,
                    (MAX_ROWS,),
                )
                return connection.total_changes - before

    def read(self, *, since: datetime | None = None, limit: int = 4_000) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), MAX_ROWS))
        query = """
            SELECT sampled_at, source_observed_at, provider, metric, window_id,
                   value, quality, source, reset_at, stale, collector_status,
                   schema_version
            FROM observations
        """
        params: list[Any] = []
        if since is not None:
            query += " WHERE sampled_at >= ?"
            params.append(_utc(since).isoformat())
        query += " ORDER BY sampled_at DESC, id DESC LIMIT ?"
        params.append(bounded_limit)
        with closing(self._connect()) as connection:
            rows = [dict(row) for row in connection.execute(query, params)]
        rows.reverse()
        for row in rows:
            row["stale"] = bool(row.get("stale"))
        return rows

    def count(self) -> int:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM observations").fetchone()
        return int(row["count"] if row else 0)


def _safe_percentage(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not 0 <= number <= 100:
        return None
    return number


def _safe_timestamp(value: Any) -> str | None:
    parsed = parse_datetime(value)
    return parsed.isoformat() if parsed is not None else None


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

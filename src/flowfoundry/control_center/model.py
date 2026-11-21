"""Normalized Control Center observations.

Quality describes numeric accuracy. SourceClass describes whether the
interface itself is a stable public contract. They are stored separately
so an exact number from an unstable CLI RPC is not labeled as a public API.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any


class Quality(StrEnum):
    EXACT_OFFICIAL = "EXACT_OFFICIAL"
    EXACT_LOCAL = "EXACT_LOCAL"
    OFFICIAL_UNSTABLE = "OFFICIAL_UNSTABLE"
    OBSERVED_INTERNAL = "OBSERVED_INTERNAL"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"


class SourceClass(StrEnum):
    AUTHORITATIVE = "AUTHORITATIVE"
    OFFICIAL_UNSTABLE = "OFFICIAL_UNSTABLE"
    LOCAL = "LOCAL"
    COMMUNITY_CURATED = "COMMUNITY_CURATED"
    INFERRED = "INFERRED"


class FailureState(StrEnum):
    AVAILABLE = "AVAILABLE"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    UNSUPPORTED_ACCOUNT_TIER = "UNSUPPORTED_ACCOUNT_TIER"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    RATE_LIMITED = "RATE_LIMITED"
    NETWORK_ERROR = "NETWORK_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    UNKNOWN = "UNKNOWN"


class Kind(StrEnum):
    QUOTA = "quota"
    HEALTH = "health"
    WORK = "work"
    RADAR = "radar"
    CATALOG = "catalog"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def parse_datetime(value: object) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        # Codex resetsAt is unix seconds.
        if value > 1_000_000_000_000:
            value = value / 1000.0
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass
class Observation:
    kind: str
    provider: str
    account_label: str
    quality: str
    source: str
    observed_at: str
    payload: dict[str, Any] = field(default_factory=dict)
    source_class: str = SourceClass.LOCAL.value
    failure_state: str = FailureState.UNKNOWN.value
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def unknown(
        cls,
        *,
        kind: str,
        provider: str,
        source: str,
        now: datetime,
        account_label: str = "default",
        failure_state: str = FailureState.UNKNOWN.value,
        last_error: str | None = None,
        source_class: str = SourceClass.LOCAL.value,
        payload: dict[str, Any] | None = None,
    ) -> "Observation":
        return cls(
            kind=kind,
            provider=provider,
            account_label=account_label,
            quality=Quality.UNKNOWN.value,
            source=source,
            observed_at=isoformat(now) or "",
            payload=payload or {},
            source_class=source_class,
            failure_state=failure_state,
            last_error=last_error,
        )


def remaining_from_used_percent(used_percent: object) -> int | None:
    try:
        used = int(used_percent)
    except (TypeError, ValueError):
        return None
    if used < 0 or used > 100:
        return None
    return 100 - used


def relabel_stale(
    observation: Observation,
    *,
    now: datetime,
    max_age: timedelta,
) -> Observation:
    """Keep numbers, but mark stale official captures as observed/internal."""
    observed = parse_datetime(observation.observed_at)
    payload = dict(observation.payload)
    if observed is None:
        payload["stale"] = True
        payload["freshness"] = Quality.UNKNOWN.value
        observation.payload = payload
        if observation.quality in {
            Quality.EXACT_OFFICIAL.value,
            Quality.OFFICIAL_UNSTABLE.value,
        }:
            payload["original_quality"] = observation.quality
            observation.quality = Quality.OBSERVED_INTERNAL.value
        return observation
    age = now - observed
    if age <= max_age:
        payload["stale"] = False
        payload["freshness"] = "FRESH"
        observation.payload = payload
        return observation
    payload["stale"] = True
    payload["freshness"] = "STALE"
    payload["stale_age_seconds"] = int(age.total_seconds())
    if observation.quality in {
        Quality.EXACT_OFFICIAL.value,
        Quality.OFFICIAL_UNSTABLE.value,
    }:
        payload["original_quality"] = observation.quality
        observation.quality = Quality.OBSERVED_INTERNAL.value
    observation.payload = payload
    return observation

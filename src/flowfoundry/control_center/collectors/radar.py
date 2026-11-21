"""Minimal Model Radar: official Atom/changelog plus models.dev catalog hash."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import Request, urlopen

from ..model import (
    FailureState,
    Kind,
    Observation,
    Quality,
    SourceClass,
    isoformat,
    parse_datetime,
)

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
CODEX_ATOM = "https://github.com/openai/codex/releases.atom"
CLAUDE_FEED = "https://raw.githubusercontent.com/anthropics/claude-code/main/feed.xml"
MODELS_DEV = "https://models.dev/catalog.json"
USER_AGENT = "FlowFoundry-ControlCenter/0.2"


def parse_atom(xml_text: str, *, source: str, provider: str, now: datetime) -> list[Observation]:
    items: list[Observation] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return [
            Observation.unknown(
                kind=Kind.RADAR.value,
                provider=provider,
                source=source,
                now=now,
                failure_state=FailureState.PROVIDER_ERROR.value,
                last_error="malformed Atom/XML feed",
                source_class=SourceClass.AUTHORITATIVE.value,
            )
        ]
    entries = root.findall("atom:entry", ATOM_NS) or root.findall("entry")
    for entry in entries[:8]:
        title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or entry.findtext("title") or "").strip()
        updated = (
            entry.findtext("atom:updated", default="", namespaces=ATOM_NS)
            or entry.findtext("updated")
            or entry.findtext("atom:published", default="", namespaces=ATOM_NS)
            or ""
        )
        ident = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or entry.findtext("id") or title)
        link = ""
        link_el = entry.find("atom:link", ATOM_NS)
        if link_el is None:
            link_el = entry.find("link")
        if link_el is not None:
            link = link_el.get("href") or ""
        published = isoformat(parse_datetime(updated))
        kind = "release"
        lowered = title.casefold()
        if "deprecat" in lowered:
            kind = "deprecation"
        items.append(
            Observation(
                kind=Kind.RADAR.value,
                provider=provider,
                account_label="catalog",
                quality=Quality.EXACT_OFFICIAL.value,
                source=source,
                observed_at=isoformat(now) or "",
                payload={
                    "title": title or ident,
                    "published_at": published,
                    "version": ident,
                    "change_kind": kind,
                    "url": link,
                },
                source_class=SourceClass.AUTHORITATIVE.value,
                failure_state=FailureState.AVAILABLE.value,
            )
        )
    return items


def parse_grok_changelog(payload: Any, *, now: datetime, version: str | None) -> list[Observation]:
    items: list[Observation] = []
    if not isinstance(payload, list):
        return [
            Observation.unknown(
                kind=Kind.RADAR.value,
                provider="xai",
                source="grok.CHANGELOG.json",
                now=now,
                failure_state=FailureState.PROVIDER_ERROR.value,
                last_error="malformed Grok changelog",
                source_class=SourceClass.AUTHORITATIVE.value,
            )
        ]
    for entry in payload[:8]:
        if not isinstance(entry, dict):
            continue
        category = str(entry.get("category") or "update")
        description = str(entry.get("description") or "").strip()
        breaking = bool(entry.get("breaking_change"))
        change_kind = "breaking" if breaking else category
        items.append(
            Observation(
                kind=Kind.RADAR.value,
                provider="xai",
                account_label="catalog",
                quality=Quality.EXACT_LOCAL.value,
                source="grok.CHANGELOG.json",
                observed_at=isoformat(now) or "",
                payload={
                    "title": description[:240] or category,
                    "published_at": None,
                    "version": version,
                    "change_kind": change_kind,
                    "url": "https://x.ai/build/changelog",
                },
                source_class=SourceClass.AUTHORITATIVE.value,
                failure_state=FailureState.AVAILABLE.value,
            )
        )
    return items


def parse_models_dev_headers(
    headers: dict[str, str],
    *,
    now: datetime,
    body: bytes | None = None,
) -> Observation:
    normalized = {str(key).lower(): str(value) for key, value in headers.items()}
    digest = None
    if body:
        digest = hashlib.sha256(body).hexdigest()
    return Observation(
        kind=Kind.CATALOG.value,
        provider="models.dev",
        account_label="catalog",
        quality=Quality.EXACT_OFFICIAL.value,
        source="models.dev/catalog.json",
        observed_at=isoformat(now) or "",
        payload={
            "title": "models.dev catalog",
            "etag": normalized.get("etag"),
            "last_modified": normalized.get("last-modified"),
            "content_length": normalized.get("content-length"),
            "sha256": digest,
            "change_kind": "catalog",
            "note": "Community catalog cross-check; official changelogs remain release authority.",
        },
        source_class=SourceClass.COMMUNITY_CURATED.value,
        failure_state=FailureState.AVAILABLE.value,
    )


def _fetch(url: str, timeout: float = 4.0, method: str = "GET") -> tuple[int, dict[str, str], bytes]:
    request = Request(url, method=method, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read() if method != "HEAD" else b""
        headers = {key: value for key, value in response.headers.items()}
        return int(getattr(response, "status", 200) or 200), headers, body


def collect_radar(
    *,
    now: datetime,
    home: Path,
    fetch: Callable[[str, float, str], tuple[int, dict[str, str], bytes]] | None = None,
) -> list[Observation]:
    getter = fetch or _fetch

    def feed(url: str, provider: str) -> list[Observation]:
        try:
            status, _headers, body = getter(url, 4.0, "GET")
            if status >= 400:
                raise URLError(f"HTTP {status}")
            return parse_atom(body.decode("utf-8", errors="replace"), source=url, provider=provider, now=now)
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            return [
                Observation.unknown(
                    kind=Kind.RADAR.value,
                    provider=provider,
                    source=url,
                    now=now,
                    failure_state=FailureState.NETWORK_ERROR.value,
                    last_error=str(exc)[:300],
                    source_class=SourceClass.AUTHORITATIVE.value,
                )
            ]

    def models_dev() -> Observation:
        try:
            status, headers, _body = getter(MODELS_DEV, 4.0, "HEAD")
            if status >= 400:
                raise URLError(f"HTTP {status}")
            return parse_models_dev_headers(headers, now=now)
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            return Observation.unknown(
                kind=Kind.CATALOG.value,
                provider="models.dev",
                source=MODELS_DEV,
                now=now,
                failure_state=FailureState.NETWORK_ERROR.value,
                last_error=str(exc)[:300],
                source_class=SourceClass.COMMUNITY_CURATED.value,
            )

    with ThreadPoolExecutor(max_workers=3) as pool:
        codex_f = pool.submit(feed, CODEX_ATOM, "openai")
        claude_f = pool.submit(feed, CLAUDE_FEED, "anthropic")
        catalog_f = pool.submit(models_dev)
        items: list[Observation] = []
        items.extend(codex_f.result())
        items.extend(claude_f.result())
        grok_items = _local_grok_changelog(home, now)
        items.extend(grok_items)
        items.append(catalog_f.result())
    return items


def _local_grok_changelog(home: Path, now: datetime) -> list[Observation]:
    changelog = home / ".grok" / "CHANGELOG.json"
    version = None
    version_path = home / ".grok" / "version.json"
    if version_path.is_file():
        try:
            version_payload = json.loads(version_path.read_text(encoding="utf-8"))
            if isinstance(version_payload, dict):
                version = version_payload.get("version")
        except (OSError, json.JSONDecodeError, UnicodeError):
            version = None
    if changelog.is_file():
        try:
            payload = json.loads(changelog.read_text(encoding="utf-8"))
            return parse_grok_changelog(payload, now=now, version=str(version) if version else None)
        except (OSError, json.JSONDecodeError, UnicodeError) as exc:
            return [
                Observation.unknown(
                    kind=Kind.RADAR.value,
                    provider="xai",
                    source="grok.CHANGELOG.json",
                    now=now,
                    failure_state=FailureState.PROVIDER_ERROR.value,
                    last_error=str(exc)[:300],
                    source_class=SourceClass.AUTHORITATIVE.value,
                )
            ]
    return [
        Observation.unknown(
            kind=Kind.RADAR.value,
            provider="xai",
            source="grok.CHANGELOG.json",
            now=now,
            failure_state=FailureState.UNKNOWN.value,
            last_error="Grok changelog file is not present",
            source_class=SourceClass.AUTHORITATIVE.value,
        )
    ]

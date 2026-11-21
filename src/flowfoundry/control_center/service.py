"""Loopback HTTP status service. stdlib only."""

from __future__ import annotations

import json
import socket
import threading
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from ipaddress import ip_address
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any
from urllib.parse import urlparse

from .redact import redact_value
from .snapshot import collect_snapshot
from .model import isoformat, utcnow

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4730
CACHE_TTL = timedelta(minutes=5)


class LoopbackError(ValueError):
    """Raised when the service would listen beyond loopback."""


def assert_loopback(host: str) -> None:
    try:
        parsed = ip_address(host)
    except ValueError as exc:
        raise LoopbackError(f"bind host must be a loopback IP: {host}") from exc
    if not parsed.is_loopback:
        raise LoopbackError(f"refusing to bind non-loopback address {host}")


class _Cache:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.snapshot: dict[str, Any] | None = None
        self.collected_at: datetime | None = None
        self.collecting = False


def pending_snapshot(now: datetime | None = None) -> dict[str, Any]:
    moment = isoformat(now or utcnow())
    return {
        "generated_at": moment,
        "bind": "127.0.0.1",
        "overview": [],
        "live_work": {
            "responsible_worker": None,
            "specialist": None,
            "run_state": "IDLE",
            "operation": None,
            "tokens": None,
            "latency_seconds": None,
            "evidence_path": None,
            "events": [],
        },
        "radar": [],
        "analytics": {
            "metric": "remaining_percent",
            "series": [],
            "history": {"status": "COLLECTING", "observation_rows": 0},
        },
        "collecting": True,
        "notes": ["Collecting provider status."],
    }


def _html() -> bytes:
    path = resources.files("flowfoundry.control_center") / "static" / "index.html"
    return path.read_bytes()


def _kick_refresh(root: Path, home: Path, cache: _Cache, force: bool = False) -> None:
    with cache.lock:
        now = utcnow()
        fresh = (
            cache.snapshot is not None
            and cache.collected_at is not None
            and now - cache.collected_at < CACHE_TTL
        )
        if cache.collecting:
            return
        if fresh and not force:
            return
        cache.collecting = True

    def run() -> None:
        try:
            snapshot = collect_snapshot(root=root, home=home)
            with cache.lock:
                cache.snapshot = snapshot
                cache.collected_at = utcnow()
        finally:
            with cache.lock:
                cache.collecting = False

    threading.Thread(target=run, daemon=True, name="control-center-refresh").start()


def make_handler(root: Path, home: Path, cache: _Cache):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            # The page polls locally. Routine access logs would bury the one
            # useful startup URL and provide no operational value here.
            return

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(body)

        def _snapshot(self, force: bool = False) -> dict[str, Any]:
            with cache.lock:
                empty = cache.snapshot is None
            if empty or force:
                _kick_refresh(root, home, cache, force=force)
            with cache.lock:
                snapshot = cache.snapshot
                collecting = cache.collecting
            if snapshot is None:
                payload = pending_snapshot()
            else:
                payload = dict(snapshot)
                payload["collecting"] = collecting
            return payload

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send(200, _html(), "text/html; charset=utf-8")
                return
            if parsed.path == "/health":
                body = json.dumps({"ok": True, "bind": DEFAULT_HOST}).encode("utf-8")
                self._send(200, body, "application/json")
                return
            if parsed.path == "/api/status":
                force = "refresh=1" in (parsed.query or "")
                payload = redact_value(self._snapshot(force=force))
                body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                self._send(200, body, "application/json")
                return
            self._send(404, b"not found\n", "text/plain; charset=utf-8")

        def do_POST(self) -> None:  # noqa: N802
            self._send(405, b"method not allowed\n", "text/plain; charset=utf-8")

    return Handler


class ControlCenterServer(ThreadingHTTPServer, ThreadingMixIn):
    daemon_threads = True
    allow_reuse_address = True


def serve_control_center(
    *,
    root: Path,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    home: Path | None = None,
) -> ControlCenterServer:
    assert_loopback(host)
    cache = _Cache()
    home_dir = home or Path.home()
    try:
        server = ControlCenterServer((host, port), make_handler(root, home_dir, cache))
    except socket.gaierror as exc:
        raise OSError(f"cannot bind Control Center to {host}:{port}: {exc}") from exc
    bound_host, bound_port = server.server_address[:2]
    assert_loopback(str(bound_host))
    # Bind first. An occupied port must fail without leaving a collector thread.
    _kick_refresh(root, home_dir, cache, force=True)
    return server

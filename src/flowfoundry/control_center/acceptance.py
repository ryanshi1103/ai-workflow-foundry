"""Bounded subprocess acceptance for the long-running Control Center service."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from http.client import HTTPConnection
from pathlib import Path
from typing import Any

from .service import assert_loopback
from .redact import contains_secret


class ControlCenterAcceptanceError(RuntimeError):
    """Raised when the controlled service cannot complete acceptance."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _request(host: str, port: int, path: str, timeout: float) -> tuple[int, bytes]:
    connection = HTTPConnection(host, port, timeout=timeout)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def _failure_output(process: subprocess.Popen[str]) -> str:
    stdout, stderr = process.communicate(timeout=1)
    detail = (stderr or stdout or "no child output").strip()
    return detail[-1200:]


def _wait_for_health(
    process: subprocess.Popen[str], host: str, port: int, deadline: float
) -> tuple[int, dict[str, Any]]:
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise ControlCenterAcceptanceError(
                f"Control Center exited before ready: {_failure_output(process)}"
            )
        try:
            status, body = _request(host, port, "/health", timeout=0.5)
            payload = json.loads(body)
            if status == 200 and payload.get("ok") is True:
                return status, payload
        except (OSError, TimeoutError, ValueError, json.JSONDecodeError):
            pass
        time.sleep(0.05)
    raise ControlCenterAcceptanceError("timed out waiting for /health")


def _wait_for_status(
    process: subprocess.Popen[str], host: str, port: int, deadline: float
) -> tuple[int, dict[str, Any]]:
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise ControlCenterAcceptanceError(
                f"Control Center exited while collecting: {_failure_output(process)}"
            )
        try:
            status, body = _request(host, port, "/api/status", timeout=1.0)
            payload = json.loads(body)
            providers = {
                item.get("provider")
                for item in payload.get("overview", [])
                if isinstance(item, dict)
            }
            if (
                status == 200
                and not payload.get("collecting")
                and {"openai", "anthropic", "xai", "google"} <= providers
            ):
                return status, payload
        except (OSError, TimeoutError, ValueError, json.JSONDecodeError):
            pass
        time.sleep(0.1)
    raise ControlCenterAcceptanceError("timed out waiting for a complete /api/status")


def _assert_single_page(body: bytes) -> None:
    page = body.decode("utf-8")
    required = (
        "模型容量",
        "容量分析",
        "当前任务",
        "最新动态",
        "帮助与数据口径",
        "Noto Sans CJK SC",
        "chartSvg",
    )
    missing = [label for label in required if label not in page]
    banned = ('href="/overview"', 'href="/providers"', 'href="/live"', 'href="/radar"')
    found_banned = [route for route in banned if route in page]
    if missing or found_banned:
        raise ControlCenterAcceptanceError(
            f"single-page contract failed; missing={missing}, banned={found_banned}"
        )


def _pid_gone(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def _process_group_gone(group_id: int) -> bool:
    try:
        os.killpg(group_id, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def _port_closed(host: str, port: int) -> bool:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.settimeout(0.2)
    try:
        return probe.connect_ex((host, port)) != 0
    finally:
        probe.close()


def _stop_child(
    process: subprocess.Popen[str], host: str, port: int, *, was_ready: bool
) -> dict[str, Any]:
    terminated = False
    killed = False
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        terminated = True
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            killed = True
            process.wait(timeout=2)
    group_deadline = time.monotonic() + 1.0
    while not _process_group_gone(process.pid) and time.monotonic() < group_deadline:
        time.sleep(0.02)
    if not _process_group_gone(process.pid):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        killed = True
        group_deadline = time.monotonic() + 1.0
        while not _process_group_gone(process.pid) and time.monotonic() < group_deadline:
            time.sleep(0.02)
    stdout, stderr = process.communicate(timeout=1)
    cleanup = {
        "terminated": terminated,
        "killed": killed,
        "exit_code": process.returncode,
        "pid_gone": _pid_gone(process.pid),
        "process_group_gone": _process_group_gone(process.pid),
        "port_released": _port_closed(host, port) if was_ready else None,
        "stdout": stdout.strip()[-1200:],
        "stderr": stderr.strip()[-1200:],
    }
    if (
        not cleanup["pid_gone"]
        or not cleanup["process_group_gone"]
        or (was_ready and not cleanup["port_released"])
    ):
        raise ControlCenterAcceptanceError(f"child cleanup failed: {cleanup}")
    return cleanup


def _cycle(
    *, root: Path, host: str, port: int, timeout_seconds: float, cycle: int
) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "flowfoundry",
        "control-center",
        "--workspace",
        str(root),
        "--host",
        host,
        "--port",
        str(port),
    ]
    started_at = _timestamp()
    started = time.monotonic()
    environment = os.environ.copy()
    source_root = str(Path(__file__).resolve().parents[2])
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_root + os.pathsep + existing_pythonpath
        if existing_pythonpath
        else source_root
    )
    process = subprocess.Popen(
        command,
        cwd=root,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        close_fds=True,
    )
    record: dict[str, Any] = {
        "cycle": cycle,
        "pid": process.pid,
        "port": port,
        "started_at": started_at,
        "command": command,
    }
    was_ready = False
    failure: BaseException | None = None
    try:
        deadline = started + timeout_seconds
        health_status, health = _wait_for_health(process, host, port, deadline)
        was_ready = True
        root_status, page = _request(host, port, "/", timeout=1.0)
        if root_status != 200:
            raise ControlCenterAcceptanceError(f"GET / returned {root_status}")
        _assert_single_page(page)
        api_status, payload = _wait_for_status(process, host, port, deadline)
        if not isinstance(payload.get("live_work"), dict):
            raise ControlCenterAcceptanceError("/api/status has no Live Work object")
        if not isinstance(payload.get("radar"), list) or not payload["radar"]:
            raise ControlCenterAcceptanceError("/api/status has no Radar records")
        analytics = payload.get("analytics")
        if not isinstance(analytics, dict) or not isinstance(analytics.get("series"), list):
            raise ControlCenterAcceptanceError("/api/status has no analytics series")
        history = analytics.get("history")
        if not isinstance(history, dict) or history.get("storage") != "local SQLite":
            raise ControlCenterAcceptanceError("/api/status has no local history provenance")
        if contains_secret(payload):
            raise ControlCenterAcceptanceError("/api/status contains a credential marker")
        record.update(
            {
                "ready_at": _timestamp(),
                "health": {"status": health_status, "body": health},
                "responses": {
                    "/": root_status,
                    "/api/status": api_status,
                    "provider_cards": len(payload.get("overview", [])),
                    "live_work": isinstance(payload.get("live_work"), dict),
                    "radar_records": len(payload.get("radar", [])),
                    "analytics_series": len(analytics["series"]),
                    "history_rows": history.get("observation_rows", 0),
                },
            }
        )
    except BaseException as exc:
        failure = exc
    finally:
        cleanup = _stop_child(process, host, port, was_ready=was_ready)
        record["cleanup"] = cleanup
        record["elapsed_seconds"] = round(time.monotonic() - started, 3)
    if failure is not None:
        raise failure
    return record


def run_control_center_acceptance(
    *, root: Path, host: str, port: int, timeout_seconds: float = 20.0
) -> dict[str, Any]:
    """Start, probe, terminate, restart, and re-probe the real CLI service."""

    assert_loopback(host)
    if not 1 <= port <= 65535:
        raise ValueError("control-center acceptance requires a fixed port from 1 to 65535")
    if timeout_seconds <= 0:
        raise ValueError("control-center acceptance timeout must be positive")
    cycles = [
        _cycle(
            root=root,
            host=host,
            port=port,
            timeout_seconds=timeout_seconds,
            cycle=index,
        )
        for index in (1, 2)
    ]
    return {
        "result": "PASS",
        "url": f"http://{host}:{port}",
        "restart_verified": True,
        "orphan_process": False,
        "cycles": cycles,
    }

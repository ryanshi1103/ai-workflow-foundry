from __future__ import annotations

import io
import json
import os
import socket
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch

from flowfoundry.cli import build_parser, main
from flowfoundry.coordinator import CoordinatorTask, save_task
from flowfoundry.control_center.acceptance import (
    ControlCenterAcceptanceError,
    run_control_center_acceptance,
)
from flowfoundry.control_center.collectors.claude import (
    parse_jsonl_usage,
    parse_statusline_rate_limits,
    collect_claude,
)
from flowfoundry.control_center.collectors.codex import (
    parse_rate_limits,
    read_app_server_rate_limits,
    collect_codex,
)
from flowfoundry.control_center.collectors.grok import collect_grok, parse_usage_file
from flowfoundry.control_center.collectors.live_work import collect_live_work
from flowfoundry.control_center.collectors.radar import parse_atom, parse_grok_changelog, parse_models_dev_headers
from flowfoundry.control_center.model import FailureState, Quality, relabel_stale, Observation
from flowfoundry.control_center.redact import contains_secret, redact_value
from flowfoundry.control_center.service import LoopbackError, assert_loopback, serve_control_center
from flowfoundry.control_center.snapshot import collect_snapshot
from flowfoundry.goal_runner import environment_status


NOW = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)

CODEX_PAYLOAD = {
    "rateLimits": {
        "planType": "plus",
        "primary": {"usedPercent": 28, "resetsAt": 1759226400, "windowDurationMins": 300},
        "secondary": {"usedPercent": 41, "resetsAt": 1759744800, "windowDurationMins": 10080},
        "rateLimitReachedType": None,
    },
    "ordinaryUsageAllowed": True,
}

ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>v0.159.2</title>
    <id>https://github.com/openai/codex/releases/tag/rust-v0.159.2</id>
    <updated>2026-09-29T19:27:09Z</updated>
    <link href="https://github.com/openai/codex/releases/tag/rust-v0.159.2"/>
  </entry>
</feed>
"""


class ControlCenterTests(unittest.TestCase):
    def test_codex_exact_quota_parsing(self) -> None:
        obs = parse_rate_limits(CODEX_PAYLOAD, now=NOW)
        self.assertEqual(obs.quality, Quality.EXACT_OFFICIAL.value)
        self.assertEqual(obs.failure_state, FailureState.AVAILABLE.value)
        windows = {item["id"]: item for item in obs.payload["windows"]}
        self.assertEqual(windows["5h"]["remaining_percent"], 72)
        self.assertEqual(windows["weekly"]["remaining_percent"], 59)
        self.assertIsNotNone(windows["5h"]["resets_at"])

    def test_codex_unavailable(self) -> None:
        obs = collect_codex(now=NOW, which=lambda _: None)
        self.assertEqual(obs.quality, Quality.UNKNOWN.value)
        self.assertEqual(obs.failure_state, FailureState.PROVIDER_ERROR.value)
        self.assertEqual(obs.payload.get("windows"), [])

    def test_codex_malformed_and_auth(self) -> None:
        malformed = parse_rate_limits(["nope"], now=NOW)
        self.assertEqual(malformed.quality, Quality.UNKNOWN.value)
        with self.assertRaises(RuntimeError):
            read_app_server_rate_limits(['{"id":2,"error":{"message":"login required"}}'])
        obs = collect_codex(
            now=NOW,
            which=lambda _: "/usr/bin/codex",
            run_app_server=lambda *_: (1, '{"id":2,"error":{"message":"unauthorized"}}\n', ""),
        )
        self.assertEqual(obs.failure_state, FailureState.AUTH_REQUIRED.value)
        self.assertEqual(obs.quality, Quality.UNKNOWN.value)

    def test_claude_statusline_and_jsonl_fallback(self) -> None:
        limits = parse_statusline_rate_limits(
            {
                "five_hour": {"used_percentage": 12, "resets_at": "2026-09-30T16:00:00Z"},
                "seven_day": {"used_percentage": 40, "resets_at": "2026-10-04T12:00:00Z"},
            },
            now=NOW,
        )
        self.assertIsNotNone(limits)
        self.assertEqual(limits.quality, Quality.EXACT_OFFICIAL.value)
        self.assertEqual(limits.payload["windows"][0]["remaining_percent"], 88)
        usage = parse_jsonl_usage(
            [
                json.dumps({"type": "assistant", "message": {"usage": {"input_tokens": 10, "output_tokens": 4}}}),
                "not-json",
                json.dumps({"usage": {"input_tokens": 5, "output_tokens": 1, "cache_read_input_tokens": 2}}),
            ]
        )
        self.assertEqual(usage["input_tokens"], 15)
        self.assertEqual(usage["output_tokens"], 5)

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            project = home / ".claude" / "projects" / "demo"
            project.mkdir(parents=True)
            (project / "session.jsonl").write_text(
                json.dumps({"message": {"usage": {"input_tokens": 9, "output_tokens": 3}}}) + "\n",
                encoding="utf-8",
            )
            obs = collect_claude(now=NOW, home=home, which=lambda _: "/usr/bin/claude")
            self.assertEqual(obs.quality, Quality.EXACT_LOCAL.value)
            self.assertEqual(obs.source, "claude.local.jsonl.usage")
            self.assertIsNone(obs.payload["windows"][0]["remaining_percent"])
            self.assertEqual(obs.payload["remaining_quota"], Quality.UNKNOWN.value)
            self.assertEqual(obs.payload["local_tokens"]["input_tokens"], 9)

    def test_claude_fallback_quality_downgrade_without_rate_limits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            obs = collect_claude(now=NOW, home=Path(directory), which=lambda _: "/bin/claude")
            self.assertEqual(obs.quality, Quality.UNKNOWN.value)
            self.assertEqual(obs.payload["windows"][0]["remaining_percent"], None)

    def test_grok_usage_and_unknown_weekly(self) -> None:
        parsed = parse_usage_file({"session": {"inputTokens": 11, "outputTokens": 7, "totalTokens": 18}})
        self.assertEqual(parsed["input_tokens"], 11)
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            session = home / ".grok" / "sessions" / "demo"
            session.mkdir(parents=True)
            (session / "usage.json").write_text(
                json.dumps({"updatedAt": "2026-09-30T11:00:00Z", "session": {"inputTokens": 3, "outputTokens": 2, "totalTokens": 5}}),
                encoding="utf-8",
            )
            obs = collect_grok(now=NOW, home=home, which=lambda _: "/usr/bin/grok")
            self.assertEqual(obs.quality, Quality.EXACT_LOCAL.value)
            self.assertEqual(obs.payload["windows"][0]["id"], "weekly")
            self.assertIsNone(obs.payload["windows"][0]["remaining_percent"])
            self.assertEqual(obs.payload["weekly_remaining"], Quality.UNKNOWN.value)
            missing = collect_grok(now=NOW, home=home, which=lambda _: None)
            self.assertEqual(missing.quality, Quality.UNKNOWN.value)

    def test_no_credentials_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / ".codex").mkdir()
            collect_claude(now=NOW, home=home, which=lambda _: "/usr/bin/claude")
            collect_grok(now=NOW, home=home, which=lambda _: "/usr/bin/grok")
            self.assertFalse((home / ".claude" / ".credentials.json").exists())
            self.assertFalse((home / ".codex" / "auth.json").exists())
            self.assertFalse((home / ".grok" / "auth.json").exists())

    def test_localhost_only_service(self) -> None:
        with self.assertRaises(LoopbackError):
            assert_loopback("0.0.0.0")
        with self.assertRaises(LoopbackError):
            serve_control_center(root=Path("."), host="192.0.2.9", port=9)
        fake = {
            "generated_at": "2026-09-30T12:00:00+00:00",
            "overview": [],
            "live_work": {},
            "radar": [],
            "bind": "127.0.0.1",
        }
        with tempfile.TemporaryDirectory() as directory, patch(
            "flowfoundry.control_center.service.collect_snapshot", return_value=fake
        ):
            server = serve_control_center(root=Path(directory), host="127.0.0.1", port=0)
            host, port = server.server_address[:2]
            self.assertEqual(host, "127.0.0.1")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn = HTTPConnection("127.0.0.1", port, timeout=5)
                conn.request("GET", "/")
                page = conn.getresponse().read().decode("utf-8")
                conn.request("GET", "/api/status")
                payload = json.loads(conn.getresponse().read().decode("utf-8"))
                conn.request("GET", "/index.html")
                index_status = conn.getresponse().status
                conn.request("GET", "/providers")
                provider_route_status = conn.getresponse().status
                conn.close()
            finally:
                server.shutdown()
                server.server_close()
            self.assertIn("模型容量", page)
            self.assertIn("容量分析", page)
            self.assertIn("当前任务", page)
            self.assertIn("最新动态", page)
            self.assertIn("帮助与数据口径", page)
            self.assertIn("Noto Sans CJK SC", page)
            self.assertIn("chartSvg", page)
            self.assertIn("Theil–Sen", page)
            self.assertIn("UNKNOWN 表示没有可信观测", page)
            self.assertNotIn('href="/overview"', page)
            self.assertNotIn('href="/providers"', page)
            self.assertNotIn("sk-ant-", page)
            self.assertEqual(index_status, 404)
            self.assertEqual(provider_route_status, 404)
            self.assertFalse(contains_secret(payload))
            self.assertEqual(payload["bind"], "127.0.0.1")

    def test_status_returns_while_collectors_run(self) -> None:
        fake = {
            "generated_at": "2026-09-30T12:00:00+00:00",
            "overview": [{"display_name": "Codex"}],
            "live_work": {},
            "radar": [],
            "bind": "127.0.0.1",
        }
        release = threading.Event()

        def slow(*_args: object, **_kwargs: object) -> dict:
            release.wait(timeout=5)
            return fake

        with tempfile.TemporaryDirectory() as directory, patch(
            "flowfoundry.control_center.service.collect_snapshot", side_effect=slow
        ):
            server = serve_control_center(root=Path(directory), host="127.0.0.1", port=0)
            host, port = server.server_address[:2]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                started = time.monotonic()
                conn = HTTPConnection("127.0.0.1", port, timeout=2)
                conn.request("GET", "/api/status")
                payload = json.loads(conn.getresponse().read().decode("utf-8"))
                conn.close()
                elapsed = time.monotonic() - started
            finally:
                release.set()
                server.shutdown()
                server.server_close()
        self.assertLess(elapsed, 1.0)
        self.assertEqual(payload["bind"], "127.0.0.1")
        self.assertTrue(payload.get("collecting"))

    def test_normalized_status_schema_and_unknown_remains_unknown(self) -> None:
        snapshot = collect_snapshot(
            root=Path("."),
            home=Path("."),
            now=NOW,
            collectors={
                "codex": lambda now: parse_rate_limits(CODEX_PAYLOAD, now=now),
                "claude": lambda now, home: collect_claude(now=now, home=home, which=lambda _: "/bin/claude"),
                "grok": lambda now, home: collect_grok(now=now, home=home, which=lambda _: None),
                "gemini": lambda now, home: Observation.unknown(
                    kind="health",
                    provider="google",
                    source="test",
                    now=now,
                    payload={"display_name": "Gemini CLI", "windows": []},
                ),
                "live_work": lambda now, root: collect_live_work(now=now, root=root),
                "radar": lambda now, home: parse_atom(ATOM, source="test", provider="openai", now=now),
            },
        )
        self.assertEqual(snapshot["overview"][0]["quality"], Quality.EXACT_OFFICIAL.value)
        claude = snapshot["overview"][1]
        self.assertEqual(claude["windows"][0]["remaining_percent"], None)
        self.assertEqual(claude["quality"], Quality.UNKNOWN.value)
        self.assertNotIn("offline", json.dumps(snapshot))

    def test_stale_data_relabeling(self) -> None:
        obs = parse_rate_limits(CODEX_PAYLOAD, now=NOW - timedelta(hours=2))
        relabeled = relabel_stale(obs, now=NOW, max_age=timedelta(minutes=15))
        self.assertEqual(relabeled.quality, Quality.OBSERVED_INTERNAL.value)
        self.assertTrue(relabeled.payload["stale"])
        self.assertEqual(relabeled.payload["original_quality"], Quality.EXACT_OFFICIAL.value)

    def test_live_work_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / ".flowfoundry" / "do" / "goal-20260930-test"
            run.mkdir(parents=True)
            (run / "result.json").write_text(
                json.dumps(
                    {
                        "schema_version": 4,
                        "run_id": "goal-20260930-test",
                        "goal": "inspect parser",
                        "executor": "codex",
                        "responsible_agent": "Codex",
                        "status": "PASS",
                        "execution_status": "completed",
                        "elapsed_seconds": 12.5,
                        "agent_response": "secret chain of thought should stay out",
                        "usage": {"input_tokens": 9, "output_tokens": 3},
                        "verification": {
                            "evidence": [{"kind": "command", "command": "python -m unittest"}]
                        },
                    }
                ),
                encoding="utf-8",
            )
            obs = collect_live_work(now=NOW, root=root)
            self.assertEqual(obs.quality, Quality.EXACT_LOCAL.value)
            self.assertEqual(obs.payload["responsible_worker"], "Codex")
            self.assertEqual(obs.payload["goal"], "inspect parser")
            self.assertEqual(obs.payload["tokens"]["input_tokens"], 9)
            self.assertEqual(obs.payload["events"][0]["kind"], "command")
            self.assertEqual(obs.payload["events"][0]["detail"], "python -m unittest")
            self.assertNotIn("agent_response", obs.payload)
            self.assertNotIn("secret chain of thought", json.dumps(obs.to_dict()))

    def test_running_live_work_is_not_overlaid_by_an_old_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_run = root / ".flowfoundry" / "do" / "goal-20260929-old"
            old_run.mkdir(parents=True)
            (old_run / "result.json").write_text(
                json.dumps(
                    {
                        "schema_version": 4,
                        "run_id": "goal-20260929-old",
                        "goal": "old completed goal",
                        "responsible_agent": "Codex",
                        "status": "PASS",
                        "execution_status": "completed",
                    }
                ),
                encoding="utf-8",
            )
            save_task(
                root,
                CoordinatorTask(
                    task_id="task-20260930-running",
                    parent_goal="current founder goal",
                    worker_capability="coding",
                    instruction="current founder goal",
                    context_refs=(),
                    dependencies=(),
                    allowed_actions=(),
                    expected_artifact="working tree",
                    acceptance_criteria="tests pass",
                    status="RUNNING",
                    phase="EXECUTING",
                    pid=os.getpid(),
                ),
            )
            obs = collect_live_work(now=NOW, root=root)
            self.assertEqual(obs.payload["goal"], "current founder goal")
            self.assertEqual(obs.payload["responsible_worker"], "Codex")
            self.assertEqual(obs.payload["run_state"], "RUNNING")
            self.assertEqual(obs.payload["operation"], "FlowFoundry task state: RUNNING")
            self.assertEqual(obs.payload["events"][0]["kind"], "state_transition")

    def test_radar_feed_parsing(self) -> None:
        items = parse_atom(ATOM, source="https://github.com/openai/codex/releases.atom", provider="openai", now=NOW)
        self.assertEqual(items[0].payload["title"], "v0.159.2")
        self.assertEqual(items[0].quality, Quality.EXACT_OFFICIAL.value)
        bad = parse_atom("<not xml", source="x", provider="openai", now=NOW)
        self.assertEqual(bad[0].quality, Quality.UNKNOWN.value)
        grok_items = parse_grok_changelog(
            [{"category": "features", "description": "Added /usage", "breaking_change": False}],
            now=NOW,
            version="1.0.44",
        )
        self.assertEqual(grok_items[0].payload["version"], "1.0.44")
        catalog = parse_models_dev_headers({"ETag": "abc", "Content-Length": "12"}, now=NOW, body=b"catalog")
        self.assertEqual(catalog.source_class, "COMMUNITY_CURATED")
        self.assertEqual(len(catalog.payload["sha256"]), 64)

    def test_redact_secrets_from_status_json(self) -> None:
        redacted = redact_value(
            {
                "token": "sk-ant-abc",
                "ok": True,
                "note": "Bearer abcdefghijklmnop",
                "tokens": {"input_tokens": 9, "output_tokens": 3},
                "local_tokens": {"input_tokens": 4},
            }
        )
        self.assertEqual(redacted["token"], "[redacted]")
        self.assertEqual(redacted["tokens"]["input_tokens"], 9)
        self.assertEqual(redacted["local_tokens"]["input_tokens"], 4)
        self.assertNotIn("sk-ant-abc", json.dumps(redacted))
        self.assertFalse(contains_secret(redacted["tokens"]))

    def test_existing_providers_unaffected(self) -> None:
        parser = build_parser()
        commands = set(parser._subparsers._group_actions[0].choices)
        self.assertIn("do", commands)
        self.assertIn("ask", commands)
        self.assertIn("control-center", commands)
        with tempfile.TemporaryDirectory() as directory:
            status = environment_status(Path(directory))
            self.assertIn("ready", status)
        output = io.StringIO()
        with patch("flowfoundry.cli.environment_status", return_value={"ready": True, "executor": "codex"}), redirect_stdout(output):
            result = main(["validate", "--workspace", "."])
        self.assertEqual(result, 0)

    def test_control_center_once_json(self) -> None:
        output = io.StringIO()
        error = io.StringIO()
        fake = {
            "generated_at": "now",
            "overview": [],
            "live_work": {},
            "radar": [],
            "bind": "127.0.0.1",
        }
        with tempfile.TemporaryDirectory() as directory, patch(
            "flowfoundry.control_center.snapshot.collect_snapshot", return_value=fake
        ), redirect_stdout(output), redirect_stderr(error):
            code = main(["control-center", "--once", "--workspace", directory])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["bind"], "127.0.0.1")
        self.assertEqual(error.getvalue(), "")

    def test_control_center_keyboard_interrupt_closes_without_shutdown(self) -> None:
        class InterruptedServer:
            server_address = ("127.0.0.1", 4730)

            def __init__(self) -> None:
                self.closed = False

            def serve_forever(self) -> None:
                raise KeyboardInterrupt

            def shutdown(self) -> None:
                self.fail("shutdown must not run from the serve_forever thread")

            def server_close(self) -> None:
                self.closed = True

            def fail(self, message: str) -> None:
                raise AssertionError(message)

        server = InterruptedServer()
        error = io.StringIO()
        with tempfile.TemporaryDirectory() as directory, patch(
            "flowfoundry.control_center.service.serve_control_center",
            return_value=server,
        ), redirect_stderr(error):
            code = main(["control-center", "--workspace", directory])
        self.assertEqual(code, 0)
        self.assertTrue(server.closed)
        self.assertIn("http://127.0.0.1:4730", error.getvalue())

    def test_long_running_acceptance_terminates_and_restarts(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"HOME": directory}
        ):
            report = run_control_center_acceptance(
                root=Path(directory),
                host="127.0.0.1",
                port=port,
                timeout_seconds=15,
            )
        self.assertEqual(report["result"], "PASS")
        self.assertTrue(report["restart_verified"])
        self.assertFalse(report["orphan_process"])
        self.assertEqual(len(report["cycles"]), 2)
        first_pid, second_pid = (item["pid"] for item in report["cycles"])
        self.assertNotEqual(first_pid, second_pid)
        for cycle in report["cycles"]:
            self.assertEqual(cycle["health"]["status"], 200)
            self.assertEqual(cycle["responses"]["/"], 200)
            self.assertEqual(cycle["responses"]["/api/status"], 200)
            self.assertEqual(cycle["responses"]["provider_cards"], 4)
            self.assertGreaterEqual(cycle["responses"]["analytics_series"], 4)
            self.assertGreaterEqual(cycle["responses"]["history_rows"], 4)
            self.assertTrue(cycle["cleanup"]["pid_gone"])
            self.assertTrue(cycle["cleanup"]["process_group_gone"])
            self.assertTrue(cycle["cleanup"]["port_released"])
            self.assertIn("FlowFoundry Model Control Center", cycle["cleanup"]["stderr"])
            self.assertIn("Control Center:", cycle["cleanup"]["stderr"])

    def test_occupied_port_acceptance_fails_bounded_without_killing_owner(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as owner:
            owner.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            owner.bind(("127.0.0.1", 0))
            owner.listen()
            port = owner.getsockname()[1]
            started = time.monotonic()
            with tempfile.TemporaryDirectory() as directory, patch.dict(
                os.environ, {"HOME": directory}
            ), self.assertRaises(ControlCenterAcceptanceError) as raised:
                run_control_center_acceptance(
                    root=Path(directory),
                    host="127.0.0.1",
                    port=port,
                    timeout_seconds=2,
                )
            self.assertLess(time.monotonic() - started, 3)
            self.assertIn("Address already in use", str(raised.exception))
            self.assertEqual(owner.getsockname()[1], port)

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flowfoundry.goal_runner import (
    _git_head,
    _git_status,
    _repository_changes,
    _workspace_baseline,
    environment_status,
    run_goal,
)


EVENTS = "\n".join(
    (
        '{"type":"thread.started","thread_id":"thread-123"}',
        '{"type":"item.started","item":{"type":"command_execution",'
        '"command":"python -m unittest","status":"in_progress"}}',
        '{"type":"item.completed","item":{"type":"command_execution",'
        '"command":"python -m unittest","status":"completed","exit_code":0}}',
        '{"type":"item.completed","item":{"type":"agent_message","text":"done"}}',
        '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":2}}',
    )
)


class CapturingInput:
    def __init__(self) -> None:
        self.value = ""
        self.closed = False

    def write(self, value: str) -> int:
        self.value += value
        return len(value)

    def close(self) -> None:
        self.closed = True


class FakeProcess:
    def __init__(self, command: list[str], *, hangs: bool = False) -> None:
        self.command = command
        self.stdin = CapturingInput()
        self.stdout = io.StringIO(EVENTS + "\n")
        self.stderr = io.StringIO("provider diagnostic\n")
        self.hangs = hangs
        self.killed = False

    def wait(self, timeout: float | None = None) -> int:
        if self.hangs and not self.killed:
            raise subprocess.TimeoutExpired(self.command, timeout)
        return -9 if self.killed else 0

    def kill(self) -> None:
        self.killed = True


class GoalRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.processes: list[FakeProcess] = []

    def completed(self, command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        if command[:3] == ["git", "status", "--porcelain=v1"]:
            return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, stdout="head-123\n", stderr="")
        if command[:3] == ["git", "diff", "--check"]:
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        self.fail(f"unexpected subprocess.run call: {command}")

    def popen(self, command: list[str], **_: object) -> FakeProcess:
        self.assertEqual(command[:2], ["/usr/bin/codex", "exec"])
        self.assertIn("approval_policy=\"never\"", command)
        process = FakeProcess(command)
        self.processes.append(process)
        return process

    def test_direct_goal_records_compact_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.goal_runner.shutil.which", return_value="/usr/bin/codex"
        ), patch(
            "flowfoundry.goal_runner.subprocess.run", side_effect=self.completed
        ), patch("flowfoundry.goal_runner.subprocess.Popen", side_effect=self.popen):
            root = Path(temp_dir)
            progress: list[str] = []
            code, result = run_goal(
                "fix one bug",
                root=root,
                runs_root=root / ".flowfoundry" / "do",
                verbose=True,
                progress=progress.append,
            )
            self.assertEqual(code, 0)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["agent_response"], "done")
            self.assertEqual(result["responsible_agent"], "Codex")
            self.assertEqual(result["verification"]["status"], "PASS")
            self.assertEqual(result["thread_id"], "thread-123")
            result_path = root / ".flowfoundry" / "do" / result["run_id"] / "result.json"
            self.assertEqual(json.loads(result_path.read_text())["final_message"], "done")
            self.assertIn("FlowFoundry authority boundary", self.processes[0].stdin.value)
            self.assertIn("shown directly to the Founder", self.processes[0].stdin.value)
            self.assertIn("compact code or diff excerpts", self.processes[0].stdin.value)
            self.assertTrue(self.processes[0].stdin.closed)
            self.assertIn("executor session ready", progress)
            self.assertIn("running: python -m unittest", progress)
            self.assertIn("command passed: python -m unittest", progress)
            self.assertTrue(any(item.startswith("checking: git diff") for item in progress))
            events_path = result_path.with_name("events.jsonl")
            self.assertEqual(events_path.read_text(), EVENTS + "\n")
            self.assertEqual(
                result_path.with_name("stderr.log").read_text(),
                "provider diagnostic\n",
            )
            self.assertEqual(len(self.processes), 1, "normal work must not add a reporter call")

    def test_substantive_agent_response_survives_persistence(self) -> None:
        response = (
            "I inspected the parser and found that evaluator prose replaced the Worker report.\n\n"
            "Changed files:\n- src/reporting.py\n- tests/test_reporting.py\n\n"
            "Important code:\n```python\nagent_response = provider.final_message\n```\n\n"
            "Tests: python -m unittest tests.test_reporting — PASS.\n"
            "Remaining limitation: external provider behavior was not tested."
        )
        events = EVENTS.replace('"text":"done"', '"text":' + json.dumps(response))
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.goal_runner.shutil.which", return_value="/usr/bin/codex"
        ), patch(
            "flowfoundry.goal_runner.subprocess.run", side_effect=self.completed
        ), patch(
            "flowfoundry.goal_runner.subprocess.Popen", side_effect=self.popen
        ), patch(__name__ + ".EVENTS", events):
            root = Path(temp_dir)
            runs = root / ".flowfoundry" / "do"
            _, result = run_goal("fix result reporting", root=root, runs_root=runs)
            saved = json.loads((runs / result["run_id"] / "result.json").read_text())

        self.assertEqual(saved["agent_response"], response)
        self.assertEqual(saved["result"], response)
        self.assertEqual(saved["verification"]["status"], "PASS")
        self.assertEqual(len(self.processes), 1)

    def test_repository_change_evidence_excludes_preexisting_founder_edit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            source = root / "reporting.py"
            source.write_text("agent_response = 'original'\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "reporting.py"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=FlowFoundry Test",
                    "-c", "user.email=test@flowfoundry.invalid", "commit", "-qm", "base",
                ],
                check=True,
            )
            source.write_text("agent_response = 'founder draft'\n", encoding="utf-8")
            before_status = _git_status(root)
            before_head = _git_head(root)
            before_dirty = _workspace_baseline(root, before_status)

            source.write_text(
                "agent_response = provider.final_message\n",
                encoding="utf-8",
            )
            paths, diff, truncated = _repository_changes(
                root,
                before_status=before_status,
                before_head=before_head,
                before_dirty=before_dirty,
                after_status=_git_status(root),
                after_head=_git_head(root),
            )

        self.assertEqual(paths, ["reporting.py"])
        self.assertIn("-agent_response = 'founder draft'", diff)
        self.assertIn("+agent_response = provider.final_message", diff)
        self.assertNotIn("'original'", diff)
        self.assertFalse(truncated)

    def test_validate_requires_codex_login_and_git(self) -> None:
        def probe(command: list[str], **_: object) -> subprocess.CompletedProcess:
            if command[-2:] == ["login", "status"]:
                return subprocess.CompletedProcess(command, 0, stdout="Logged in", stderr="")
            if command[-1:] == ["--version"]:
                return subprocess.CompletedProcess(command, 0, stdout="codex-cli 1.0\n", stderr="")
            return subprocess.CompletedProcess(command, 0, stdout="true\n", stderr="")

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.goal_runner.shutil.which",
            side_effect=lambda name: f"/usr/bin/{name}",
        ), patch("flowfoundry.goal_runner.subprocess.run", side_effect=probe):
            status = environment_status(Path(temp_dir))
        self.assertTrue(status["ready"])
        self.assertTrue(status["executor_authenticated"])
        self.assertEqual(status["executor_version"], "codex-cli 1.0")

    def test_repaired_test_failure_produces_passing_saved_result(self) -> None:
        failed_test = json.dumps({
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": "python -m unittest",
                "status": "completed",
                "exit_code": 1,
            },
        })
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.goal_runner.shutil.which", return_value="/usr/bin/codex"
        ), patch(
            "flowfoundry.goal_runner.subprocess.run", side_effect=self.completed
        ), patch(
            "flowfoundry.goal_runner.subprocess.Popen", side_effect=self.popen
        ), patch(__name__ + ".EVENTS", failed_test + "\n" + EVENTS):
            root = Path(temp_dir)
            runs = root / ".flowfoundry" / "do"
            code, result = run_goal("fix failing test", root=root, runs_root=runs)
            saved = json.loads((runs / result["run_id"] / "result.json").read_text())
        self.assertEqual(code, 0)
        self.assertEqual(saved["status"], "PASS")
        evidence = saved["verification"]["evidence"]
        self.assertEqual([item["exit_code"] for item in evidence], [1, 0, 0])

    def test_printed_test_command_cannot_create_passing_saved_result(self) -> None:
        events = [json.loads(line) for line in EVENTS.splitlines()]
        for event in events:
            item = event.get("item", {})
            if item.get("type") == "command_execution":
                item["command"] = "echo 'python -m unittest'"
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.goal_runner.shutil.which", return_value="/usr/bin/codex"
        ), patch(
            "flowfoundry.goal_runner.subprocess.run", side_effect=self.completed
        ), patch(
            "flowfoundry.goal_runner.subprocess.Popen", side_effect=self.popen
        ), patch(__name__ + ".EVENTS", "\n".join(json.dumps(event) for event in events)):
            root = Path(temp_dir)
            runs = root / ".flowfoundry" / "do"
            _, result = run_goal("fix a bug", root=root, runs_root=runs)
            saved = json.loads((runs / result["run_id"] / "result.json").read_text())
        self.assertEqual(saved["status"], "UNKNOWN")
        self.assertFalse(any(item["acceptance_check"] for item in saved["verification"]["evidence"]))

    def test_resume_uses_recorded_thread(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.goal_runner.shutil.which", return_value="/usr/bin/codex"
        ), patch(
            "flowfoundry.goal_runner.subprocess.run", side_effect=self.completed
        ), patch("flowfoundry.goal_runner.subprocess.Popen", side_effect=self.popen):
            root = Path(temp_dir)
            runs = root / ".flowfoundry" / "do"
            _, first = run_goal("fix first bug", root=root, runs_root=runs)
            code, second = run_goal(
                "continue fixing the bug",
                root=root,
                runs_root=runs,
                resume=first["run_id"],
            )
            self.assertEqual(code, 0)
            self.assertEqual(second["resume_of"], first["run_id"])
            self.assertIn("resume", self.processes[-1].command)
            self.assertIn("thread-123", self.processes[-1].command)
            self.assertIn('sandbox_mode="workspace-write"', self.processes[-1].command)

    def test_read_only_resume_reasserts_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.goal_runner.shutil.which", return_value="/usr/bin/codex"
        ), patch(
            "flowfoundry.goal_runner.subprocess.run", side_effect=self.completed
        ), patch("flowfoundry.goal_runner.subprocess.Popen", side_effect=self.popen):
            root = Path(temp_dir)
            runs = root / ".flowfoundry" / "do"
            _, first = run_goal("fix first bug", root=root, runs_root=runs)
            run_goal(
                "continue",
                root=root,
                runs_root=runs,
                resume=first["run_id"],
                read_only=True,
            )
            resume_command = self.processes[-1].command
            self.assertIn('sandbox_mode="read-only"', resume_command)

    def test_timeout_preserves_partial_evidence_and_returns_124(self) -> None:
        def hanging_popen(command: list[str], **_: object) -> FakeProcess:
            process = FakeProcess(command, hangs=True)
            self.processes.append(process)
            return process

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.goal_runner.shutil.which", return_value="/usr/bin/codex"
        ), patch(
            "flowfoundry.goal_runner.subprocess.run", side_effect=self.completed
        ), patch(
            "flowfoundry.goal_runner.subprocess.Popen", side_effect=hanging_popen
        ):
            root = Path(temp_dir)
            code, result = run_goal(
                "work until timeout",
                root=root,
                runs_root=root / ".flowfoundry" / "do",
                timeout_seconds=1,
                verbose=True,
            )
            self.assertEqual(code, 1)
            self.assertEqual(result["return_code"], 124)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["execution_status"], "failed")
            self.assertTrue(self.processes[-1].killed)
            evidence = root / ".flowfoundry" / "do" / result["run_id"]
            self.assertIn("thread.started", (evidence / "events.jsonl").read_text())
            self.assertIn("timed out after 1s", (evidence / "stderr.log").read_text())

    def test_read_only_rejects_unsandboxed_custom_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(ValueError, "workspace-write"):
                run_goal(
                    "inspect",
                    root=root,
                    runs_root=root / ".flowfoundry" / "do",
                    read_only=True,
                    checks=("python -m unittest",),
                )

    def test_capability_reduction_controls_the_real_worker_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.goal_runner.shutil.which", return_value="/usr/bin/codex"
        ):
            root = Path(temp_dir)
            _, result = run_goal(
                "summarize the project",
                root=root,
                runs_root=root / ".flowfoundry" / "do",
                permission_level=4,
                dry_run=True,
            )

        self.assertEqual(result["selection"]["session_permission_ceiling"], 4)
        self.assertEqual(result["selection"]["effective_permission"], 1)
        self.assertEqual(result["sandbox"], "read-only")
        self.assertIn("read-only", result["command"])

    def test_resume_reuses_recorded_capability_under_current_ceiling(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.goal_runner.shutil.which", return_value="/usr/bin/codex"
        ):
            root = Path(temp_dir)
            runs = root / ".flowfoundry" / "do"
            previous = runs / "goal-previous"
            previous.mkdir(parents=True)
            (previous / "result.json").write_text(
                json.dumps(
                    {
                        "project_root": str(root),
                        "thread_id": "thread-previous",
                        "selection": {"task_kind": "coding"},
                    }
                ),
                encoding="utf-8",
            )
            _, result = run_goal(
                "continue the previous task",
                root=root,
                runs_root=runs,
                resume="goal-previous",
                permission_level=3,
                dry_run=True,
            )

        self.assertEqual(result["selection"]["task_kind"], "coding")
        self.assertEqual(result["selection"]["effective_permission"], 3)
        self.assertEqual(result["sandbox"], "workspace-write")
        self.assertIn("thread-previous", result["command"])


if __name__ == "__main__":
    unittest.main()

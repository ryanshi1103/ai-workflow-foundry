from __future__ import annotations

import io
import os
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from flowfoundry.cli import main
from flowfoundry.orchestration.execution import ProviderExecutionHandle
from flowfoundry.orchestration.meeting import MeetingRuntime
from flowfoundry.orchestration.models import AgentSpec, TaskStatus
from flowfoundry.orchestration.planner import RuleBasedPlanner
from flowfoundry.orchestration.providers import LocalCommandProvider
from flowfoundry.orchestration.recovery import RecoveryManager
from flowfoundry.orchestration.registry import AgentRegistry
from flowfoundry.orchestration.router import TaskRouter
from flowfoundry.orchestration.scheduler import RunScheduler
from flowfoundry.orchestration.workspace import RunWorkspace, atomic_write_json


HARNESS = Path(__file__).parent / "fixtures" / "provider_process_harness.py"


class NativeCancellationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.runs_root = self.temp_path / "runs"
        self.plan = RuleBasedPlanner().plan(
            "Implement offline collaboration",
            execution_mode="multi_agent",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def agent_registry(
        self,
        mode: str,
        ready_path: Path,
        child_pid_path: Path | None = None,
    ) -> AgentRegistry:
        common = {
            "cost_class": "free",
            "concurrency_limit": 1,
            "permission_profile": ("read_workspace", "write_workspace"),
            "context_limit": 10_000,
            "availability": True,
            "workspace_mode": "shared",
            "local": True,
        }
        builder_command = (
            sys.executable,
            str(HARNESS),
            mode,
            str(ready_path),
            str(child_pid_path) if child_pid_path is not None else "-",
        )
        complete_command = (sys.executable, str(HARNESS), "complete", "-")
        return AgentRegistry(
            (
                AgentSpec(
                    id="harness-builder",
                    display_name="Harness Builder",
                    provider="local",
                    role="builder",
                    capabilities=("implementation",),
                    command_template=builder_command,
                    **common,
                ),
                AgentSpec(
                    id="harness-reviewer",
                    display_name="Harness Reviewer",
                    provider="local",
                    role="reviewer",
                    capabilities=("review", "implementation"),
                    command_template=complete_command,
                    **common,
                ),
                AgentSpec(
                    id="harness-tester",
                    display_name="Harness Tester",
                    provider="local",
                    role="tester",
                    capabilities=("testing",),
                    command_template=complete_command,
                    **common,
                ),
            )
        )

    @staticmethod
    def wait_for(path: Path, timeout: float = 5.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if path.exists():
                return
            time.sleep(0.02)
        raise AssertionError(f"timed out waiting for {path}")

    def start_and_cancel(
        self,
        mode: str,
        *,
        run_id: str,
        grace_seconds: float,
        child_pid_path: Path | None = None,
    ) -> tuple[RunWorkspace, list[BaseException]]:
        ready = self.temp_path / f"{run_id}.ready"
        workspace = RunWorkspace.create(self.runs_root, run_id, self.plan)
        registry = self.agent_registry(mode, ready, child_pid_path)
        provider = LocalCommandProvider(enabled=True)
        errors: list[BaseException] = []

        def run() -> None:
            try:
                RunScheduler(TaskRouter(registry), provider).run(workspace)
            except BaseException as exc:  # test thread must report provider boundary failures
                errors.append(exc)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        self.wait_for(ready)
        MeetingRuntime(TaskRouter(registry), provider).cancel(
            workspace,
            grace_period_seconds=grace_seconds,
        )
        thread.join(timeout=8)
        self.assertFalse(thread.is_alive(), "cancelled scheduler thread did not finish")
        return workspace, errors

    def test_cancel_before_start_makes_zero_provider_calls(self) -> None:
        workspace = RunWorkspace.create(self.runs_root, "pre-start", self.plan)
        registry = self.agent_registry("complete", self.temp_path / "unused.ready")
        provider = LocalCommandProvider(enabled=True)
        manifest = MeetingRuntime(TaskRouter(registry), provider).cancel(workspace)

        self.assertEqual(manifest["meeting"]["state"], "cancelled")
        self.assertEqual(list(workspace.contained("executions").glob("*/execution.json")), [])
        RunScheduler(TaskRouter(registry), provider).run(workspace)
        self.assertEqual(list(workspace.contained("executions").glob("*/execution.json")), [])

    def test_running_process_uses_graceful_group_termination(self) -> None:
        workspace, errors = self.start_and_cancel(
            "graceful",
            run_id="graceful",
            grace_seconds=0.5,
        )
        self.assertEqual(errors, [])
        manifest = workspace.manifest()
        cancellation = manifest["meeting"]["cancellation"]
        self.assertEqual(manifest["meeting"]["state"], "cancelled")
        self.assertTrue(cancellation["graceful_termination"])
        self.assertFalse(cancellation["forced_termination"])
        self.assertEqual(cancellation["termination_status"], "graceful")

    def test_cli_cancel_terminates_active_local_process_and_status_is_redacted(self) -> None:
        ready = self.temp_path / "cli.ready"
        workspace = RunWorkspace.create(self.runs_root, "cli-active", self.plan)
        registry = self.agent_registry("graceful", ready)
        provider = LocalCommandProvider(enabled=True)
        thread = threading.Thread(
            target=RunScheduler(TaskRouter(registry), provider).run,
            args=(workspace,),
            daemon=True,
        )
        thread.start()
        self.wait_for(ready)
        output = io.StringIO()
        error = io.StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            result = main(
                [
                    "team",
                    "cancel",
                    "cli-active",
                    "--runs-root",
                    str(self.runs_root),
                ]
            )
        thread.join(timeout=8)
        self.assertEqual((result, error.getvalue()), (0, ""))
        self.assertFalse(thread.is_alive())
        self.assertIn('"state": "cancelled"', output.getvalue())

        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                main(
                    [
                        "team",
                        "status",
                        "cli-active",
                        "--runs-root",
                        str(self.runs_root),
                    ]
                ),
                0,
            )
        status_output = output.getvalue()
        self.assertIn('"termination_status": "cancelled"', status_output)
        self.assertNotIn("provider_process_harness.py", status_output)
        self.assertNotIn("command_fingerprint", status_output)

    def test_forced_termination_escalates_after_grace_period(self) -> None:
        workspace, errors = self.start_and_cancel(
            "ignore",
            run_id="forced",
            grace_seconds=0.1,
        )
        self.assertEqual(errors, [])
        cancellation = workspace.manifest()["meeting"]["cancellation"]
        self.assertTrue(cancellation["forced_termination"])
        self.assertFalse(cancellation["graceful_termination"])
        execution = ProviderExecutionHandle.status_for_run(workspace.path)[0]
        self.assertEqual(execution["state"], "cancelled")

    def test_process_group_cancel_leaves_no_child(self) -> None:
        child_pid_path = self.temp_path / "child.pid"
        workspace, errors = self.start_and_cancel(
            "child",
            run_id="child-group",
            grace_seconds=0.1,
            child_pid_path=child_pid_path,
        )
        self.assertEqual(errors, [])
        child_pid = int(child_pid_path.read_text(encoding="utf-8"))
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and self.process_alive(child_pid):
            time.sleep(0.05)
        self.assertFalse(self.process_alive(child_pid))
        self.assertTrue(workspace.manifest()["meeting"]["cancellation"]["forced_termination"])

    def test_double_cancel_is_terminal_no_op_and_experience_is_written_once(self) -> None:
        workspace, errors = self.start_and_cancel(
            "graceful",
            run_id="double",
            grace_seconds=0.5,
        )
        self.assertEqual(errors, [])
        experience_path = workspace.contained("final", "meeting-experience.json")
        before_mtime = experience_path.stat().st_mtime_ns
        before_receipts = list(workspace.contained("artifacts", "meeting", "calls").glob("*.json"))
        registry = self.agent_registry("complete", self.temp_path / "unused-double.ready")
        manifest = MeetingRuntime(
            TaskRouter(registry),
            LocalCommandProvider(enabled=True),
        ).cancel(workspace)
        self.assertEqual(manifest["meeting"]["state"], "cancelled")
        self.assertEqual(experience_path.stat().st_mtime_ns, before_mtime)
        self.assertEqual(
            list(workspace.contained("artifacts", "meeting", "calls").glob("*.json")),
            before_receipts,
        )

    def test_cancel_preserves_partial_output_usage_and_experience(self) -> None:
        workspace, errors = self.start_and_cancel(
            "graceful",
            run_id="partial",
            grace_seconds=0.5,
        )
        self.assertEqual(errors, [])
        result = workspace.read_json("tasks/build/result.json")
        self.assertTrue(result["partial_result"])
        self.assertIn("partial-before-cancel", result["outputs"]["stdout"])
        self.assertIsNotNone(result["usage"]["latency_ms"])
        self.assertIsNone(result["usage"]["input_tokens"])
        self.assertIsNone(result["usage"]["estimated_cost_usd"])
        experience = workspace.read_json("final/meeting-experience.json")
        self.assertTrue(experience["cancellation_requested"])
        self.assertTrue(experience["provider_running_at_cancel"])
        self.assertTrue(experience["partial_result"])
        self.assertEqual(experience["agent_calls"], 1)
        self.assertEqual(experience["final_state"], "cancelled")

    def test_resume_cancelled_run_does_not_restart_provider(self) -> None:
        workspace, errors = self.start_and_cancel(
            "graceful",
            run_id="resume-cancelled",
            grace_seconds=0.5,
        )
        self.assertEqual(errors, [])
        before = ProviderExecutionHandle.status_for_run(workspace.path)
        RecoveryManager().recover_interrupted(workspace)
        registry = self.agent_registry("complete", self.temp_path / "resume-unused.ready")
        RunScheduler(TaskRouter(registry), LocalCommandProvider(enabled=True)).run(workspace)
        self.assertEqual(ProviderExecutionHandle.status_for_run(workspace.path), before)

    def test_explicit_retry_creates_new_execution_and_preserves_cancel_experience(self) -> None:
        workspace, errors = self.start_and_cancel(
            "graceful",
            run_id="retry-cancelled",
            grace_seconds=0.5,
        )
        self.assertEqual(errors, [])
        first_ids = {
            item["execution_id"] for item in ProviderExecutionHandle.status_for_run(workspace.path)
        }
        first_experience = workspace.contained("final", "meeting-experience.json")
        first_mtime = first_experience.stat().st_mtime_ns

        RecoveryManager().retry_failed_task(workspace, "build")
        registry = self.agent_registry("complete", self.temp_path / "retry.ready")
        RunScheduler(TaskRouter(registry), LocalCommandProvider(enabled=True)).run(workspace)

        statuses = ProviderExecutionHandle.status_for_run(workspace.path)
        new_ids = {item["execution_id"] for item in statuses} - first_ids
        self.assertTrue(new_ids)
        self.assertEqual(first_experience.stat().st_mtime_ns, first_mtime)
        self.assertTrue(workspace.contained("final", "meeting-experience-attempt-2.json").is_file())
        retry_receipt = workspace.contained(
            "artifacts", "meeting", "calls", "round1-build-attempt-2.json"
        )
        self.assertTrue(retry_receipt.is_file())

    def test_completion_wins_when_process_exited_before_physical_cancel(self) -> None:
        workspace = RunWorkspace.create(self.runs_root, "race", self.plan)
        handle = ProviderExecutionHandle.start(
            [sys.executable, str(HARNESS), "complete", "-"],
            provider="local",
            task_id="build",
            participant_id="harness-builder",
            task_dir=workspace.task_dir("build"),
            project_root=workspace.project_root,
        )
        time.sleep(0.15)
        outcome = ProviderExecutionHandle(handle.path).cancel(grace_seconds=0.1)
        result = handle.communicate(None, timeout_seconds=2)
        self.assertEqual(outcome.action, "already_exited")
        self.assertEqual(result.state, "completed")
        self.assertFalse(result.cancelled)
        self.assertEqual(
            ProviderExecutionHandle.status_for_run(workspace.path)[0]["state"],
            "completed",
        )

    def test_pid_identity_mismatch_refuses_to_signal(self) -> None:
        workspace = RunWorkspace.create(self.runs_root, "pid-safety", self.plan)
        execution_dir = workspace.contained("executions", "forged")
        execution_dir.mkdir(mode=0o700)
        atomic_write_json(
            execution_dir / "execution.json",
            {
                "schema_version": 1,
                "execution_id": "forged",
                "run_id": workspace.run_id,
                "provider": "local",
                "task_id": "build",
                "participant_id": "harness-builder",
                "pid": os.getpid(),
                "process_group_id": 999_999,
                "session_id": 999_999,
                "process_start_ticks": -1,
                "command_fingerprint": "mismatch",
                "state": "running",
                "started_at": "2026-08-10T00:00:00+00:00",
                "partial_result": False,
            },
        )
        registry = self.agent_registry("complete", self.temp_path / "identity-unused.ready")
        manifest = MeetingRuntime(
            TaskRouter(registry),
            LocalCommandProvider(enabled=True),
        ).cancel(workspace, grace_period_seconds=0.1)
        self.assertEqual(manifest["meeting"]["state"], "cancel_unverified")
        self.assertEqual(
            manifest["meeting"]["cancellation"]["executions"][0]["action"],
            "refused_unverified",
        )
        status = ProviderExecutionHandle.status_for_run(workspace.path)[0]
        self.assertEqual(status["state"], "cancel_unverified")
        self.assertEqual(status["termination_status"], "cancel_unverified")

    @staticmethod
    def process_alive(pid: int) -> bool:
        stat_path = Path("/proc") / str(pid) / "stat"
        try:
            content = stat_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return False
        fields = content[content.rfind(")") + 2 :].split()
        return bool(fields) and fields[0] != "Z"


if __name__ == "__main__":
    unittest.main()

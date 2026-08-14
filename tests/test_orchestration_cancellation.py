from __future__ import annotations

import hashlib
import io
import os
import signal
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import call, patch

from flowfoundry.cli import main
from flowfoundry.orchestration.execution import (
    ProcessIdentityVerification,
    ProcessIdentityState,
    ProviderExecutionHandle,
    _verify_process,
)
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
        self.assertIn(
            cancellation["executions"][0]["identity_verification"],
            {"verified_exact", "verified_exec_transition"},
        )

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
        workspace = RunWorkspace.create(self.runs_root, "forced", self.plan)
        execution_dir = workspace.contained("executions", "forced-unit")
        execution_dir.mkdir(parents=True)
        execution_path = execution_dir / "execution.json"
        atomic_write_json(
            execution_path,
            self.identity_record(
                execution_id="forced-unit",
                run_id=workspace.run_id,
                state="running",
                partial_result=False,
            ),
        )

        clock = iter((0.0, 1.0, 2.0, 4.0, 5.0, 8.0))
        verification = ProcessIdentityVerification(
            ProcessIdentityState.VERIFIED_EXACT,
            "test-owned process identity matched",
        )
        with (
            patch(
                "flowfoundry.orchestration.execution._verify_process",
                return_value=verification,
            ),
            patch(
                "flowfoundry.orchestration.execution._verified_group_exists",
                side_effect=(True, False),
            ),
            patch("flowfoundry.orchestration.execution.os.killpg") as kill_group,
            patch(
                "flowfoundry.orchestration.execution.time.monotonic",
                side_effect=lambda: next(clock),
            ),
        ):
            outcome = ProviderExecutionHandle(execution_path).cancel(grace_seconds=0.0)

        kill_group.assert_has_calls(
            [call(4242, signal.SIGTERM), call(4242, signal.SIGKILL)]
        )
        self.assertEqual(outcome.action, "forced")
        self.assertTrue(outcome.forced)
        self.assertFalse(outcome.graceful)
        execution = ProviderExecutionHandle(execution_path).read()
        self.assertEqual(execution["termination"]["method"], "sigkill")
        self.assertTrue(execution["termination"]["forced"])
        self.assertTrue(execution["termination"]["process_group_gone"])

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

    def test_same_pid_exec_transition_is_verified_and_cancellable(self) -> None:
        workspace = RunWorkspace.create(self.runs_root, "exec-transition", self.plan)
        launcher_ready = self.temp_path / "exec-launcher.ready"
        transition = self.temp_path / "exec-transition.trigger"
        target_ready = self.temp_path / "exec-target.ready"
        handle = ProviderExecutionHandle.start(
            [
                sys.executable,
                str(HARNESS),
                "exec-launcher",
                str(launcher_ready),
                str(transition),
                str(target_ready),
            ],
            provider="local",
            task_id="build",
            participant_id="harness-builder",
            task_dir=workspace.task_dir("build"),
            project_root=workspace.project_root,
        )
        try:
            self.wait_for(launcher_ready)
            before = handle.read()
            transition.write_text("exec\n", encoding="utf-8")
            self.wait_for(target_ready)
            current_fingerprint = hashlib.sha256(
                (Path("/proc") / str(before["pid"]) / "cmdline").read_bytes()
            ).hexdigest()
            self.assertNotEqual(current_fingerprint, before["command_fingerprint"])

            outcome = ProviderExecutionHandle(handle.path).cancel(grace_seconds=0.5)
            if outcome.action == "refused_unverified":
                handle._terminate_owned(grace_seconds=0.2)
            result = handle.communicate(None, timeout_seconds=2)

            self.assertEqual(outcome.action, "terminated")
            self.assertEqual(outcome.identity_verification, "verified_exec_transition")
            self.assertTrue(outcome.graceful)
            self.assertEqual(result.state, "cancelled")
        finally:
            if handle.process is not None and handle.process.poll() is None:
                handle._terminate_owned(grace_seconds=0.2)
                handle.process.communicate(timeout=2)

    def test_exec_transition_group_cancel_leaves_no_child(self) -> None:
        workspace = RunWorkspace.create(self.runs_root, "exec-transition-child", self.plan)
        launcher_ready = self.temp_path / "exec-child-launcher.ready"
        transition = self.temp_path / "exec-child-transition.trigger"
        target_ready = self.temp_path / "exec-child-target.ready"
        child_pid_path = self.temp_path / "exec-child.pid"
        handle = ProviderExecutionHandle.start(
            [
                sys.executable,
                str(HARNESS),
                "exec-launcher",
                str(launcher_ready),
                str(transition),
                str(target_ready),
                "exec-target-child",
                str(child_pid_path),
            ],
            provider="local",
            task_id="build",
            participant_id="harness-builder",
            task_dir=workspace.task_dir("build"),
            project_root=workspace.project_root,
        )
        try:
            self.wait_for(launcher_ready)
            transition.write_text("exec\n", encoding="utf-8")
            self.wait_for(target_ready)
            self.wait_for(child_pid_path)
            child_pid = int(child_pid_path.read_text(encoding="utf-8"))

            outcome = ProviderExecutionHandle(handle.path).cancel(grace_seconds=0.1)
            result = handle.communicate(None, timeout_seconds=2)

            self.assertEqual(outcome.identity_verification, "verified_exec_transition")
            self.assertEqual(outcome.action, "forced")
            self.assertTrue(outcome.forced)
            self.assertEqual(result.state, "cancelled")
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline and self.process_alive(child_pid):
                time.sleep(0.05)
            self.assertFalse(self.process_alive(child_pid))
        finally:
            if handle.process is not None and handle.process.poll() is None:
                handle._terminate_owned(grace_seconds=0.1)
                handle.process.communicate(timeout=2)

    @staticmethod
    def identity_record(**overrides: object) -> dict[str, object]:
        record: dict[str, object] = {
            "execution_id": "execution-1",
            "run_id": "run-1",
            "provider": "local",
            "task_id": "build",
            "participant_id": "harness-builder",
            "pid": 4242,
            "process_group_id": 4242,
            "session_id": 4242,
            "process_start_ticks": 101,
            "command_fingerprint": "initial-command",
        }
        record.update(overrides)
        return record

    @staticmethod
    def live_identity(**overrides: object) -> dict[str, object]:
        identity: dict[str, object] = {
            "verified": True,
            "process_state": "S",
            "process_group_id": 4242,
            "session_id": 4242,
            "process_start_ticks": 101,
            "command_fingerprint": "initial-command",
        }
        identity.update(overrides)
        return identity

    def test_exact_process_identity_verification(self) -> None:
        with patch(
            "flowfoundry.orchestration.execution._process_identity",
            return_value=self.live_identity(),
        ):
            verification = _verify_process(self.identity_record())
        self.assertEqual(verification.state, ProcessIdentityState.VERIFIED_EXACT)
        self.assertTrue(verification.signal_allowed)

    def test_command_change_with_hard_anchors_is_exec_transition(self) -> None:
        with patch(
            "flowfoundry.orchestration.execution._process_identity",
            return_value=self.live_identity(command_fingerprint="runtime-command"),
        ):
            verification = _verify_process(self.identity_record())
        self.assertEqual(
            verification.state,
            ProcessIdentityState.VERIFIED_EXEC_TRANSITION,
        )
        self.assertTrue(verification.signal_allowed)

    def test_pid_reuse_start_ticks_mismatch_is_rejected(self) -> None:
        with patch(
            "flowfoundry.orchestration.execution._process_identity",
            return_value=self.live_identity(process_start_ticks=202),
        ):
            verification = _verify_process(self.identity_record())
        self.assertEqual(verification.state, ProcessIdentityState.MISMATCH)
        self.assertEqual(verification.reason, "start_ticks_mismatch")
        self.assertFalse(verification.signal_allowed)

    def test_process_group_mismatch_is_rejected(self) -> None:
        with patch(
            "flowfoundry.orchestration.execution._process_identity",
            return_value=self.live_identity(process_group_id=5252),
        ):
            verification = _verify_process(self.identity_record())
        self.assertEqual(verification.state, ProcessIdentityState.MISMATCH)
        self.assertEqual(verification.reason, "pgid_mismatch")

    def test_session_mismatch_is_rejected(self) -> None:
        with patch(
            "flowfoundry.orchestration.execution._process_identity",
            return_value=self.live_identity(session_id=5252),
        ):
            verification = _verify_process(self.identity_record())
        self.assertEqual(verification.state, ProcessIdentityState.MISMATCH)
        self.assertEqual(verification.reason, "session_mismatch")

    def test_command_change_cannot_override_start_ticks_mismatch(self) -> None:
        with patch(
            "flowfoundry.orchestration.execution._process_identity",
            return_value=self.live_identity(
                process_start_ticks=202,
                command_fingerprint="still-looks-like-provider",
            ),
        ):
            verification = _verify_process(self.identity_record())
        self.assertEqual(verification.state, ProcessIdentityState.MISMATCH)
        self.assertEqual(verification.reason, "start_ticks_mismatch")

    def test_gone_process_is_distinct_from_unverified(self) -> None:
        with (
            patch(
                "flowfoundry.orchestration.execution._process_identity",
                return_value={"verified": False},
            ),
            patch(
                "flowfoundry.orchestration.execution.os.kill",
                side_effect=ProcessLookupError,
            ),
        ):
            verification = _verify_process(self.identity_record())
        self.assertEqual(verification.state, ProcessIdentityState.GONE)
        self.assertEqual(verification.reason, "process_gone")

    def test_partial_proc_failure_remains_fail_closed(self) -> None:
        with (
            patch(
                "flowfoundry.orchestration.execution._process_identity",
                return_value={"verified": False},
            ),
            patch("flowfoundry.orchestration.execution.os.kill", return_value=None),
        ):
            verification = _verify_process(self.identity_record())
        self.assertEqual(verification.state, ProcessIdentityState.UNVERIFIED)
        self.assertEqual(verification.reason, "insufficient_proc_evidence")
        self.assertFalse(verification.signal_allowed)

    def test_execution_metadata_path_mismatch_is_rejected(self) -> None:
        record = self.identity_record(execution_id="different-execution")
        execution_path = self.temp_path / "executions" / "execution-1" / "execution.json"
        verification = _verify_process(record, execution_path)
        self.assertEqual(verification.state, ProcessIdentityState.MISMATCH)
        self.assertEqual(verification.reason, "execution_metadata_mismatch")

    def test_unknown_command_fingerprint_version_is_unverified(self) -> None:
        record = self.identity_record(command_fingerprint_version=999)
        with patch(
            "flowfoundry.orchestration.execution._process_identity",
            return_value=self.live_identity(),
        ):
            verification = _verify_process(record)
        self.assertEqual(verification.state, ProcessIdentityState.UNVERIFIED)
        self.assertEqual(
            verification.reason,
            "unsupported_command_fingerprint_version",
        )
        self.assertFalse(verification.signal_allowed)

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
        with patch("flowfoundry.orchestration.execution.os.killpg") as kill_group:
            manifest = MeetingRuntime(
                TaskRouter(registry),
                LocalCommandProvider(enabled=True),
            ).cancel(workspace, grace_period_seconds=0.1)
        kill_group.assert_not_called()
        self.assertEqual(manifest["meeting"]["state"], "cancel_unverified")
        self.assertEqual(
            manifest["meeting"]["cancellation"]["executions"][0]["action"],
            "refused_unverified",
        )
        self.assertEqual(
            manifest["meeting"]["cancellation"]["executions"][0][
                "identity_verification"
            ],
            "mismatch",
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

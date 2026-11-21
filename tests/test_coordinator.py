from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flowfoundry.cli import build_parser, main
from flowfoundry.coordinator import (
    TaskStatus,
    approve_task,
    create_task,
    load_task,
    reconcile_task,
    result_for_task,
    save_task,
    worker_main,
)


class CoordinatorTests(unittest.TestCase):
    def test_session_permission_ceiling_and_effective_worker_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for level in (1, 2, 3, 4):
                task = create_task(root, "Fix the README", start=False, permission_level=level)
                self.assertEqual(task.session_permission_ceiling, level)
                self.assertLessEqual(task.effective_permission, level)
                self.assertEqual(task.effective_permission, min(level, 3))
                self.assertEqual(task.read_only, level == 1)

    def test_worker_passes_effective_permission_to_executor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = create_task(root, "Fix the README", start=False, permission_level=4)
            with patch("flowfoundry.goal_runner.run_goal", return_value=(0, {
                "run_id": "test-run", "status": "PASS",
            })) as run:
                worker_main(root, task.task_id)
            self.assertEqual(run.call_args.kwargs["permission_level"], 3)

    def test_read_only_ceiling_forces_read_only_executor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = create_task(root, "Fix the README", start=False, permission_level=1)
            with patch("flowfoundry.goal_runner.run_goal", return_value=(0, {
                "run_id": "test-run", "status": "PASS",
            })) as run:
                worker_main(root, task.task_id)
            self.assertTrue(run.call_args.kwargs["read_only"])

    def test_background_read_only_survives_cli_persistence_and_worker(self) -> None:
        for read_only in (False, True):
            with self.subTest(read_only=read_only), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                argv = ["do", "Check the README", "--background", "--workspace", str(root)]
                if read_only:
                    argv.append("--read-only")
                fake_process = type("Process", (), {"pid": 4321})()
                with patch("flowfoundry.coordinator.subprocess.Popen", return_value=fake_process):
                    self.assertEqual(main(argv), 0)
                path, = (root / ".flowfoundry/coordinator/tasks").glob("*.json")
                saved = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(saved["read_only"], read_only)
                with patch("flowfoundry.goal_runner.run_goal", return_value=(0, {
                    "run_id": "test-run", "status": "PASS",
                })) as run:
                    self.assertEqual(worker_main(root, saved["task_id"]), 0)
                self.assertEqual(
                    run.call_args.kwargs["read_only"],
                    read_only or saved["effective_permission"] <= 1,
                )

    def test_legacy_task_without_read_only_keeps_writable_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = create_task(root, "Check the README", start=False)
            path = root / ".flowfoundry/coordinator/tasks" / f"{task.task_id}.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value.pop("read_only", None)
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertFalse(load_task(root, task.task_id).read_only)

    def test_worker_exception_preserves_human_cancellation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = create_task(root, "Check the README", start=False)

            def cancel_then_raise(*args, **kwargs):
                from flowfoundry.coordinator import cancel_task

                cancel_task(root, task.task_id)
                raise RuntimeError("executor stopped after cancellation")

            with patch("flowfoundry.goal_runner.run_goal", side_effect=cancel_then_raise):
                self.assertEqual(worker_main(root, task.task_id), 1)

            saved = load_task(root, task.task_id)
            self.assertEqual(saved.status, TaskStatus.CANCELLED.value)
            self.assertEqual(saved.error, "Cancelled by human.")
            self.assertIsNone(saved.result_ref)

    def test_worker_exception_without_cancellation_records_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = create_task(root, "Check the README", start=False)
            with patch("flowfoundry.goal_runner.run_goal", side_effect=RuntimeError("executor failed")):
                self.assertEqual(worker_main(root, task.task_id), 1)
            saved = load_task(root, task.task_id)
            self.assertEqual(saved.status, TaskStatus.FAILED.value)
            self.assertEqual(saved.error, "RuntimeError: executor failed")

    def test_task_contract_is_durable_and_context_is_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".ai").mkdir()
            (root / ".ai" / "PROJECT_STATE.md").write_text("state", encoding="utf-8")
            task = create_task(root, "Check the README", start=False)
            loaded = load_task(root, task.task_id)
            self.assertEqual(loaded.status, TaskStatus.QUEUED.value)
            self.assertEqual(loaded.worker_capability, "general")
            self.assertIn(".ai/PROJECT_STATE.md", loaded.context_refs)
            self.assertEqual(loaded.dependencies, ())
            self.assertTrue(loaded.acceptance_criteria)

    def test_high_impact_task_waits_for_human_without_spawning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("flowfoundry.coordinator._spawn") as spawn:
                task = create_task(root, "Publish this release", start=True)
            spawn.assert_not_called()
            self.assertEqual(task.status, TaskStatus.WAITING_HUMAN.value)
            self.assertIn("publish", task.error or "")
            with patch("flowfoundry.coordinator._spawn", side_effect=lambda _, value: value):
                approved = approve_task(root, task.task_id)
            self.assertEqual(approved.status, TaskStatus.QUEUED.value)

    def test_lost_worker_becomes_failed_not_fake_running(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = create_task(root, "Check the README", start=False)
            task.status = TaskStatus.RUNNING.value
            task.pid = 321987
            save_task(root, task)
            with patch("flowfoundry.coordinator.os.kill", side_effect=ProcessLookupError):
                reconciled = reconcile_task(root, task)
            self.assertEqual(reconciled.status, TaskStatus.PROCESS_LOST.value)
            self.assertIn("PROCESS_LOST", reconciled.error or "")

    def test_verifying_without_result_becomes_process_lost(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = create_task(root, "Check the README", start=False)
            task.status = TaskStatus.VERIFYING.value
            task.phase = TaskStatus.VERIFYING.value
            task.pid = 321987
            save_task(root, task)
            with patch("flowfoundry.coordinator.os.kill", side_effect=ProcessLookupError):
                reconciled = reconcile_task(root, task)
            self.assertEqual(reconciled.status, TaskStatus.PROCESS_LOST.value)
            self.assertIsNone(reconciled.result_ref)

    def test_live_invalid_verifying_is_recovered_to_running(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = create_task(root, "Check the README", start=False)
            task.status = TaskStatus.VERIFYING.value
            task.pid = 321987
            save_task(root, task)
            with patch("flowfoundry.coordinator._pid_alive", return_value=True):
                reconciled = reconcile_task(root, task)
            self.assertEqual(reconciled.status, TaskStatus.RUNNING.value)

    def test_timeout_requires_budget_and_marks_task_timed_out(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = create_task(root, "Check the README", start=False)
            task.status = TaskStatus.RUNNING.value
            task.pid = 1234
            task.started_at = "2020-01-01T00:00:00+00:00"
            task.timeout_seconds = 1
            save_task(root, task)
            with patch("flowfoundry.coordinator._pid_alive", return_value=True), patch("flowfoundry.coordinator.os.killpg") as kill:
                reconciled = reconcile_task(root, task)
            kill.assert_called_once()
            self.assertEqual(reconciled.status, TaskStatus.TIMED_OUT.value)

    def test_cancel_stops_only_one_reversible_worker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = create_task(root, "Check the README", start=False)
            task.status = TaskStatus.RUNNING.value
            task.pid = 1234
            save_task(root, task)
            with patch("flowfoundry.coordinator._pid_alive", return_value=True), patch(
                "flowfoundry.coordinator.os.killpg"
            ) as kill:
                from flowfoundry.coordinator import cancel_task

                cancelled = cancel_task(root, task.task_id)
            kill.assert_called_once()
            self.assertEqual(cancelled.status, TaskStatus.CANCELLED.value)

    def test_result_requires_worker_artifact_and_stays_project_local(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = create_task(root, "Check the README", start=False)
            task.result_ref = ".flowfoundry/do/result.json"
            save_task(root, task)
            result_path = root / task.result_ref
            result_path.parent.mkdir(parents=True)
            result_path.write_text(json.dumps({"status": "PASS", "result": "ok"}), encoding="utf-8")
            self.assertEqual(result_for_task(root, task.task_id)["status"], "PASS")

    def test_background_result_restores_substantive_agent_response(self) -> None:
        response = "Codex inspected the code, changed reporting.py, and ran the full test suite."
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = create_task(root, "Fix reporting", start=False)
            task.result_ref = ".flowfoundry/do/goal-result/result.json"
            save_task(root, task)
            result_path = root / task.result_ref
            result_path.parent.mkdir(parents=True)
            result_path.write_text(
                json.dumps(
                    {
                        "run_id": "goal-result",
                        "status": "UNKNOWN",
                        "responsible_agent": "Codex",
                        "agent_response": response,
                        "verification": {"status": "UNKNOWN", "evidence": []},
                    }
                ),
                encoding="utf-8",
            )

            restored = result_for_task(root, task.task_id)

        self.assertEqual(restored["agent_response"], response)
        self.assertEqual(restored["verification"]["status"], "UNKNOWN")

    def test_default_help_hides_internal_worker_and_exposes_small_surface(self) -> None:
        help_text = build_parser().format_help()
        self.assertIn("status", help_text)
        self.assertIn("approve", help_text)
        self.assertNotIn("_coordinator-worker", help_text)

    def test_background_cli_returns_before_worker_finishes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_process = type("Process", (), {"pid": 4321})()
            with patch("flowfoundry.coordinator.subprocess.Popen", return_value=fake_process):
                code = main(["do", "Check the README", "--background", "--workspace", str(root)])
            self.assertEqual(code, 0)
            tasks = list((root / ".flowfoundry" / "coordinator" / "tasks").glob("*.json"))
            self.assertEqual(len(tasks), 1)
            saved = json.loads(tasks[0].read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], TaskStatus.RUNNING.value)
            self.assertEqual(saved["pid"], 4321)


if __name__ == "__main__":
    unittest.main()

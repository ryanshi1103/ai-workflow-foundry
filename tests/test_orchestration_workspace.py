from __future__ import annotations

import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flowfoundry.orchestration.approvals import ApprovalGate
from flowfoundry.orchestration.mailbox import Mailbox
from flowfoundry.orchestration.models import RiskLevel, TaskPlan, TaskSpec
from flowfoundry.orchestration.planner import RuleBasedPlanner
from flowfoundry.orchestration.workspace import RunWorkspace, atomic_write_json


class RunWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "runs"
        self.plan = RuleBasedPlanner().plan("Build safely", execution_mode="multi_agent")
        self.workspace = RunWorkspace.create(self.root, "run-001", self.plan)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_layout_schema_and_private_permissions(self) -> None:
        manifest = self.workspace.manifest()
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(set(manifest["tasks"]), {"build", "review", "test"})
        self.assertEqual(Path(manifest["project_root"]), Path.cwd())
        self.assertEqual(self.workspace.project_root, Path.cwd())
        self.assertEqual(os.stat(self.workspace.path).st_mode & 0o777, 0o700)
        self.assertEqual(os.stat(self.workspace.path / "manifest.json").st_mode & 0o777, 0o600)

    def test_run_and_task_path_escape_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RunWorkspace(self.root, "../outside")
        with self.assertRaises(ValueError):
            self.workspace.task_dir("../outside")
        with self.assertRaises(ValueError):
            self.workspace.contained("tasks", "..", "..", "outside")

    def test_atomic_json_redacts_secret_values(self) -> None:
        path = self.workspace.contained("artifacts", "safe.json")
        value = "sk-" + "a" * 30
        atomic_write_json(path, {"message": f"key={value}"})
        content = path.read_text(encoding="utf-8")
        self.assertNotIn(value, content)
        self.assertIn("REDACTED", content)

    def test_existing_run_is_not_overwritten(self) -> None:
        with self.assertRaises(FileExistsError):
            RunWorkspace.create(self.root, "run-001", self.plan)

    def test_open_recovers_persisted_plan(self) -> None:
        opened = RunWorkspace.open(self.root, "run-001")
        self.assertEqual(opened.plan(), self.plan)


class MailboxConcurrencyTests(unittest.TestCase):
    def test_parallel_writers_produce_unique_atomic_messages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = RunWorkspace.create(
                Path(temp_dir) / "runs",
                "parallel",
                RuleBasedPlanner().plan("Parallel mailbox"),
            )
            mailbox = Mailbox(workspace)

            def send(index: int) -> None:
                mailbox.send(
                    sender=f"agent-{index}",
                    recipient="aggregator",
                    task_id="build",
                    kind="result",
                    payload={"index": index},
                )

            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(send, range(40)))
            messages = mailbox.list(recipient="aggregator")
            self.assertEqual(len(messages), 40)
            self.assertEqual({message["sequence"] for message in messages}, set(range(1, 41)))
            for path in workspace.contained("messages").glob("*.json"):
                json.loads(path.read_text(encoding="utf-8"))


class ApprovalGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        plan = TaskPlan(
            "Release",
            (
                TaskSpec(
                    id="release",
                    title="Release",
                    role="builder",
                    required_capabilities=("implementation",),
                    risk_level=RiskLevel.HIGH,
                    approval_requirements=("release",),
                ),
            ),
        )
        self.task = plan.tasks[0]
        self.workspace = RunWorkspace.create(Path(self.temp_dir.name), "approval", plan)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_overnight_gate_records_pending_human_action(self) -> None:
        decision = ApprovalGate().evaluate(self.workspace, self.task)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.pending_actions, ("release",))
        self.assertIn("release", self.workspace.contained("HUMAN_ACTIONS_REQUIRED.md").read_text())

    def test_recorded_approval_is_honored(self) -> None:
        gate = ApprovalGate()
        gate.record_approval(self.workspace, "release", ("release",), "operator")
        self.assertTrue(gate.evaluate(self.workspace, self.task).allowed)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from flowfoundry.orchestration.aggregator import ResultAggregator
from flowfoundry.orchestration.models import (
    ReviewDecision,
    RiskLevel,
    TaskPlan,
    TaskSpec,
    TaskStatus,
)
from flowfoundry.orchestration.planner import RuleBasedPlanner
from flowfoundry.orchestration.providers import FakeProvider
from flowfoundry.orchestration.recovery import RecoveryManager
from flowfoundry.orchestration.registry import default_registry
from flowfoundry.orchestration.router import TaskRouter
from flowfoundry.orchestration.scheduler import RunScheduler
from flowfoundry.orchestration.workspace import RunWorkspace


class SchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "runs"
        self.plan = RuleBasedPlanner().plan("Offline collaboration")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_plan(self, provider: FakeProvider, plan: TaskPlan | None = None) -> RunWorkspace:
        active_plan = plan or self.plan
        workspace = RunWorkspace.create(self.root, "test-run", active_plan)
        scheduler = RunScheduler(
            TaskRouter(default_registry().synthetic()),
            provider,
            max_workers=3,
        )
        scheduler.run(workspace)
        return workspace

    def test_synthetic_builder_reviewer_tester_end_to_end(self) -> None:
        workspace = self.run_plan(FakeProvider())
        manifest = workspace.manifest()
        self.assertEqual(manifest["status"], "completed")
        self.assertTrue(
            all(state["status"] == TaskStatus.COMPLETED.value for state in manifest["tasks"].values())
        )
        report = ResultAggregator().aggregate(workspace)
        self.assertEqual(report["completed_tasks"], ["build", "review", "test"])
        self.assertFalse(report["human_actions_required"])

    def test_retry_succeeds_within_limit(self) -> None:
        provider = FakeProvider(failures_before_success={"build": 1})
        workspace = self.run_plan(provider)
        self.assertEqual(provider.calls["build"], 2)
        self.assertEqual(workspace.manifest()["tasks"]["build"]["status"], "completed")

    def test_blocked_review_blocks_source_and_skips_test(self) -> None:
        provider = FakeProvider(reviews={"review": ReviewDecision.BLOCKED})
        workspace = self.run_plan(provider)
        states = workspace.manifest()["tasks"]
        self.assertEqual(states["build"]["status"], TaskStatus.BLOCKED.value)
        self.assertEqual(states["review"]["status"], TaskStatus.BLOCKED.value)
        self.assertEqual(states["test"]["status"], TaskStatus.SKIPPED.value)
        review = workspace.read_json("reviews/review.json")
        self.assertEqual(review["decision"], "BLOCKED")
        self.assertIn("commit", review)
        self.assertIn("tests", review)

    def test_review_pending_stops_dependent_test(self) -> None:
        provider = FakeProvider(reviews={"review": ReviewDecision.REVIEW_PENDING})
        workspace = self.run_plan(provider)
        manifest = workspace.manifest()
        self.assertEqual(manifest["status"], "review_pending")
        self.assertEqual(manifest["tasks"]["test"]["status"], TaskStatus.PENDING.value)

    def test_approved_with_notes_allows_validation(self) -> None:
        provider = FakeProvider(reviews={"review": ReviewDecision.APPROVED_WITH_NOTES})
        workspace = self.run_plan(provider)
        self.assertEqual(workspace.manifest()["status"], "completed")

    def test_high_risk_task_is_skipped_without_waiting(self) -> None:
        plan = TaskPlan(
            "Deploy",
            (
                TaskSpec(
                    id="deploy",
                    title="Deploy",
                    role="builder",
                    required_capabilities=("implementation",),
                    risk_level=RiskLevel.HIGH,
                    approval_requirements=("deployment",),
                ),
            ),
        )
        workspace = self.run_plan(FakeProvider(), plan)
        self.assertEqual(
            workspace.manifest()["tasks"]["deploy"]["status"],
            TaskStatus.SKIPPED_PENDING_HUMAN.value,
        )
        self.assertTrue(workspace.contained("HUMAN_ACTIONS_REQUIRED.md").exists())


class RecoveryTests(unittest.TestCase):
    def test_resume_resets_interrupted_but_not_completed_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = RuleBasedPlanner().plan("Recover")
            workspace = RunWorkspace.create(Path(temp_dir), "recover", plan)
            workspace.update_task("build", status=TaskStatus.COMPLETED.value)
            workspace.update_task("review", status=TaskStatus.RUNNING.value)
            RecoveryManager().recover_interrupted(workspace)
            states = workspace.manifest()["tasks"]
            self.assertEqual(states["build"]["status"], TaskStatus.COMPLETED.value)
            self.assertEqual(states["review"]["status"], TaskStatus.PENDING.value)

    def test_reconcile_does_not_repeat_unchanged_completed_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            planner = RuleBasedPlanner()
            plan = planner.plan("Stable")
            workspace = RunWorkspace.create(Path(temp_dir), "stable", plan)
            workspace.update_task("build", status=TaskStatus.COMPLETED.value)
            RecoveryManager().reconcile_plan(workspace, plan)
            self.assertEqual(
                workspace.manifest()["tasks"]["build"]["status"],
                TaskStatus.COMPLETED.value,
            )

    def test_changed_input_resets_task_and_dependents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            planner = RuleBasedPlanner()
            original = planner.plan("Original")
            workspace = RunWorkspace.create(Path(temp_dir), "changed", original)
            for task in original.tasks:
                workspace.update_task(task.id, status=TaskStatus.COMPLETED.value)
            changed_build = replace(original.tasks[0], inputs={"goal": "Changed"})
            changed = TaskPlan("Changed", (changed_build, *original.tasks[1:]))
            RecoveryManager().reconcile_plan(workspace, changed)
            states = workspace.manifest()["tasks"]
            self.assertTrue(all(state["status"] == "pending" for state in states.values()))


if __name__ == "__main__":
    unittest.main()

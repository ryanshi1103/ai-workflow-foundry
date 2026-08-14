from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from flowfoundry.cli import main
from flowfoundry.orchestration.models import TaskPlan, TaskSpec, TaskStatus
from flowfoundry.orchestration.reconciliation import (
    DurableRunReconciler,
    ReconciliationState,
)
from flowfoundry.orchestration.recovery import RecoveryManager
from flowfoundry.orchestration.workspace import RunWorkspace, atomic_write_json


class DurableRunReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "runs"
        plan = TaskPlan(
            "reconcile durable state",
            (
                TaskSpec(
                    id="build",
                    title="Build",
                    role="builder",
                    required_capabilities=("implementation",),
                ),
            ),
        )
        self.workspace = RunWorkspace.create(self.root, "stale-run", plan)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_candidate(self, *, success: bool = True, validated: bool = True) -> None:
        atomic_write_json(
            self.workspace.contained("artifacts/candidates/candidate.json"),
            {
                "provider_result": {"success": success},
                "validation": {
                    "success": validated,
                    "candidate_commit": "candidate-commit" if validated else None,
                },
            },
        )

    def write_worktree(
        self,
        *,
        status: str = "retained",
        writer_outcome: str | None = None,
        validated: bool | None = None,
        candidate: bool = False,
    ) -> None:
        record: dict[str, object] = {
            "worktree_id": "wt-test",
            "status": status,
            "active_writer": None,
            "retained_after_run": status == "retained",
            "last_writer_outcome": writer_outcome,
        }
        if validated is not None:
            record["validation"] = {"success": validated}
        if candidate:
            record["cleanup_decision"] = "retained_unintegrated_commits"
        atomic_write_json(self.workspace.contained("worktrees/wt-test.json"), record)

    def reconcile_with(self, statuses: list[dict[str, object]]):
        return DurableRunReconciler(lambda _: statuses).reconcile(self.workspace)

    def test_verified_active_process_remains_running(self) -> None:
        result = self.reconcile_with(
            [{"state": "running", "liveness": "verified", "task_id": "build"}]
        )
        self.assertEqual(result.reconciled_state, ReconciliationState.STILL_RUNNING.value)
        self.assertTrue(result.active_process)
        self.assertFalse(result.resume_execution)

    def test_successful_validated_candidate_awaits_integration(self) -> None:
        self.workspace.write_task_result(
            "build", {"success": True, "termination": {"status": "completed"}}
        )
        self.write_candidate()
        self.write_worktree(status="retained", candidate=True)
        result = self.reconcile_with([])
        self.assertEqual(
            result.reconciled_state,
            ReconciliationState.COMPLETED_AWAITING_INTEGRATION.value,
        )
        self.assertTrue(result.human_action_required)

    def test_failed_receipt_with_retained_worktree_is_failed_retained(self) -> None:
        self.write_worktree(status="retained", writer_outcome="failed")
        result = self.reconcile_with([])
        self.assertEqual(result.reconciled_state, ReconciliationState.FAILED_RETAINED.value)

    def test_cancellation_receipt_with_retained_worktree_is_cancelled_retained(self) -> None:
        self.workspace.write_task_result("build", {"cancelled": True})
        self.write_worktree(status="retained")
        result = self.reconcile_with([])
        self.assertEqual(
            result.reconciled_state,
            ReconciliationState.CANCELLED_RETAINED.value,
        )

    def test_missing_process_without_terminal_receipt_blocks(self) -> None:
        self.workspace.update_task("build", status=TaskStatus.RUNNING.value)
        result = self.reconcile_with([])
        self.assertEqual(
            result.reconciled_state,
            ReconciliationState.RECONCILIATION_BLOCKED.value,
        )
        self.assertNotIn("success", result.reason)

    def test_conflicting_terminal_receipts_block(self) -> None:
        result = self.reconcile_with(
            [
                {"state": "completed", "liveness": "terminal"},
                {"state": "failed", "liveness": "terminal"},
            ]
        )
        self.assertEqual(
            result.reconciled_state,
            ReconciliationState.RECONCILIATION_BLOCKED.value,
        )
        self.assertEqual(result.reason, "terminal_receipts_conflict")

    def test_double_apply_is_idempotent(self) -> None:
        self.workspace.write_task_result("build", {"success": True})
        reconciler = DurableRunReconciler(lambda _: [])
        first = reconciler.reconcile(self.workspace, apply=True)
        after_first = self.workspace.contained("manifest.json").read_bytes()
        second = reconciler.reconcile(self.workspace, apply=True)
        after_second = self.workspace.contained("manifest.json").read_bytes()
        self.assertTrue(first.mutation_performed)
        self.assertFalse(second.mutation_performed)
        self.assertEqual(after_first, after_second)

    def test_status_exposes_effective_state_not_stale_running(self) -> None:
        self.workspace.write_task_result("build", {"success": True})
        output = io.StringIO()
        error = io.StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            result = main(
                [
                    "team",
                    "status",
                    "stale-run",
                    "--runs-root",
                    str(self.root),
                ]
            )
        status = json.loads(output.getvalue())
        self.assertEqual((result, error.getvalue()), (0, ""))
        self.assertEqual(status["observed_status"], "running")
        self.assertEqual(status["status"], "completed")

    def test_resume_does_not_restart_terminal_reconciled_execution(self) -> None:
        self.workspace.write_task_result("build", {"success": True})
        self.workspace.update_task("build", status=TaskStatus.RUNNING.value)
        recovered = RecoveryManager().recover_interrupted(self.workspace)
        self.assertFalse(recovered["recovery_decision"]["resume_execution"])
        self.assertEqual(
            recovered["tasks"]["build"]["status"], TaskStatus.RUNNING.value
        )
        self.assertEqual(recovered["status"], ReconciliationState.COMPLETED.value)

    def test_retained_worktree_alone_does_not_imply_success_or_failure(self) -> None:
        self.write_worktree(status="retained")
        result = self.reconcile_with([])
        self.assertEqual(
            result.reconciled_state,
            ReconciliationState.RECONCILIATION_BLOCKED.value,
        )


if __name__ == "__main__":
    unittest.main()

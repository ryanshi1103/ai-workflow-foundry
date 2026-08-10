from __future__ import annotations

import subprocess
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from flowfoundry.cli import main
from flowfoundry.orchestration.aggregator import ResultAggregator
from flowfoundry.orchestration.isolation import (
    WorktreeError,
    WorktreeManager,
    sanitize_component,
)
from flowfoundry.orchestration.meeting import MeetingRuntime
from flowfoundry.orchestration.models import (
    AgentSpec,
    IsolationMode,
    ProviderResult,
    ReviewDecision,
    TaskPlan,
    TaskSpec,
    TaskStatus,
    WorktreeStatus,
)
from flowfoundry.orchestration.planner import RuleBasedPlanner
from flowfoundry.orchestration.providers import FakeProvider, LocalCommandProvider
from flowfoundry.orchestration.recovery import RecoveryManager
from flowfoundry.orchestration.registry import AgentRegistry, default_registry
from flowfoundry.orchestration.router import TaskRouter
from flowfoundry.orchestration.scheduler import RunScheduler
from flowfoundry.orchestration.workspace import RunWorkspace


def git(path: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(path), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


class GitFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.project = root / "project"
        self.runs = root / "state" / "runs"
        self.managed = root / "managed"
        self.project.mkdir()
        git(self.project, "init", "-q")
        git(self.project, "config", "user.name", "FlowFoundry Test")
        git(self.project, "config", "user.email", "flowfoundry@example.invalid")
        (self.project / "base.txt").write_text("original\n", encoding="utf-8")
        git(self.project, "add", "base.txt")
        git(self.project, "commit", "-qm", "base")
        self.base = git(self.project, "rev-parse", "HEAD")

    def workspace(self, run_id: str = "isolation") -> RunWorkspace:
        task = TaskSpec(
            id="write",
            title="Write",
            role="builder",
            required_capabilities=("implementation",),
            required_permissions=("read_workspace", "write_workspace"),
        )
        return RunWorkspace.create(
            self.runs,
            run_id,
            TaskPlan("write safely", (task,)),
            project_root=self.project,
        )

    def manager(self, run_id: str = "isolation") -> WorktreeManager:
        return WorktreeManager(self.workspace(run_id), managed_root=self.managed)


class WorktreeIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.fixture = GitFixture(self.root)
        self.workspace = self.fixture.workspace()
        self.manager = WorktreeManager(self.workspace)
        self.fixture.managed = self.manager.managed_root

    def tearDown(self) -> None:
        for record in self.manager.records():
            path = Path(record["path"])
            if path.exists() and not self.manager.is_dirty(record):
                if record["status"] not in {
                    WorktreeStatus.COMPLETED.value,
                    WorktreeStatus.RETAINED.value,
                    WorktreeStatus.FAILED.value,
                }:
                    record["status"] = WorktreeStatus.COMPLETED.value
                    self.manager._write_record(record)
                self.manager.cleanup(record["worktree_id"])
        self.temp.cleanup()

    def allocate(self, task: str, participant: str, attempt: int = 1) -> dict[str, object]:
        return self.manager.allocate(
            task_id=task,
            participant_id=participant,
            attempt_id=attempt,
            base_commit=self.fixture.base,
        )

    def test_vertical_slice_candidate_diff_validation_and_main_integrity(self) -> None:
        record = self.allocate("build", "writer-a")
        self.manager.acquire_writer(record["worktree_id"], participant_id="writer-a", attempt_id=1)
        candidate = Path(record["path"])
        (candidate / "base.txt").write_text("A\n", encoding="utf-8")
        self.manager.release_writer(
            record["worktree_id"],
            participant_id="writer-a",
            attempt_id=1,
            outcome="success",
        )
        self.manager.begin_validation(record["worktree_id"])
        validation = {
            "success": (candidate / "base.txt").read_text(encoding="utf-8") == "A\n",
            "cwd": str(candidate),
        }
        self.manager.finish_validation(record["worktree_id"], validation)
        result = self.manager.candidate_result(
            record["worktree_id"],
            provider_result={"success": True},
            validation=validation,
        )

        self.assertEqual((self.fixture.project / "base.txt").read_text(), "original\n")
        self.assertEqual(result.base_commit, self.fixture.base)
        self.assertEqual(result.changed_files, ("base.txt",))
        self.assertEqual(result.validation["cwd"], str(candidate))
        self.assertIn("base.txt", result.diff_summary)
        self.assertTrue(self.workspace.contained(result.diff_artifact_ref).is_file())

    def test_parallel_writers_can_change_same_file_without_collision(self) -> None:
        records = [self.allocate("solution-a", "writer-a"), self.allocate("solution-b", "writer-b")]

        def write(record: dict[str, object], value: str) -> str:
            participant = str(record["participant_id"])
            worktree_id = str(record["worktree_id"])
            self.manager.acquire_writer(worktree_id, participant_id=participant, attempt_id=1)
            (Path(str(record["path"])) / "base.txt").write_text(value + "\n", encoding="utf-8")
            self.manager.release_writer(
                worktree_id,
                participant_id=participant,
                attempt_id=1,
                outcome="success",
            )
            return value

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(write, record, value) for record, value in zip(records, ("A", "B"))]
            self.assertEqual([future.result() for future in futures], ["A", "B"])

        self.assertEqual((Path(str(records[0]["path"])) / "base.txt").read_text(), "A\n")
        self.assertEqual((Path(str(records[1]["path"])) / "base.txt").read_text(), "B\n")
        self.assertEqual((self.fixture.project / "base.txt").read_text(), "original\n")

    def test_dirty_main_is_not_copied_changed_or_cleaned(self) -> None:
        (self.fixture.project / "base.txt").write_text("user tracked\n", encoding="utf-8")
        (self.fixture.project / "user-untracked.txt").write_text("private local\n", encoding="utf-8")
        before = git(self.fixture.project, "status", "--porcelain=v1", "--untracked-files=all")
        record = self.allocate("dirty-safe", "writer")
        candidate = Path(str(record["path"]))

        self.assertEqual((candidate / "base.txt").read_text(), "original\n")
        self.assertFalse((candidate / "user-untracked.txt").exists())
        self.assertEqual(
            git(self.fixture.project, "status", "--porcelain=v1", "--untracked-files=all"),
            before,
        )
        record["status"] = WorktreeStatus.COMPLETED.value
        self.manager._write_record(record)
        self.manager.cleanup(record["worktree_id"])
        self.assertEqual((self.fixture.project / "base.txt").read_text(), "user tracked\n")
        self.assertEqual((self.fixture.project / "user-untracked.txt").read_text(), "private local\n")

    def test_explicit_dirty_dependency_requires_future_snapshot(self) -> None:
        with self.assertRaises(WorktreeError) as raised:
            self.manager.allocate(
                task_id="dirty",
                participant_id="writer",
                attempt_id=1,
                dirty_base_required=True,
            )
        self.assertEqual(raised.exception.code, "DIRTY_BASE_REQUIRES_SNAPSHOT")
        self.assertEqual(self.manager.records(), [])

    def test_writer_lease_is_exclusive_and_illegal_transition_is_rejected(self) -> None:
        record = self.allocate("lease", "writer-a")
        self.manager.acquire_writer(record["worktree_id"], participant_id="writer-a", attempt_id=1)
        with self.assertRaises(WorktreeError) as held:
            self.manager.acquire_writer(record["worktree_id"], participant_id="writer-b", attempt_id=1)
        self.assertEqual(held.exception.code, "WRITER_LEASE_HELD")
        with self.assertRaises(WorktreeError):
            self.manager.begin_validation(record["worktree_id"])
        self.manager.release_writer(
            record["worktree_id"], participant_id="writer-a", attempt_id=1, outcome="success"
        )

    def test_isolation_policy_uses_permissions_and_meeting_execution_mode(self) -> None:
        self.assertEqual(
            WorktreeManager.isolation_mode(
                required_permissions=(),
                agent_permissions=(),
                provider_requires_isolation=True,
            ),
            IsolationMode.NONE,
        )
        self.assertEqual(
            WorktreeManager.isolation_mode(
                required_permissions=("read_workspace",),
                agent_permissions=("read_workspace",),
                provider_requires_isolation=True,
            ),
            IsolationMode.READ_ONLY,
        )
        self.assertEqual(
            WorktreeManager.isolation_mode(
                required_permissions=("read_workspace", "write_workspace"),
                agent_permissions=("read_workspace", "write_workspace"),
                provider_requires_isolation=True,
            ),
            IsolationMode.MANAGED_WORKTREE,
        )
        self.assertEqual(
            WorktreeManager.isolation_mode(
                required_permissions=("read_workspace", "write_workspace"),
                agent_permissions=("read_workspace", "write_workspace"),
                provider_requires_isolation=True,
                meeting=True,
            ),
            IsolationMode.READ_ONLY,
        )

    def test_path_safety_and_allocation_idempotency(self) -> None:
        values = ("../../escape", "run / with spaces", "参与者/../x", "...", "a" * 500)
        for value in values:
            safe = sanitize_component(value)
            self.assertNotIn("/", safe)
            self.assertNotIn("..", safe)
            self.assertLessEqual(len(safe), 48)

        first = self.manager.allocate(
            task_id="../../task",
            participant_id="writer / ü",
            attempt_id=1,
            candidate_id="candidate / ../../outside",
        )
        second = self.manager.allocate(
            task_id="../../task",
            participant_id="writer / ü",
            attempt_id=99,
            candidate_id="candidate / ../../outside",
        )
        self.assertEqual(first["worktree_id"], second["worktree_id"])
        self.assertEqual(Path(first["path"]).resolve().parent.parent, self.fixture.managed)
        self.assertEqual(len(self.manager.records()), 1)

    def test_recovery_releases_stale_writer_without_duplicate(self) -> None:
        record = self.allocate("recover", "writer")
        self.manager.acquire_writer(record["worktree_id"], participant_id="writer", attempt_id=1)
        (Path(record["path"]) / "partial.txt").write_text("partial\n", encoding="utf-8")

        restarted = WorktreeManager(self.workspace, managed_root=self.fixture.managed)
        reconciled = restarted.reconcile(active_executions=())
        recovered = next(item for item in reconciled if item["worktree_id"] == record["worktree_id"])
        self.assertEqual(recovered["status"], WorktreeStatus.RETAINED.value)
        self.assertIsNone(recovered["active_writer"])
        self.assertEqual(len(restarted.reconcile(active_executions=())), 1)
        again = restarted.allocate(
            task_id="recover", participant_id="writer", attempt_id=2, base_commit=self.fixture.base
        )
        self.assertEqual(again["worktree_id"], record["worktree_id"])

    def test_recovery_finishes_crash_interrupted_allocation(self) -> None:
        record = self.allocate("allocating", "writer")
        record["status"] = WorktreeStatus.ALLOCATING.value
        self.manager._write_record(record)
        recovered = self.manager.reconcile()
        self.assertEqual(recovered[0]["status"], WorktreeStatus.READY.value)
        self.assertIn("allocation_recovered_at", recovered[0])

    def test_recovery_does_not_release_unverifiable_live_writer(self) -> None:
        record = self.allocate("uncertain", "writer")
        self.manager.acquire_writer(record["worktree_id"], participant_id="writer", attempt_id=1)
        recovered = self.manager.reconcile(
            active_executions=(
                {
                    "task_id": "uncertain",
                    "participant_id": "writer",
                    "state": "running",
                    "liveness": "unverified",
                },
            )
        )[0]
        self.assertEqual(recovered["status"], WorktreeStatus.ORPHANED.value)
        self.assertIsNotNone(recovered["active_writer"])
        recovered["active_writer"] = None
        recovered["status"] = WorktreeStatus.COMPLETED.value
        self.manager._write_record(recovered)

    def test_cleanup_removes_only_clean_owned_terminal_worktree(self) -> None:
        clean = self.allocate("clean", "writer")
        clean["status"] = WorktreeStatus.COMPLETED.value
        self.manager._write_record(clean)
        removed = self.manager.cleanup(clean["worktree_id"])
        self.assertEqual(removed["status"], WorktreeStatus.REMOVED.value)
        self.assertFalse(Path(clean["path"]).exists())
        self.assertEqual(
            self.manager.cleanup(clean["worktree_id"])["status"],
            WorktreeStatus.REMOVED.value,
        )

        dirty = self.allocate("dirty", "writer")
        (Path(dirty["path"]) / "dirty.txt").write_text("retain\n", encoding="utf-8")
        dirty["status"] = WorktreeStatus.FAILED.value
        self.manager._write_record(dirty)
        retained = self.manager.cleanup(dirty["worktree_id"])
        self.assertEqual(retained["status"], WorktreeStatus.RETAINED.value)
        self.assertTrue(Path(dirty["path"]).exists())

    def test_user_created_worktree_is_discovered_but_never_owned_or_cleaned(self) -> None:
        user_path = self.root / "user-worktree"
        git(self.fixture.project, "worktree", "add", "-q", "-b", "user/manual", str(user_path), "HEAD")
        try:
            discovered = {item.path for item in self.manager.discover()}
            self.assertIn(user_path.resolve(), discovered)
            self.assertEqual(self.manager.records(), [])
            with self.assertRaises(WorktreeError):
                self.manager.cleanup("wt-00000000000000000000")
            self.assertTrue(user_path.exists())
            self.assertIn(user_path.resolve(), {item.path for item in self.manager.discover()})
        finally:
            git(self.fixture.project, "worktree", "remove", str(user_path))
            git(self.fixture.project, "branch", "-d", "user/manual")

    def test_unrecorded_worktree_under_managed_root_is_reported_not_removed(self) -> None:
        orphan_path = self.fixture.managed / "unknown-run" / "unknown-candidate"
        orphan_path.parent.mkdir(parents=True)
        git(
            self.fixture.project,
            "worktree",
            "add",
            "-q",
            "-b",
            "user/inside-managed-root",
            str(orphan_path),
            "HEAD",
        )
        try:
            orphan = next(
                item
                for item in self.manager.status_records()
                if item.get("directory") == "unknown-candidate"
            )
            self.assertEqual(orphan["status"], WorktreeStatus.ORPHANED.value)
            self.assertTrue(orphan["retained_after_run"])
            self.assertTrue(orphan_path.exists())
        finally:
            git(self.fixture.project, "worktree", "remove", str(orphan_path))
            git(self.fixture.project, "branch", "-d", "user/inside-managed-root")

    def test_non_git_workspace_reports_unavailable(self) -> None:
        non_git = self.root / "plain"
        non_git.mkdir()
        workspace = RunWorkspace.create(
            self.root / "plain-state" / "runs",
            "plain",
            TaskPlan(
                "plain",
                (
                    TaskSpec(
                        id="write",
                        title="write",
                        role="builder",
                        required_capabilities=("implementation",),
                        required_permissions=("read_workspace", "write_workspace"),
                    ),
                ),
            ),
            project_root=non_git,
        )
        with self.assertRaises(WorktreeError) as raised:
            WorktreeManager(workspace)
        self.assertEqual(raised.exception.code, "WORKTREE_UNAVAILABLE")

    def test_recovery_manager_reconciles_durable_worktree_and_task_state(self) -> None:
        record = self.allocate("write", "writer")
        self.manager.acquire_writer(record["worktree_id"], participant_id="writer", attempt_id=1)
        (Path(record["path"]) / "partial.txt").write_text("partial\n", encoding="utf-8")
        self.workspace.update_task("write", status=TaskStatus.RUNNING.value)

        manifest = RecoveryManager().recover_interrupted(self.workspace)
        recovered = self.manager.record(record["worktree_id"])
        self.assertEqual(manifest["tasks"]["write"]["status"], TaskStatus.PENDING.value)
        self.assertEqual(recovered["status"], WorktreeStatus.RETAINED.value)
        self.assertIsNone(recovered["active_writer"])
        self.assertEqual(manifest["worktree_recovery"][0]["worktree_id"], record["worktree_id"])


class MutatingFixtureProvider:
    requires_managed_worktree = True

    def __init__(self, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.calls: list[tuple[str, Path]] = []

    def execute(
        self,
        task: TaskSpec,
        agent: AgentSpec,
        task_dir: Path,
        project_root: Path,
    ) -> ProviderResult:
        self.calls.append((task.id, project_root.resolve()))
        if task.id.startswith("build"):
            value = str(task.inputs.get("value", task.id))
            (project_root / "base.txt").write_text(value + "\n", encoding="utf-8")
            same = (project_root / "base.txt").read_text(encoding="utf-8") == value + "\n"
            if self.failures_before_success > 0:
                self.failures_before_success -= 1
                return ProviderResult(False, "transient fixture failure")
            return ProviderResult(same, f"wrote {value}")
        if task.id == "review":
            seen = (project_root / "base.txt").read_text(encoding="utf-8").strip()
            return ProviderResult(
                seen == "candidate",
                f"review saw {seen}",
                review=ReviewDecision.APPROVED,
            )
        if task.id == "test":
            seen = (project_root / "base.txt").read_text(encoding="utf-8").strip()
            return ProviderResult(seen == "candidate", f"test saw {seen}")
        return ProviderResult(True, "fixture no-op")


class SchedulerIsolationIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.fixture = GitFixture(self.root)
        common = {
            "display_name": "Fixture Agent",
            "provider": "fixture",
            "command_template": (),
            "cost_class": "free",
            "concurrency_limit": 2,
            "context_limit": 1000,
            "availability": True,
            "local": True,
        }
        self.registry = AgentRegistry(
            (
                AgentSpec(
                    id="fixture-writer",
                    role="builder",
                    capabilities=("implementation",),
                    permission_profile=("read_workspace", "write_workspace"),
                    workspace_mode="isolated_worktree",
                    **common,
                ),
                AgentSpec(
                    id="fixture-reviewer",
                    role="reviewer",
                    capabilities=("review",),
                    permission_profile=("read_workspace",),
                    workspace_mode="read_only",
                    **common,
                ),
                AgentSpec(
                    id="fixture-tester",
                    role="tester",
                    capabilities=("testing",),
                    permission_profile=("read_workspace", "write_workspace"),
                    workspace_mode="isolated_worktree",
                    **common,
                ),
            )
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def workspace(self, run_id: str, tasks: tuple[TaskSpec, ...]) -> RunWorkspace:
        return RunWorkspace.create(
            self.fixture.runs,
            run_id,
            TaskPlan("scheduler isolation", tasks),
            project_root=self.fixture.project,
        )

    @staticmethod
    def build_task(task_id: str, value: str, *, retry_limit: int = 0) -> TaskSpec:
        return TaskSpec(
            id=task_id,
            title=task_id,
            role="builder",
            required_capabilities=("implementation",),
            inputs={"value": value},
            required_permissions=("read_workspace", "write_workspace"),
            retry_limit=retry_limit,
        )

    def test_scheduler_parallel_writers_receive_distinct_candidate_cwds(self) -> None:
        tasks = (self.build_task("build-a", "A"), self.build_task("build-b", "B"))
        workspace = self.workspace("parallel-scheduler", tasks)
        provider = MutatingFixtureProvider()
        RunScheduler(TaskRouter(self.registry), provider, max_workers=2).run(workspace)

        states = workspace.manifest()["tasks"]
        self.assertNotEqual(states["build-a"]["worktree_id"], states["build-b"]["worktree_id"])
        paths = {task_id: path for task_id, path in provider.calls}
        self.assertEqual((paths["build-a"] / "base.txt").read_text(), "A\n")
        self.assertEqual((paths["build-b"] / "base.txt").read_text(), "B\n")
        self.assertEqual((self.fixture.project / "base.txt").read_text(), "original\n")
        self.assertTrue(states["build-a"]["candidate_result_ref"].endswith(".json"))

    def test_reviewer_and_validator_use_the_writer_candidate(self) -> None:
        tasks = (
            TaskSpec(
                id="build",
                title="build",
                role="builder",
                required_capabilities=("implementation",),
                inputs={"value": "candidate"},
                required_permissions=("read_workspace", "write_workspace"),
                retry_limit=0,
                review_required=True,
            ),
            TaskSpec(
                id="review",
                title="review",
                role="reviewer",
                required_capabilities=("review",),
                dependencies=("build",),
                inputs={"source_task": "build"},
            ),
            TaskSpec(
                id="test",
                title="test",
                role="tester",
                required_capabilities=("testing",),
                dependencies=("review",),
                inputs={"source_task": "build", "validation": True},
                required_permissions=("read_workspace", "write_workspace"),
                validation_commands=("fixture validation",),
            ),
        )
        workspace = self.workspace("handoff", tasks)
        provider = MutatingFixtureProvider()
        RunScheduler(TaskRouter(self.registry), provider, max_workers=2).run(workspace)

        calls = {task_id: path for task_id, path in provider.calls}
        self.assertEqual(calls["build"], calls["review"])
        self.assertEqual(calls["build"], calls["test"])
        self.assertNotEqual(calls["test"], self.fixture.project.resolve())
        states = workspace.manifest()["tasks"]
        self.assertEqual(states["build"]["worktree_id"], states["test"]["worktree_id"])
        self.assertTrue(states["test"]["validation"]["success"])
        candidate = workspace.read_json(states["test"]["candidate_result_ref"])
        self.assertEqual(candidate["provider_result"]["summary"], "wrote candidate")
        self.assertEqual(candidate["experience"]["writer_attempts"], 1)
        self.assertEqual((self.fixture.project / "base.txt").read_text(), "original\n")

    def test_transient_retry_reuses_candidate_with_new_execution_attempt(self) -> None:
        workspace = self.workspace(
            "retry-candidate",
            (self.build_task("build", "retry-success", retry_limit=1),),
        )
        provider = MutatingFixtureProvider(failures_before_success=1)
        RunScheduler(TaskRouter(self.registry), provider).run(workspace)

        state = workspace.manifest()["tasks"]["build"]
        self.assertEqual(state["attempts"], 2)
        self.assertEqual(len({path for _, path in provider.calls}), 1)
        manager = WorktreeManager(workspace)
        self.assertEqual(len(manager.records()), 1)
        record = manager.records()[0]
        self.assertIsNone(record["active_writer"])
        self.assertEqual(record["status"], WorktreeStatus.COMPLETED.value)
        self.assertEqual((self.fixture.project / "base.txt").read_text(), "original\n")

    def test_failed_dirty_writer_is_retained(self) -> None:
        workspace = self.workspace(
            "failed-dirty",
            (self.build_task("build", "partial-failure", retry_limit=0),),
        )
        provider = MutatingFixtureProvider(failures_before_success=1)
        RunScheduler(TaskRouter(self.registry), provider).run(workspace)
        record = WorktreeManager(workspace).records()[0]
        self.assertEqual(record["status"], WorktreeStatus.RETAINED.value)
        self.assertTrue(record["failure_retained"])
        self.assertTrue(Path(record["path"]).exists())
        self.assertEqual((self.fixture.project / "base.txt").read_text(), "original\n")

    def test_provider_exception_still_produces_retained_diff_evidence(self) -> None:
        class RaisingProvider(MutatingFixtureProvider):
            def execute(
                self,
                task: TaskSpec,
                agent: AgentSpec,
                task_dir: Path,
                project_root: Path,
            ) -> ProviderResult:
                (project_root / "base.txt").write_text("exception-partial\n", encoding="utf-8")
                raise RuntimeError("fixture provider crashed")

        workspace = self.workspace(
            "provider-exception",
            (self.build_task("build", "unused", retry_limit=0),),
        )
        RunScheduler(TaskRouter(self.registry), RaisingProvider()).run(workspace)
        state = workspace.manifest()["tasks"]["build"]
        record = WorktreeManager(workspace).records()[0]
        self.assertEqual(state["status"], TaskStatus.FAILED.value)
        self.assertEqual(record["status"], WorktreeStatus.RETAINED.value)
        candidate = workspace.read_json(state["candidate_result_ref"])
        self.assertEqual(candidate["changed_files"], ["base.txt"])
        self.assertIn("RuntimeError", candidate["provider_result"]["summary"])

    def test_cli_status_and_report_show_safe_candidate_observability(self) -> None:
        workspace = self.workspace(
            "candidate-observability",
            (self.build_task("build", "observable"),),
        )
        RunScheduler(
            TaskRouter(self.registry), MutatingFixtureProvider()
        ).run(workspace)
        report = ResultAggregator().aggregate(workspace)
        self.assertEqual(len(report["workspace_isolation"]), 1)
        item = report["workspace_isolation"][0]
        self.assertEqual(item["status"], WorktreeStatus.COMPLETED.value)
        self.assertNotIn(str(self.root), str(item))

        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(
                [
                    "team",
                    "status",
                    workspace.run_id,
                    "--runs-root",
                    str(self.fixture.runs),
                ]
            )
        self.assertEqual(exit_code, 0)
        self.assertIn('"workspace_isolation"', output.getvalue())
        self.assertNotIn(str(WorktreeManager(workspace).managed_root), output.getvalue())

    def test_cancel_releases_writer_and_retains_partial_candidate(self) -> None:
        ready = self.root / "writer.ready"
        harness = Path(__file__).parent / "fixtures" / "provider_process_harness.py"
        agent = AgentSpec(
            id="native-fixture-writer",
            display_name="Native Fixture Writer",
            provider="local",
            role="builder",
            capabilities=("implementation",),
            command_template=(
                sys.executable,
                str(harness),
                "write-graceful",
                str(ready),
            ),
            cost_class="free",
            concurrency_limit=1,
            permission_profile=("read_workspace", "write_workspace"),
            context_limit=1000,
            availability=True,
            workspace_mode="isolated_worktree",
            local=True,
        )
        registry = AgentRegistry((agent,))
        workspace = self.workspace(
            "cancel-writer",
            (self.build_task("build", "ignored"),),
        )
        scheduler = RunScheduler(
            TaskRouter(registry),
            LocalCommandProvider(enabled=True),
        )
        errors: list[BaseException] = []

        def run() -> None:
            try:
                scheduler.run(workspace)
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not ready.exists():
            time.sleep(0.02)
        self.assertTrue(ready.exists(), "writer fixture never became ready")
        first = MeetingRuntime(
            TaskRouter(registry), LocalCommandProvider(enabled=True)
        ).cancel(workspace, grace_period_seconds=0.5)
        thread.join(timeout=8)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])

        manager = WorktreeManager(workspace)
        record = manager.records()[0]
        self.assertEqual(first["status"], "cancelled")
        self.assertEqual(record["status"], WorktreeStatus.RETAINED.value)
        self.assertIsNone(record["active_writer"])
        self.assertEqual((Path(record["path"]) / "base.txt").read_text(), "partial-candidate\n")
        self.assertEqual((self.fixture.project / "base.txt").read_text(), "original\n")
        candidate_refs = list(workspace.contained("artifacts", "candidates").glob("*.json"))
        self.assertEqual(len(candidate_refs), 1)
        second = MeetingRuntime(
            TaskRouter(registry), LocalCommandProvider(enabled=True)
        ).cancel(workspace, grace_period_seconds=0.5)
        self.assertEqual(second["cancellation"], first["cancellation"])
        self.assertEqual(
            list(workspace.contained("artifacts", "candidates").glob("*.json")),
            candidate_refs,
        )

    def test_parallel_write_requirement_blocks_non_git_workspace(self) -> None:
        plain = self.root / "plain-project"
        plain.mkdir()
        task = TaskSpec(
            id="build",
            title="build",
            role="builder",
            required_capabilities=("implementation",),
            inputs={"parallel_write_required": True, "value": "unsafe"},
            required_permissions=("read_workspace", "write_workspace"),
            retry_limit=0,
        )
        workspace = RunWorkspace.create(
            self.root / "plain-state" / "runs",
            "plain-parallel",
            TaskPlan("parallel write", (task,)),
            project_root=plain,
        )
        provider = MutatingFixtureProvider()
        RunScheduler(TaskRouter(self.registry), provider).run(workspace)
        state = workspace.manifest()["tasks"]["build"]
        self.assertEqual(state["status"], TaskStatus.BLOCKED.value)
        self.assertIn("WORKTREE_UNAVAILABLE", state["error"])
        self.assertEqual(provider.calls, [])

    def test_meeting_is_read_oriented_and_allocates_no_worktree(self) -> None:
        plan = RuleBasedPlanner().plan(
            "Implement a bounded architecture change",
            execution_mode="multi_agent",
        )
        workspace = RunWorkspace.create(
            self.fixture.runs,
            "meeting-read-only",
            plan,
            project_root=self.fixture.project,
        )
        RunScheduler(
            TaskRouter(default_registry().synthetic()),
            FakeProvider(),
        ).run(workspace)
        self.assertEqual(list(workspace.contained("worktrees").glob("*.json")), [])
        self.assertEqual((self.fixture.project / "base.txt").read_text(), "original\n")


if __name__ == "__main__":
    unittest.main()

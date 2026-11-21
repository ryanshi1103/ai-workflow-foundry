from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from flowfoundry.orchestration.aggregator import ResultAggregator
from flowfoundry.orchestration.models import TaskPlan, TaskSpec, TaskStatus
from flowfoundry.orchestration.providers import FakeProvider
from flowfoundry.orchestration.recovery import RecoveryManager
from flowfoundry.orchestration.registry import default_registry
from flowfoundry.orchestration.router import TaskRouter
from flowfoundry.orchestration.scheduler import RunScheduler
from flowfoundry.orchestration.workspace import RunWorkspace
from flowfoundry.orchestration.workspace_preflight import (
    WorkspaceCompatibilityPreflight,
)


class PreflightCountingProvider(FakeProvider):
    execution_kind = "deterministic_preflight_test"


class CodexWorkspacePreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.runs_root = self.temp_path / "runs"
        self.plan = TaskPlan(
            "Codex workspace preflight",
            (
                TaskSpec(
                    id="build",
                    title="Read-only Codex task",
                    role="builder",
                    required_capabilities=("documentation",),
                    required_permissions=("read_workspace",),
                    retry_limit=0,
                ),
            ),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @staticmethod
    def git_init(path: Path) -> None:
        subprocess.run(
            ("git", "init", "--quiet"),
            cwd=path,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )

    @staticmethod
    def scheduler(
        provider: FakeProvider,
        preflight: WorkspaceCompatibilityPreflight | None = None,
    ) -> RunScheduler:
        return RunScheduler(
            TaskRouter(default_registry().synthetic()),
            provider,
            workspace_preflight=preflight,
        )

    def user_workspace(self, name: str) -> Path:
        path = self.temp_path / name
        path.mkdir()
        return path

    def test_real_git_workspace_allows_execution(self) -> None:
        project = self.user_workspace("git-project")
        self.git_init(project)
        workspace = RunWorkspace.create(
            self.runs_root, "real-git", self.plan, project_root=project
        )
        provider = PreflightCountingProvider()

        self.scheduler(provider).run(workspace)

        self.assertEqual(provider.calls, {"build": 1})
        state = workspace.manifest()["tasks"]["build"]
        self.assertEqual(state["status"], TaskStatus.COMPLETED.value)
        self.assertTrue(state["workspace_compatible"])

    def test_user_non_git_workspace_blocks_without_initializing(self) -> None:
        project = self.user_workspace("user-non-git")
        workspace = RunWorkspace.create(
            self.runs_root,
            "user-non-git",
            self.plan,
            project_root=project,
            workspace_origin="user",
        )
        provider = PreflightCountingProvider()

        self.scheduler(provider).run(workspace)

        state = workspace.manifest()["tasks"]["build"]
        self.assertEqual(provider.calls, {})
        self.assertEqual(state["status"], TaskStatus.BLOCKED.value)
        self.assertEqual(state["attempts"], 0)
        self.assertEqual(state["usage"]["provider_calls"], 0)
        self.assertEqual(state["precondition_code"], "CODEX_WORKSPACE_NOT_GIT")
        self.assertFalse((project / ".git").exists())
        report = ResultAggregator().aggregate(workspace)
        self.assertEqual(report["usage"]["provider_calls"], 0)
        self.assertTrue(any("CODEX_WORKSPACE_NOT_GIT" in risk for risk in report["risks"]))

    def test_flowfoundry_disposable_non_git_is_initialized_and_allowed(self) -> None:
        workspace = RunWorkspace.create(
            self.runs_root,
            "disposable-init",
            self.plan,
            workspace_origin="flowfoundry_disposable",
        )
        project = workspace.project_root
        provider = PreflightCountingProvider()

        self.scheduler(provider).run(workspace)

        self.assertTrue((project / ".git").is_dir())
        self.assertEqual(provider.calls, {"build": 1})
        evidence = workspace.read_json("provider-setup/build-workspace-preflight.json")
        self.assertTrue(evidence["compatible"])
        self.assertEqual(evidence["remediation"], "auto_initialized_disposable_git")

    def test_disposable_already_git_is_not_reinitialized(self) -> None:
        workspace = RunWorkspace.create(
            self.runs_root,
            "disposable-git",
            self.plan,
            workspace_origin="flowfoundry_disposable",
        )
        project = workspace.project_root
        self.git_init(project)
        head_before = (project / ".git" / "HEAD").read_text(encoding="utf-8")
        provider = PreflightCountingProvider()

        self.scheduler(provider).run(workspace)

        evidence = workspace.read_json("provider-setup/build-workspace-preflight.json")
        self.assertEqual(evidence["remediation"], "none")
        self.assertNotIn("git_init", evidence["checks"])
        self.assertEqual(
            (project / ".git" / "HEAD").read_text(encoding="utf-8"), head_before
        )
        self.assertEqual(provider.calls, {"build": 1})

    def test_missing_workspace_fails_before_provider_attempt(self) -> None:
        project = self.user_workspace("missing")
        workspace = RunWorkspace.create(
            self.runs_root, "missing", self.plan, project_root=project
        )
        shutil.rmtree(project)
        provider = PreflightCountingProvider()

        self.scheduler(provider).run(workspace)

        state = workspace.manifest()["tasks"]["build"]
        self.assertEqual(provider.calls, {})
        self.assertEqual(state["precondition_code"], "CODEX_WORKSPACE_MISSING")
        self.assertEqual(state["attempts"], 0)

    def test_workspace_file_fails_before_provider_attempt(self) -> None:
        project = self.user_workspace("becomes-file")
        workspace = RunWorkspace.create(
            self.runs_root, "file", self.plan, project_root=project
        )
        project.rmdir()
        project.write_text("not a directory", encoding="utf-8")
        provider = PreflightCountingProvider()

        self.scheduler(provider).run(workspace)

        state = workspace.manifest()["tasks"]["build"]
        self.assertEqual(provider.calls, {})
        self.assertEqual(state["precondition_code"], "CODEX_WORKSPACE_NOT_DIRECTORY")

    def test_git_command_failure_fails_closed(self) -> None:
        project = self.user_workspace("git-failure")
        workspace = RunWorkspace.create(
            self.runs_root, "git-failure", self.plan, project_root=project
        )
        provider = PreflightCountingProvider()
        preflight = WorkspaceCompatibilityPreflight(
            command_runner=lambda command, cwd, timeout: subprocess.CompletedProcess(
                command, 1, stdout="", stderr="unexpected git failure"
            )
        )

        self.scheduler(provider, preflight).run(workspace)

        state = workspace.manifest()["tasks"]["build"]
        self.assertEqual(provider.calls, {})
        self.assertEqual(state["precondition_code"], "CODEX_WORKSPACE_GIT_CHECK_FAILED")

    def test_git_check_timeout_fails_closed(self) -> None:
        project = self.user_workspace("git-timeout")
        workspace = RunWorkspace.create(
            self.runs_root, "git-timeout", self.plan, project_root=project
        )
        provider = PreflightCountingProvider()

        def timeout(
            command: tuple[str, ...], cwd: Path, timeout_seconds: float
        ) -> subprocess.CompletedProcess[str]:
            raise subprocess.TimeoutExpired(command, timeout_seconds)

        preflight = WorkspaceCompatibilityPreflight(command_runner=timeout)

        self.scheduler(provider, preflight).run(workspace)

        state = workspace.manifest()["tasks"]["build"]
        self.assertEqual(provider.calls, {})
        self.assertEqual(state["precondition_code"], "CODEX_WORKSPACE_GIT_CHECK_TIMEOUT")

    def test_resume_after_workspace_fix_rechecks_without_consuming_retry(self) -> None:
        project = self.user_workspace("resume")
        workspace = RunWorkspace.create(
            self.runs_root, "resume", self.plan, project_root=project
        )
        provider = PreflightCountingProvider()
        scheduler = self.scheduler(provider)

        scheduler.run(workspace)
        blocked = workspace.manifest()["tasks"]["build"]
        self.assertEqual(blocked["attempts"], 0)
        self.assertEqual(blocked["usage"]["provider_calls"], 0)
        self.assertEqual(provider.calls, {})

        self.git_init(project)
        RecoveryManager().recover_interrupted(workspace)
        scheduler.run(workspace)

        completed = workspace.manifest()["tasks"]["build"]
        self.assertEqual(completed["status"], TaskStatus.COMPLETED.value)
        self.assertEqual(completed["attempts"], 1)
        self.assertEqual(completed["usage"]["provider_calls"], 1)
        self.assertEqual(provider.calls, {"build": 1})

    def test_local_provider_is_not_subject_to_codex_git_rule(self) -> None:
        plan = TaskPlan(
            "Local validation",
            (
                TaskSpec(
                    id="test",
                    title="Test locally",
                    role="tester",
                    required_capabilities=("testing",),
                    required_permissions=("read_workspace",),
                    retry_limit=0,
                ),
            ),
        )
        project = self.user_workspace("local-non-git")
        workspace = RunWorkspace.create(
            self.runs_root, "local", plan, project_root=project
        )
        provider = PreflightCountingProvider()

        self.scheduler(provider).run(workspace)

        self.assertEqual(provider.calls, {"test": 1})
        self.assertFalse((project / ".git").exists())

    def test_mock_execution_remains_offline_and_does_not_initialize_git(self) -> None:
        project = self.user_workspace("mock-non-git")
        workspace = RunWorkspace.create(
            self.runs_root, "mock", self.plan, project_root=project
        )
        provider = FakeProvider()

        self.scheduler(provider).run(workspace)

        self.assertEqual(provider.calls, {"build": 1})
        self.assertFalse((project / ".git").exists())


if __name__ == "__main__":
    unittest.main()

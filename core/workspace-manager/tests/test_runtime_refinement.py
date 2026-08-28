"""Unit contracts for the Phase 2.1 runtime refinement."""

from __future__ import annotations

import inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from flowfoundry.workspace import lifecycle, sessions
from flowfoundry.workspace.lifecycle import launcher, project
from flowfoundry.workspace.policy import runtime
from flowfoundry.workspace.sessions import finalize
from flowfoundry.workspace.sessions.finalization import pipeline
from flowfoundry.workspace.sessions.finalization.hooks import run_git_finalize_hook
from flowfoundry.workspace.sessions.finalization.output import TranscriptSummary
from flowfoundry.workspace.sessions.finalization.validation import (
    FinalizationContext,
    initial_result,
    resolve_context,
)


class FinalizeUnitTests(unittest.TestCase):
    def test_public_finalize_api_keeps_one_callable(self):
        self.assertIs(sessions.finalize_session, finalize.finalize_session)
        self.assertIs(sessions.finalize_session, pipeline.finalize_session)

    def test_validation_resolves_session_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = Path(temporary)
            project.create_project_structure(project_dir)
            project.create_project_meta(project_dir, "claude", "session-1")
            project.create_session_meta(project_dir, "session-1", "claude")
            result = initial_result(None)

            context = resolve_context(project_dir, None, "codex", result)

            self.assertIsNotNone(context)
            self.assertEqual(context.session_id, "session-1")
            self.assertEqual(context.tool, "claude")
            self.assertEqual(context.project_dir, project_dir)

    def test_pipeline_runs_isolated_stages_and_completion_hook(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = Path(temporary)
            session_id = "session-unit"
            session_dir = project_dir / ".ai-session/sessions" / session_id
            session_dir.mkdir(parents=True)
            session_meta = {
                "transcript_hash": "abc123",
                "redaction_applied": True,
                "finalize_attempts": 0,
            }
            runtime.atomic_write_json(session_dir / "meta.json", session_meta)
            runtime.atomic_write_json(
                project_dir / ".ai-session/project.json",
                {"status": "running", "tool": "claude", "finalize_attempts": 0},
            )
            context = FinalizationContext(
                project_dir=project_dir,
                session_id=session_id,
                session_dir=session_dir,
                project_meta={
                    "status": "running",
                    "tool": "claude",
                    "finalize_attempts": 0,
                },
                session_meta=dict(session_meta),
                tool="claude",
            )
            summary = TranscriptSummary("Refine runtime", ["Split stages"], ["Keep API"])
            result = initial_result(session_id)

            with (
                patch.object(pipeline, "resolve_context", return_value=context),
                patch.object(pipeline, "sync_transcript") as sync,
                patch.object(pipeline, "update_transcript_hash") as update_hash,
                patch.object(pipeline, "parse_transcript", return_value=[{"type": "user"}]),
                patch.object(pipeline, "ensure_redacted_transcript") as redact,
                patch.object(pipeline, "generate_conversation") as conversation,
                patch.object(pipeline, "summarize_transcript", return_value=summary),
                patch.object(pipeline, "write_session_docs") as session_docs,
                patch.object(pipeline, "merge_project_docs") as project_docs,
                patch.object(pipeline, "update_readme") as readme,
                patch.object(pipeline, "update_project_status", return_value=True),
                patch.object(
                    pipeline,
                    "run_git_finalize_hook",
                    return_value={"success": True, "commit": "deadbeef"},
                ) as git_hook,
                patch.object(pipeline, "record_final_commit") as record_commit,
            ):
                completed = pipeline._run_pipeline(
                    project_dir,
                    session_id,
                    "claude",
                    result,
                )

            self.assertEqual(completed["status"], "completed")
            self.assertEqual(completed["commit"], "deadbeef")
            self.assertTrue(completed["success"])
            sync.assert_called_once()
            update_hash.assert_called_once()
            redact.assert_called_once()
            conversation.assert_called_once()
            session_docs.assert_called_once()
            project_docs.assert_called_once()
            readme.assert_called_once()
            git_hook.assert_called_once()
            record_commit.assert_called_once_with(
                project_dir,
                session_id,
                "claude",
                "deadbeef",
            )

    def test_no_git_finalize_hook_is_a_successful_noop(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_git_finalize_hook(
                Path(temporary),
                "session-1",
                "claude",
                {},
                "Goal",
                [],
                [],
                "completed",
                {},
            )

        self.assertTrue(result["success"])
        self.assertIsNone(result["commit"])
        self.assertTrue(result["stage_result"]["nothing_to_commit"])


class LifecycleApiTests(unittest.TestCase):
    def test_lifecycle_exports_stable_canonical_callables(self):
        expected = {
            "create_project_structure": project.create_project_structure,
            "create_project_meta": project.create_project_meta,
            "create_session_meta": project.create_session_meta,
            "read_project_meta": project.read_project_meta,
            "update_project_status": project.update_project_status,
            "launch_new": launcher.launch_new,
            "launch_here": launcher.launch_here,
        }
        for name, implementation in expected.items():
            with self.subTest(name=name):
                self.assertIn(name, lifecycle.__all__)
                self.assertIs(getattr(lifecycle, name), implementation)

    def test_sessions_exports_stable_canonical_callables(self):
        for name in (
            "finalize_session",
            "scan_interrupted_projects",
            "recover_interrupted",
            "recover_all",
            "auto_recover_on_startup",
            "handle_hook_event",
        ):
            with self.subTest(name=name):
                self.assertIn(name, sessions.__all__)
                self.assertTrue(callable(getattr(sessions, name)))

    def test_sessions_first_import_is_cycle_free_in_fresh_interpreter(self):
        repository_root = Path(__file__).resolve().parents[3]
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(repository_root / "src")
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from flowfoundry.workspace.sessions import finalize_session; "
                "from flowfoundry.workspace.lifecycle import launch_here; "
                "assert callable(finalize_session) and callable(launch_here)",
            ],
            cwd=repository_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


class LauncherCompatibilityTests(unittest.TestCase):
    def test_public_launcher_signatures_remain_compatible(self):
        self.assertEqual(
            list(inspect.signature(launcher.launch_new).parameters),
            [
                "tool",
                "cli_path",
                "extra_args",
                "env",
                "model",
                "provider",
                "permission_mode",
                "workflow_contract_id",
            ],
        )
        self.assertEqual(
            list(inspect.signature(launcher.launch_here).parameters),
            [
                "tool",
                "project_dir",
                "cli_path",
                "extra_args",
                "env",
                "model",
                "provider",
                "permission_mode",
            ],
        )

    def test_shared_launch_core_preserves_tracking_environment_and_exit_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = Path(temporary)
            with (
                patch.dict(os.environ, {}, clear=True),
                patch.object(launcher.os, "chdir") as chdir,
                patch.object(
                    launcher.subprocess,
                    "run",
                    return_value=SimpleNamespace(returncode=7),
                ) as run,
                patch.object(launcher, "_safe_finalize", return_value=True) as finalize_call,
            ):
                result = launcher._launch_session(
                    project_dir,
                    "session-1",
                    "claude",
                    "/usr/bin/claude",
                    ["--permission-mode", "plan"],
                    {
                        "CUSTOM_SETTING": "preserved",
                        "AI_PROJECT_MANAGER_SESSION": "blocked-override",
                    },
                )

            self.assertEqual(result, 7)
            chdir.assert_called_once_with(str(project_dir))
            finalize_call.assert_called_once_with(project_dir, "claude")
            child_env = run.call_args.kwargs["env"]
            self.assertEqual(child_env["AI_PROJECT_MANAGER_SESSION"], "session-1")
            self.assertEqual(child_env["AI_PROJECT_MANAGER_PROJECT"], str(project_dir))
            self.assertEqual(child_env["CUSTOM_SETTING"], "preserved")
            self.assertEqual(
                run.call_args.args[0],
                ["/usr/bin/claude", "--permission-mode", "plan"],
            )

    def test_launch_new_keeps_cc_active_project_redirect(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = Path(temporary)
            with (
                patch.dict(os.environ, {"CC_ACTIVE_PROJECT": str(project_dir)}, clear=True),
                patch.object(launcher, "launch_here", return_value=23) as launch_here,
            ):
                result = launcher.launch_new(
                    "claude",
                    cli_path="/synthetic/claude",
                    extra_args=["--permission-mode", "plan"],
                    provider="claude",
                    permission_mode="plan",
                )

            self.assertEqual(result, 23)
            self.assertEqual(launch_here.call_args.kwargs["project_dir"], project_dir)
            self.assertEqual(launch_here.call_args.kwargs["permission_mode"], "plan")

    def test_launch_new_delegates_new_projects_to_shared_core(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = Path(temporary)
            with (
                patch.dict(os.environ, {}, clear=True),
                patch.object(launcher, "auto_recover_on_startup") as recover,
                patch.object(launcher, "_resolve_cli_path", return_value="/bin/tool"),
                patch.object(launcher, "_get_cli_version", return_value="tool 1.0"),
                patch.object(launcher, "create_new_project", return_value=project_dir),
                patch.object(launcher, "git_init"),
                patch.object(launcher, "ensure_git_identity"),
                patch.object(launcher, "_launch_session", return_value=17) as shared,
            ):
                result = launcher.launch_new(
                    "claude",
                    workflow_contract_id="workspace-contract",
                )

            self.assertEqual(result, 17)
            recover.assert_called_once_with()
            self.assertEqual(shared.call_args.kwargs["project_dir"], project_dir)
            self.assertEqual(shared.call_args.kwargs["session_id"], project_dir.name)
            self.assertTrue(shared.call_args.kwargs["announce_created"])

    def test_launch_here_delegates_to_shared_core(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = Path(temporary)
            with (
                patch.dict(os.environ, {}, clear=True),
                patch.object(launcher, "_resolve_cli_path", return_value="/bin/tool"),
                patch.object(launcher, "_prepare_session_here", return_value="session-2"),
                patch.object(launcher, "_launch_session", return_value=19) as shared,
            ):
                result = launcher.launch_here(
                    "codex",
                    project_dir=project_dir,
                    extra_args=["--profile", "safe"],
                )

            self.assertEqual(result, 19)
            self.assertEqual(shared.call_args.kwargs["session_id"], "session-2")
            self.assertEqual(shared.call_args.kwargs["project_dir"], project_dir)


if __name__ == "__main__":
    unittest.main()

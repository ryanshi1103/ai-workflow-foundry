from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from flowfoundry.cli import main
from flowfoundry.orchestration.planner import RuleBasedPlanner
from flowfoundry.orchestration.workspace import RunWorkspace

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/orchestration/codex-builder-deepseek-reviewer.json"


class TeamCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runs_root = Path(self.temp_dir.name) / "runs"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def call(self, *arguments: str) -> tuple[int, str, str]:
        output = io.StringIO()
        error = io.StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            result = main(list(arguments))
        return result, output.getvalue(), error.getvalue()

    def test_offline_run_status_review_and_report(self) -> None:
        result, output, error = self.call(
            "team",
            "run",
            str(EXAMPLE),
            "--run-id",
            "cli-smoke",
            "--runs-root",
            str(self.runs_root),
        )
        self.assertEqual((result, error), (0, ""))
        self.assertEqual(json.loads(output)["status"], "completed")

        result, output, _ = self.call(
            "team", "status", "cli-smoke", "--runs-root", str(self.runs_root)
        )
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output)["run_id"], "cli-smoke")

        result, output, _ = self.call(
            "team", "review", "cli-smoke", "--runs-root", str(self.runs_root)
        )
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output)[0]["decision"], "APPROVED")

        result, output, _ = self.call(
            "team", "report", "cli-smoke", "--runs-root", str(self.runs_root)
        )
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output)["completed_tasks"], ["build", "review", "test"])

    def test_plan_previews_profile_without_creating_a_run(self) -> None:
        task_file = Path(self.temp_dir.name) / "simple-goal.json"
        task_file.write_text(json.dumps({"goal": "Update one README heading"}), encoding="utf-8")
        result, output, error = self.call("team", "plan", str(task_file))
        self.assertEqual((result, error), (0, ""))
        plan = json.loads(output)
        self.assertEqual(plan["routing_decision"]["mode"], "single_agent")
        self.assertEqual(plan["routing_decision"]["estimated_agent_calls"], 1)
        self.assertEqual([task["id"] for task in plan["tasks"]], ["build"])
        self.assertFalse(self.runs_root.exists())

    def test_provider_status_is_structured_and_contains_no_credentials(self) -> None:
        def authenticated_status(
            command: tuple[str, ...],
            timeout: float,
            environment: dict[str, str] | None = None,
        ) -> subprocess.CompletedProcess[str]:
            if Path(command[0]).name == "codex":
                return subprocess.CompletedProcess(
                    command, 0, stdout="Logged in using ChatGPT", stderr=""
                )
            profile = Path(environment["CLAUDE_CONFIG_DIR"]).name
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps({"loggedIn": profile == ".claude-deepseek"}),
                stderr="",
            )

        with patch(
            "flowfoundry.orchestration.discovery._run_command",
            side_effect=authenticated_status,
        ):
            result, output, error = self.call("team", "providers")
        self.assertEqual((result, error), (0, ""))
        statuses = json.loads(output)
        self.assertEqual(
            {status["agent_id"] for status in statuses},
            {"claude-architect", "codex-builder", "deepseek-reviewer", "local-tester"},
        )
        for status in statuses:
            self.assertIn(
                status["authentication_state"],
                {
                    "configured",
                    "not_authenticated",
                    "not_required",
                    "unconfigured",
                    "unverified",
                    "verified",
                },
            )
            self.assertIn(
                status["readiness"],
                {"READY", "AVAILABLE_UNVERIFIED", "UNAVAILABLE"},
            )
            self.assertNotIn("credential_value", status)
        codex = next(status for status in statuses if status["provider"] == "codex")
        self.assertEqual(codex["authentication_state"], "verified")
        self.assertEqual(codex["readiness"], "READY")
        claude = next(status for status in statuses if status["provider"] == "claude")
        self.assertEqual(claude["authentication_state"], "not_authenticated")
        self.assertEqual(claude["readiness"], "AVAILABLE_UNVERIFIED")
        self.assertEqual(claude["runtime_profile"], "claude_native")
        self.assertEqual(claude["provider_identity_state"], "verified")
        deepseek = next(status for status in statuses if status["provider"] == "deepseek")
        self.assertEqual(deepseek["authentication_state"], "verified")
        self.assertEqual(deepseek["readiness"], "READY")
        self.assertEqual(deepseek["runtime_profile"], "deepseek_compatible")
        self.assertEqual(deepseek["provider_identity_state"], "verified")

    def test_run_persists_explicit_shared_workspace(self) -> None:
        task_file = Path(self.temp_dir.name) / "workspace-goal.json"
        project_root = Path(self.temp_dir.name) / "project"
        project_root.mkdir()
        task_file.write_text(json.dumps({"goal": "Update one README heading"}), encoding="utf-8")
        result, output, error = self.call(
            "team",
            "run",
            str(task_file),
            "--run-id",
            "workspace-run",
            "--workspace",
            str(project_root),
            "--runs-root",
            str(self.runs_root),
        )
        self.assertEqual((result, error), (0, ""))
        self.assertEqual(Path(json.loads(output)["project_root"]), project_root)

    def test_run_can_create_owned_disposable_workspace(self) -> None:
        task_file = Path(self.temp_dir.name) / "disposable-goal.json"
        task_file.write_text(
            json.dumps({"goal": "Document one synthetic note"}), encoding="utf-8"
        )
        result, output, error = self.call(
            "team",
            "run",
            str(task_file),
            "--run-id",
            "disposable-run",
            "--disposable-workspace",
            "--runs-root",
            str(self.runs_root),
        )
        self.assertEqual((result, error), (0, ""))
        manifest = json.loads(output)
        project_root = Path(manifest["project_root"])
        self.assertEqual(manifest["workspace_origin"], "flowfoundry_disposable")
        self.assertTrue(manifest["workspace_owned_by_flowfoundry"])
        self.assertTrue(manifest["workspace_disposable"])
        self.assertEqual(project_root.parent, self.runs_root / "disposable-run")

    def test_adaptive_meeting_plan_run_status_and_cancel_are_observable(self) -> None:
        task_file = Path(self.temp_dir.name) / "meeting-goal.json"
        task_file.write_text(
            json.dumps(
                {
                    "goal": "Research and implement a new architecture",
                    "profile": {"complexity": 5, "uncertainty": 4},
                }
            ),
            encoding="utf-8",
        )
        result, output, error = self.call("team", "plan", str(task_file))
        self.assertEqual((result, error), (0, ""))
        preview = json.loads(output)
        self.assertEqual(preview["routing_decision"]["mode"], "multi_agent")
        self.assertEqual(preview["meeting_plan"]["budget"]["max_rounds"], 3)

        result, output, error = self.call(
            "team",
            "run",
            str(task_file),
            "--run-id",
            "meeting-cli",
            "--runs-root",
            str(self.runs_root),
        )
        self.assertEqual((result, error), (0, ""))
        manifest = json.loads(output)
        self.assertEqual(manifest["meeting"]["state"], "completed")
        self.assertTrue(manifest["meeting"]["early_stopped"])
        self.assertIsNotNone(manifest["meeting"]["result_ref"])

        pending = RunWorkspace.create(
            self.runs_root,
            "cancel-cli",
            RuleBasedPlanner().plan("Design a system architecture"),
        )
        self.assertEqual(pending.manifest()["meeting"]["state"], "planned")
        result, output, error = self.call(
            "team", "cancel", "cancel-cli", "--runs-root", str(self.runs_root)
        )
        self.assertEqual((result, error), (0, ""))
        self.assertEqual(json.loads(output)["meeting"]["state"], "cancelled")

    def test_resume_recovers_running_task(self) -> None:
        result, _, _ = self.call(
            "team",
            "run",
            str(EXAMPLE),
            "--run-id",
            "resume-smoke",
            "--runs-root",
            str(self.runs_root),
        )
        self.assertEqual(result, 0)
        manifest_path = self.runs_root / "resume-smoke" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["tasks"]["test"]["status"] = "running"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        result, output, error = self.call(
            "team", "resume", "resume-smoke", "--runs-root", str(self.runs_root)
        )
        self.assertEqual((result, error), (0, ""))
        self.assertEqual(json.loads(output)["status"], "completed")

    def test_missing_run_is_reported_without_traceback(self) -> None:
        result, _, error = self.call(
            "team", "status", "missing", "--runs-root", str(self.runs_root)
        )
        self.assertEqual(result, 2)
        self.assertIn("flowfoundry team", error)

    def test_approve_retry_resume_executes_previously_gated_task(self) -> None:
        task_file = Path(self.temp_dir.name) / "gated.json"
        task_file.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "goal": "Release after approval",
                    "tasks": [
                        {
                            "id": "release",
                            "title": "Release",
                            "role": "builder",
                            "required_capabilities": ["implementation"],
                            "risk_level": "high",
                            "approval_requirements": ["release"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        result, output, _ = self.call(
            "team",
            "run",
            str(task_file),
            "--run-id",
            "gated-cli",
            "--runs-root",
            str(self.runs_root),
        )
        self.assertEqual(result, 0)
        self.assertEqual(
            json.loads(output)["tasks"]["release"]["status"],
            "skipped_pending_human",
        )
        self.assertEqual(
            self.call(
                "team",
                "approve",
                "gated-cli",
                "release",
                "--action",
                "release",
                "--actor",
                "test-operator",
                "--runs-root",
                str(self.runs_root),
            )[0],
            0,
        )
        self.assertEqual(
            self.call(
                "team",
                "retry",
                "gated-cli",
                "release",
                "--runs-root",
                str(self.runs_root),
            )[0],
            0,
        )
        result, output, error = self.call(
            "team", "resume", "gated-cli", "--runs-root", str(self.runs_root)
        )
        self.assertEqual((result, error), (0, ""))
        self.assertEqual(json.loads(output)["status"], "completed")


if __name__ == "__main__":
    unittest.main()

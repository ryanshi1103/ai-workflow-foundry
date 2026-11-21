from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from flowfoundry.cli import main


class CliTests(unittest.TestCase):
    def test_validate_command(self) -> None:
        output = io.StringIO()
        status = {"ready": True, "executor": "codex"}
        with patch("flowfoundry.cli.environment_status", return_value=status), redirect_stdout(output):
            result = main(["validate", "--workspace", "."])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue()), status)

    def test_do_dry_run_needs_no_json_file(self) -> None:
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.goal_runner.shutil.which", return_value="/usr/bin/codex"
        ), redirect_stdout(output):
            root = Path(temp_dir)
            result = main(["do", "fix the bug", "--workspace", str(root), "--dry-run"])
        self.assertEqual(result, 0)
        value = json.loads(output.getvalue())
        self.assertEqual(value["goal"], "fix the bug")
        self.assertEqual(value["status"], "dry_run")

    def test_goal_is_a_shorthand_for_do(self) -> None:
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.goal_runner.shutil.which", return_value="/usr/bin/codex"
        ), redirect_stdout(output):
            result = main(["summarize this repo", "--workspace", temp_dir, "--dry-run"])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["goal"], "summarize this repo")

    def test_missing_workspace_returns_diagnostic(self) -> None:
        error = io.StringIO()
        with redirect_stderr(error):
            result = main(["do", "work", "--workspace", "/definitely/missing"])
        self.assertEqual(result, 2)
        self.assertIn("project root does not exist", error.getvalue())

    def test_do_streams_progress_to_stderr(self) -> None:
        output = io.StringIO()
        error = io.StringIO()

        def run_goal_with_progress(*_: object, **kwargs: object) -> tuple[int, dict]:
            progress = kwargs["progress"]
            self.assertTrue(callable(progress))
            progress("running: python -m unittest")
            return 0, {
                "run_id": "goal-test",
                "goal": "fix it",
                "status": "PASS",
                "verification": {"status": "PASS"},
                "final_message": "done",
                "result": "done",
                "executor": "codex",
                "selection": {"broker_status": "SKIPPED"},
                "changes": {"paths": []},
                "human": {"needs_you": None},
            }

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.cli.run_goal", side_effect=run_goal_with_progress
        ), redirect_stdout(output), redirect_stderr(error):
            result = main(["do", "fix it", "--workspace", temp_dir, "--verbose"])
        self.assertEqual(result, 0)
        self.assertIn("done", output.getvalue())
        self.assertIn(
            "FlowFoundry: running: python -m unittest", error.getvalue()
        )

    def test_default_output_hides_internal_architecture(self) -> None:
        output = io.StringIO()
        error = io.StringIO()
        value = {
            "run_id": "goal-test",
            "goal": "answer this",
            "status": "UNKNOWN",
            "verification": {"status": "UNKNOWN"},
            "result": "the answer",
            "executor": "codex",
            "selection": {"broker_status": "SKIPPED"},
            "changes": {"paths": []},
            "human": {"needs_you": "Confirm the result."},
        }
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "flowfoundry.cli.run_goal", return_value=(0, value)
        ), redirect_stdout(output), redirect_stderr(error):
            result = main(["do", "answer this", "--workspace", temp_dir])
        self.assertEqual(result, 0)
        rendered = output.getvalue()
        self.assertIn("GOAL\n", rendered)
        self.assertIn("WHAT NEEDS YOU\n", rendered)
        self.assertNotIn("goal-test", rendered)
        self.assertNotIn("codex", rendered)
        self.assertNotIn("Broker", rendered)

    def test_team_is_legacy_and_hidden_from_default_help(self) -> None:
        output = io.StringIO()
        with self.assertRaises(SystemExit) as exit_context, redirect_stdout(output):
            main(["--help"])
        self.assertEqual(exit_context.exception.code, 0)
        self.assertNotIn("team", output.getvalue())


if __name__ == "__main__":
    unittest.main()

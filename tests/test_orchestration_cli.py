from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from flowfoundry.cli import main

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


if __name__ == "__main__":
    unittest.main()

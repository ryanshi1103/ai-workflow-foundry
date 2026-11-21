from __future__ import annotations

import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from flowfoundry.project_reporting import TaskReport, save_task_report


class ProjectReportingTests(unittest.TestCase):
    def test_writes_one_report_and_a_small_latest_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "tests@example.invalid"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "FlowFoundry Tests"],
                cwd=root,
                check=True,
            )
            (root / "tracked.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
            base = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
            report = TaskReport(
                task="Core extraction",
                slug="core extraction",
                status="PASS",
                goal="Make the product simpler.",
                base_head=base,
                final_judgment="PRODUCT_PATH_SIMPLIFIED",
                what_changed=("Added the minimal core.",),
                tests_run=("python -m unittest",),
                test_results=("1 passed",),
                next_actions=("Dogfood it.",),
                complete_result="STATUS: PASS\n\nThe complete user-facing result.",
            )
            paths = save_task_report(
                root,
                report,
                now=datetime(2026, 9, 13, 2, 15, tzinfo=timezone.utc),
                copy_to_clipboard=False,
            )

            self.assertEqual(
                paths.report.name, "2026-09-13-0215-core-extraction.md"
            )
            self.assertIn("M tracked.txt", paths.report.read_text())
            self.assertIn("## Complete final result", paths.report.read_text())
            self.assertIn("The complete user-facing result.", paths.report.read_text())
            latest = paths.latest.read_text()
            self.assertIn(str(paths.report.relative_to(root)), latest)
            self.assertNotIn("## Tests run", latest)

    def test_does_not_overwrite_same_minute_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            report = TaskReport(
                task="Audit",
                slug="audit",
                status="PASS",
                goal="Audit",
                base_head="none",
                final_judgment="DONE",
                what_changed=(),
                tests_run=(),
                test_results=(),
            )
            moment = datetime(2026, 9, 13, 2, 15, tzinfo=timezone.utc)
            save_task_report(root, report, now=moment, copy_to_clipboard=False)
            with self.assertRaises(FileExistsError):
                save_task_report(root, report, now=moment, copy_to_clipboard=False)


if __name__ == "__main__":
    unittest.main()

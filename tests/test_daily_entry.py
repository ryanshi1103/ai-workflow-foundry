import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from flowfoundry import daily


class DailyEntryTests(unittest.TestCase):
    def test_detect_project_uses_nearest_git_root(self):
        with self.subTest("git root"):
            import tempfile

            with tempfile.TemporaryDirectory() as raw:
                tmp_path = Path(raw)
                subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
                nested = tmp_path / "src" / "pkg"
                nested.mkdir(parents=True)
                self.assertEqual(daily.detect_project(nested), tmp_path.resolve())


    def test_detect_project_non_git_stays_current(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            nested = Path(raw) / "empty"
            nested.mkdir()
            self.assertEqual(daily.detect_project(nested), nested.resolve())


    def test_first_use_initializes_only_project_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            tmp_path = Path(raw)
            daily.ensure_project_state(tmp_path)
            self.assertTrue((tmp_path / ".ai" / "PROJECT_STATE.md").is_file())
            self.assertTrue((tmp_path / ".ai" / "LATEST.md").is_file())
            self.assertFalse((tmp_path / ".ai" / "DECISIONS.md").exists())


    def test_question_dispatches_to_ask_without_global_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            tmp_path = Path(raw)
            with patch("flowfoundry.cli.main", return_value=0) as dispatch:
                self.assertEqual(daily._dispatch(tmp_path, "我们现在做到哪了？"), 0)
            dispatch.assert_called_once_with(["ask", "我们现在做到哪了？", "--workspace", str(tmp_path)])


    def test_unrelated_quick_mode_does_not_initialize_project(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            tmp_path = Path(raw)
            with patch("flowfoundry.daily.input", return_value="Python yield 是什么意思？"), patch(
                "flowfoundry.daily._quick", return_value=0
            ) as quick:
                self.assertEqual(daily.run(quick=True, root=tmp_path), 0)
            quick.assert_called_once()
            self.assertFalse((tmp_path / ".ai").exists())

    def test_permission_ceiling_does_not_ask_for_provider(self):
        with patch("flowfoundry.daily.input", return_value="1"):
            value = daily._choose_session_permission()
        self.assertEqual(value["name"], "只读规划")
        self.assertTrue(value["read_only"])

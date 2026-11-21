from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flowfoundry import daily
from flowfoundry.core.selection import select_path
from flowfoundry.permissions import session_permission, worker_level
from flowfoundry.workspace.cli import launcher, tui


class FakeTerm:
    def __init__(self, keys: tuple[str, ...] = ()) -> None:
        self.keys = iter(keys)
        self.frames: list[str] = []
        self.entered = 0
        self.exited = 0

    def enter(self) -> None:
        self.entered += 1

    def exit(self) -> None:
        self.exited += 1

    def redraw(self, frame: str) -> None:
        self.frames.append(frame)

    def read_key(self) -> str:
        return next(self.keys)


class AutoIntegrationTests(unittest.TestCase):
    def test_tui_auto_selects_flowfoundry_permission_ceiling(self) -> None:
        project = Path("/project")
        expected = {
            "provider": tui.PROVIDER_FLOWFOUNDRY,
            "permission_level": 2,
            "read_only": False,
            "is_full": False,
        }
        term = FakeTerm(("enter",))
        with (
            patch.object(
                tui,
                "provider_availability",
                return_value={"c": True, "d": False, "o": True},
            ),
            patch.object(tui, "git_info", return_value=("main", tui.DOT_CLEAN, "clean")),
            patch.object(tui, "flowfoundry_permission_screen", return_value=expected) as ceiling,
        ):
            selected = tui.detail_screen(term, project)

        self.assertEqual(selected, expected)
        ceiling.assert_called_once_with(term, project)
        self.assertIn("FlowFoundry · 自动路由", term.frames[0])

    def test_tui_auto_dispatches_selected_project_and_ceiling(self) -> None:
        project = Path("/project")
        term = FakeTerm()
        config = {
            "provider": tui.PROVIDER_FLOWFOUNDRY,
            "permission_level": 3,
            "read_only": False,
            "is_full": False,
        }
        with (
            patch.object(tui, "RawTerm", return_value=term),
            patch.object(tui.launcher, "_fast_determine_project", return_value=project),
            patch.object(tui.launcher, "add_to_recent"),
            patch.object(tui.launcher, "has_git", return_value=True),
            patch.object(tui, "detail_screen", return_value=config),
            patch(
                "flowfoundry.workspace.cli.auto_ui.run_auto_session",
                return_value="quit",
            ) as session,
            patch.object(tui.launcher, "_launch_flowfoundry") as plain_launch,
        ):
            self.assertEqual(tui.tui_main(), 0)

        session.assert_called_once_with(term, project, 3)
        plain_launch.assert_not_called()
        self.assertGreaterEqual(term.exited, 1)

    def test_tui_direct_codex_path_does_not_enter_flowfoundry(self) -> None:
        project = Path("/project")
        term = FakeTerm()
        config = {
            "provider": tui.PROVIDER_CODEX,
            "mode": "p",
            "profile": "gpt56-sol-readonly",
            "is_full": False,
        }
        with (
            patch.object(tui, "RawTerm", return_value=term),
            patch.object(tui.launcher, "_fast_determine_project", return_value=project),
            patch.object(tui.launcher, "add_to_recent"),
            patch.object(tui.launcher, "has_git", return_value=True),
            patch.object(tui, "detail_screen", return_value=config),
            patch.object(tui.launcher, "_codex_preflight", return_value=True),
            patch.object(tui, "_record_launch"),
            patch.object(tui.launcher, "_launch_codex", return_value=19) as codex,
            patch.object(tui.launcher, "_launch_flowfoundry") as automatic,
        ):
            self.assertEqual(tui.tui_main(), 19)

        codex.assert_called_once_with(project, "gpt56-sol-readonly")
        automatic.assert_not_called()

    def test_plain_launcher_exposes_same_auto_path(self) -> None:
        project = Path("/project")
        permission = session_permission(2)
        with (
            patch.object(tui, "is_tui_session", return_value=False),
            patch.object(launcher, "determine_project", return_value=project),
            patch.object(launcher, "_show_remote_banner"),
            patch.object(launcher, "add_to_recent"),
            patch.object(launcher, "has_git", return_value=True),
            patch.object(launcher, "_find_executable", return_value="/usr/bin/codex"),
            patch.object(launcher, "_choose_provider", return_value="a"),
            patch.object(launcher, "_choose_flowfoundry_permission", return_value=permission),
            patch.object(launcher, "_launch_flowfoundry", return_value=23) as launch,
        ):
            self.assertEqual(launcher.main(), 23)

        launch.assert_called_once_with(project, 2)

    def test_launcher_selected_ceiling_is_reused_for_multiple_goals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            answers = iter(("fix the README", "inspect the tests", "/quit"))
            with (
                patch.object(daily, "input", side_effect=lambda _: next(answers)),
                patch("flowfoundry.cli.main", return_value=0) as dispatch,
            ):
                self.assertEqual(daily.run(root=root, permission_level=4), 0)

        self.assertEqual(dispatch.call_count, 2)
        for call in dispatch.call_args_list:
            args = call.args[0]
            self.assertEqual(args[-2:], ["--permission-level", "4"])

    def test_continue_reuses_latest_project_run_and_current_ceiling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_dir = root / ".flowfoundry" / "do" / "goal-existing"
            result_dir.mkdir(parents=True)
            (result_dir / "result.json").write_text(
                json.dumps(
                    {
                        "project_root": str(root),
                        "thread_id": "thread-existing",
                        "finished_at": "2026-09-13T15:00:00+08:00",
                    }
                ),
                encoding="utf-8",
            )
            foreign_dir = root / ".flowfoundry" / "do" / "goal-foreign"
            foreign_dir.mkdir()
            (foreign_dir / "result.json").write_text(
                json.dumps(
                    {
                        "project_root": str(root / "another-project"),
                        "thread_id": "thread-foreign",
                        "finished_at": "2026-09-13T16:00:00+08:00",
                    }
                ),
                encoding="utf-8",
            )
            answers = iter(("/continue", "/quit"))
            with (
                patch.object(daily, "input", side_effect=lambda _: next(answers)),
                patch("flowfoundry.cli.main", return_value=0) as dispatch,
            ):
                self.assertEqual(daily.run(root=root, permission_level=3), 0)

        args = dispatch.call_args.args[0]
        self.assertIn("--permission-level", args)
        self.assertEqual(args[args.index("--permission-level") + 1], "3")
        self.assertEqual(args[-2:], ["--resume", "goal-existing"])

    def test_minimum_sufficient_path_and_permission_bounds_are_retained(self) -> None:
        simple = select_path("Fix the README typo and run the test")
        complex_goal = select_path(
            "Refactor the launcher integration, preserve compatibility, and run all tests"
        )

        self.assertEqual(simple.executor, "codex")
        self.assertFalse(simple.broker_requested)
        self.assertFalse(simple.needs_second_opinion)
        self.assertEqual(complex_goal.executor, "codex")
        self.assertFalse(complex_goal.broker_requested)
        self.assertFalse(complex_goal.needs_second_opinion)
        for ceiling in (1, 2, 3, 4):
            self.assertLessEqual(worker_level(ceiling, "coding"), ceiling)


if __name__ == "__main__":
    unittest.main()

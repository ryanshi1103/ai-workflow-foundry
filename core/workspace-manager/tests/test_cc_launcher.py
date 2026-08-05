"""Regression coverage for the unified ``cc`` Python launcher.

These tests replace static assertions against the retired 1000-line shell
implementation with behavior-level coverage of the same public launcher
contract.  All temporary projects stay below the active repository and are
removed by ``TemporaryDirectory``.
"""

from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from flowfoundry.workspace import cc_launcher


REPO_ROOT = Path(__file__).resolve().parents[3]
COMPONENT_ROOT = REPO_ROOT / "core" / "workspace-manager"
TEST_TMP_BASE = Path(os.environ.get("FLOWFOUNDRY_TEST_TMP", REPO_ROOT / ".test-tmp"))


class RepoTemporaryDirectory(tempfile.TemporaryDirectory):
    def __init__(self):
        TEST_TMP_BASE.mkdir(parents=True, exist_ok=True)
        super().__init__(dir=TEST_TMP_BASE)


class WrapperContractTests(unittest.TestCase):
    def test_all_public_wrappers_pass_bash_syntax(self):
        for name in ("cc", "aiproj", "cc-projects-maintain"):
            result = subprocess.run(
                ["bash", "-n", str(COMPONENT_ROOT / "bin" / name)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrappers_delegate_to_unified_public_modules(self):
        expected = {
            "cc": "flowfoundry.cc",
            "aiproj": "flowfoundry.aiproj",
            "cc-projects-maintain": "flowfoundry.workspace.maintain_cli",
        }
        for name, module in expected.items():
            source = (COMPONENT_ROOT / "bin" / name).read_text(encoding="utf-8")
            self.assertIn(f"python3 -m {module}", source)
            self.assertIn("MONOREPO_ROOT", source)

    def test_wrapper_has_no_project_specific_default(self):
        source = (COMPONENT_ROOT / "bin" / "cc").read_text(encoding="utf-8")
        self.assertNotIn("meeting-media-auto", source)


class LauncherHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = RepoTemporaryDirectory()
        self.root = Path(self.temp.name)
        self.projects = self.root / "home" / "Projects"
        self.projects.mkdir(parents=True)
        self.state = self.root / "state" / "cc-launcher"
        self.recent = self.state / "recent-projects"

    def tearDown(self):
        self.temp.cleanup()

    def launcher_paths(self):
        return patch.multiple(
            cc_launcher,
            PROJECTS_ROOT=self.projects,
            RECENT_STATE_DIR=self.state,
            RECENT_FILE=self.recent,
        )

    def test_timestamp_session_names_are_rejected(self):
        self.assertTrue(cc_launcher.is_timestamp_session_dir("20260805-120102-codex-a1b2c3"))
        self.assertFalse(cc_launcher.is_timestamp_session_dir("real-project"))

    def test_recent_projects_are_ordered_deduplicated_and_space_safe(self):
        first = self.projects / "project one"
        second = self.projects / "project-two"
        first.mkdir()
        second.mkdir()
        with self.launcher_paths():
            cc_launcher.add_to_recent(first)
            cc_launcher.add_to_recent(second)
            cc_launcher.add_to_recent(first)
        self.assertEqual(self.recent.read_text(encoding="utf-8").splitlines(), [str(first), str(second)])

    def test_recent_projects_drop_stale_entries_and_cap_at_twenty(self):
        stale = self.projects / "stale"
        stale.mkdir()
        with self.launcher_paths():
            cc_launcher.add_to_recent(stale)
            stale.rmdir()
            for index in range(25):
                project = self.projects / f"many-{index:02d}"
                project.mkdir()
                cc_launcher.add_to_recent(project)
        entries = self.recent.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(entries), 20)
        self.assertNotIn(str(stale), entries)

    def test_recent_projects_reject_outside_and_session_directories(self):
        outside = self.root / "outside"
        outside.mkdir()
        timestamped = self.projects / "20260805-120102-codex-a1b2c3"
        timestamped.mkdir()
        nested_session = self.projects / "real" / ".ai-session" / "sessions" / "session"
        nested_session.mkdir(parents=True)
        with self.launcher_paths():
            cc_launcher.add_to_recent(outside)
            cc_launcher.add_to_recent(timestamped)
            cc_launcher.add_to_recent(nested_session)
        self.assertFalse(self.recent.exists())

    def test_project_picker_group_honors_managed_and_archive_policy(self):
        policy = self.root / "managed-projects"
        policy.write_text(
            "public-copy | managed | true | mirror\n"
            "old-workspace | archive | false | legacy\n"
            "flagship | primary | true | main\n",
            encoding="utf-8",
        )
        with patch.dict(os.environ, {"CC_MANAGED_PROJECTS_FILE": str(policy)}):
            self.assertEqual(cc_launcher.project_picker_group("public-copy"), "managed")
            self.assertEqual(cc_launcher.project_picker_group("old-workspace"), "managed")
            self.assertEqual(cc_launcher.project_picker_group("flagship"), "primary")
            self.assertEqual(cc_launcher.project_picker_group("unknown"), "primary")

    def test_recent_menu_shows_basename_full_path_and_navigation(self):
        project = self.projects / "recent-project"
        project.mkdir()
        self.state.mkdir(parents=True)
        self.recent.write_text(f"{project}\n", encoding="utf-8")
        output = io.StringIO()
        with self.launcher_paths(), patch.object(cc_launcher, "_input_fn", lambda _: "b"), \
                patch.object(cc_launcher, "project_indicators", lambda _: "[Git]"), redirect_stdout(output):
            selected = cc_launcher._recent_menu()
        rendered = output.getvalue()
        self.assertIsNone(selected)
        self.assertIn("recent-project", rendered)
        self.assertIn(str(project), rendered)
        self.assertIn("返回主菜单", rendered)
        self.assertIn("q  退出", rendered)

    def test_create_project_rejects_traversal_then_initializes_git(self):
        answers = iter(["../escape", "new-project", "1"])
        with self.launcher_paths(), patch.object(cc_launcher, "_input_fn", lambda _: next(answers)):
            created = cc_launcher._create_new_project()
        self.assertEqual(created, self.projects / "new-project")
        self.assertTrue((created / ".git").is_dir())

    def test_create_project_can_open_existing_directory(self):
        existing = self.projects / "existing"
        existing.mkdir()
        answers = iter(["existing", "1", "1"])
        with self.launcher_paths(), patch.object(cc_launcher, "_input_fn", lambda _: next(answers)):
            selected = cc_launcher._create_new_project()
        self.assertEqual(selected, existing)

    def test_manual_input_resolves_existing_path(self):
        target = self.root / "manual project"
        target.mkdir()
        output = io.StringIO()
        with patch.object(cc_launcher, "_input_fn", lambda _: str(target)), redirect_stdout(output):
            selected = cc_launcher._manual_input()
        self.assertEqual(selected, target.resolve())
        self.assertIn("解析后的路径", output.getvalue())

    def test_determine_project_uses_here_and_preset_modes(self):
        target = self.projects / "preset"
        target.mkdir()
        with patch.dict(os.environ, {"_CC_PRESET_PROJECT": str(target)}, clear=False):
            self.assertEqual(cc_launcher.determine_project(), target)
        with patch.dict(os.environ, {"_CC_HERE_MODE": "1"}, clear=False), \
                patch("pathlib.Path.cwd", return_value=target):
            self.assertEqual(cc_launcher.determine_project(), target)


class MenuContractTests(unittest.TestCase):
    def run_prompt(self, function, answer):
        output = io.StringIO()
        with patch.object(cc_launcher, "_input_fn", lambda _: answer), redirect_stdout(output):
            result = function()
        return result, output.getvalue()

    def test_provider_menu_preserves_all_tools_and_safe_exit(self):
        project = Path("/tmp/synthetic-project")
        for answer in ("c", "d", "o"):
            output = io.StringIO()
            with patch.object(cc_launcher, "_input_fn", lambda _, value=answer: value), redirect_stdout(output):
                self.assertEqual(cc_launcher._choose_provider(project), answer)
            rendered = output.getvalue()
            self.assertIn("Claude", rendered)
            self.assertIn("DeepSeek", rendered)
            self.assertIn("OpenAI Codex", rendered)
        output = io.StringIO()
        with patch.object(cc_launcher, "_input_fn", lambda _: "q"), redirect_stdout(output):
            self.assertIsNone(cc_launcher._choose_provider(project))
        self.assertIn("已取消", output.getvalue())

    def test_invalid_provider_is_an_error(self):
        output = io.StringIO()
        with patch.object(cc_launcher, "_input_fn", lambda _: "x"), redirect_stdout(output):
            result = cc_launcher._choose_provider(Path("/tmp/synthetic-project"))
        self.assertEqual(result, "error")
        self.assertIn("无效选择", output.getvalue())

    def test_claude_permission_modes_preserve_public_values(self):
        expected = {
            "m": ("default", False),
            "e": ("acceptEdits", False),
            "p": ("plan", False),
            "a": ("auto", False),
            "b": ("bypassPermissions", True),
        }
        for answer, (mode, bypass) in expected.items():
            with self.subTest(answer=answer), patch.object(cc_launcher, "_input_fn", lambda _, value=answer: value):
                result = cc_launcher._choose_permission_mode()
            self.assertEqual(result["mode"], mode)
            self.assertEqual(result["bypass"], bypass)

    def test_codex_modes_preserve_profile_mapping(self):
        expected = {
            "m": "gpt56-sol-manual",
            "p": "gpt56-sol-readonly",
            "a": "gpt56-sol-auto",
            "b": "gpt56-sol-full",
        }
        for answer, profile in expected.items():
            with self.subTest(answer=answer), patch.object(cc_launcher, "_input_fn", lambda _, value=answer: value):
                result = cc_launcher._choose_codex_mode()
            self.assertEqual(result["profile"], profile)

    def test_prompt_records_closed_input(self):
        with patch.object(cc_launcher, "_input_fn", lambda _: (_ for _ in ()).throw(EOFError)):
            self.assertEqual(cc_launcher._prompt("prompt"), "")
        self.assertTrue(cc_launcher._prompt_closed)

    def test_remote_confirmation_requires_exact_phrase(self):
        output = io.StringIO()
        with patch.object(cc_launcher, "_is_remote", True), \
                patch.object(cc_launcher, "_input_fn", lambda _: "wrong"), redirect_stdout(output):
            self.assertFalse(cc_launcher._confirm_remote("test mode"))
        self.assertIn("远程高权限确认失败", output.getvalue())
        with patch.object(cc_launcher, "_is_remote", True), \
                patch.object(cc_launcher, "_input_fn", lambda _: "remote-yes"):
            self.assertTrue(cc_launcher._confirm_remote("test mode"))


class LaunchContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = RepoTemporaryDirectory()
        self.project = Path(self.temp.name) / "project"
        self.project.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_claude_launch_uses_selected_project_provider_and_permission(self):
        with patch.dict(os.environ, {}, clear=True), \
                patch.object(cc_launcher, "_find_executable", return_value="/usr/bin/claude"), \
                patch("flowfoundry.workspace.launcher.launch_here", return_value=0) as launch:
            result = cc_launcher._launch_claude(self.project, "claude", "plan", False)
        self.assertEqual(result, 0)
        kwargs = launch.call_args.kwargs
        self.assertEqual(kwargs["project_dir"], self.project)
        self.assertEqual(kwargs["provider"], "claude")
        self.assertEqual(kwargs["permission_mode"], "plan")
        self.assertIn("--permission-mode", kwargs["extra_args"])

    def test_deepseek_uses_isolated_config_directory(self):
        with patch.dict(os.environ, {}, clear=True), \
                patch.object(cc_launcher, "_find_executable", return_value="/usr/bin/claude"), \
                patch("flowfoundry.workspace.launcher.launch_here", return_value=0):
            cc_launcher._launch_claude(self.project, "deepseek", "default", False)
            self.assertTrue(os.environ["CLAUDE_CONFIG_DIR"].endswith(".claude-deepseek"))

    def test_codex_launch_execs_native_cli_in_selected_project(self):
        with patch.object(cc_launcher, "_find_executable", return_value="/usr/bin/codex"), \
                patch("os.chdir") as chdir, patch("os.execv") as execv:
            result = cc_launcher._launch_codex(self.project, "gpt56-sol-readonly")
        self.assertEqual(result, 0)
        chdir.assert_called_once_with(self.project)
        execv.assert_called_once_with(
            "/usr/bin/codex", ["/usr/bin/codex", "--profile", "gpt56-sol-readonly"]
        )


class SourceSafetyTests(unittest.TestCase):
    def test_launcher_retains_api_preflight_and_no_public_dns_probe(self):
        source = Path(cc_launcher.__file__).read_text(encoding="utf-8")
        self.assertIn("https://api.openai.com/", source)
        self.assertNotIn("/dev/tcp/8.8.8.8/53", source)

    def test_launcher_has_no_eval_or_root_recursive_delete(self):
        source = Path(cc_launcher.__file__).read_text(encoding="utf-8")
        self.assertNotIn("eval(", source)
        self.assertNotIn("rm -rf /", source)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
import pty
import select
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from flowfoundry.workspace.cli import auto_ui, layout


class FakeTerm:
    def __init__(self, keys: tuple[str, ...]) -> None:
        self.keys = iter(keys)
        self.frames: list[str] = []

    def redraw(self, frame: str) -> None:
        self.frames.append(frame)

    def read_key(self) -> str:
        return next(self.keys)


def box_widths(frame: str) -> set[int]:
    return {
        layout.display_width(line)
        for line in frame.splitlines()
        if line.startswith(("╭", "│", "╰"))
    }


class WrapTextTests(unittest.TestCase):
    def test_wraps_english_at_words_and_cjk_at_cells(self) -> None:
        english = layout.wrap_text("alpha beta gamma delta", 12)
        cjk = layout.wrap_text("检查这个项目最重要的问题", 10)

        self.assertEqual(english, ["alpha beta", "gamma delta"])
        self.assertGreater(len(cjk), 1)
        for line in [*english, *cjk]:
            self.assertLessEqual(layout.display_width(line), 12)

    def test_wrap_preserves_explicit_blank_lines(self) -> None:
        self.assertEqual(layout.wrap_text("one\n\ntwo", 20), ["one", "", "two"])


class AutoFrameTests(unittest.TestCase):
    project = Path("ai-workflow-foundry")

    def assert_frame_fits(self, frame: str, width: int, height: int) -> None:
        self.assertEqual(len(box_widths(frame)), 1)
        self.assertLessEqual(max(map(layout.display_width, frame.splitlines())), width)
        self.assertLessEqual(len(frame.splitlines()), height)

    def test_empty_and_long_question_frames_match_launcher_contract(self) -> None:
        prompts = (
            "",
            "检查这个项目并把今天最值得完成的事情做完，同时保留现有的经典 CC 启动体验。",
            "Inspect the project, fix the most important usability issue, and verify the complete launcher flow without changing manual providers.",
        )
        for width, height in ((42, 14), (80, 24), (140, 32)):
            for prompt in prompts:
                with self.subTest(width=width, prompt=prompt[:8]):
                    frame = auto_ui.build_auto_question_frame(
                        project=self.project,
                        permission_name="项目内自动修改",
                        buffer=prompt,
                        cursor=len(prompt),
                        term_size=(width, height),
                    )
                    self.assert_frame_fits(frame, width, height)
                    self.assertIn("· Auto", frame)
                    self.assertIn("权限", frame)
                    self.assertIn("目标", frame)
                    self.assertIn("▊", frame)

    def test_running_frame_is_compact_and_hides_backend_progress(self) -> None:
        frame = auto_ui.build_auto_running_frame(
            project=self.project,
            permission_name="项目内自动修改",
            goal="修掉当前最影响使用的问题。",
            phase=auto_ui._phase_for_progress("running: python -m unittest"),
            elapsed_seconds=18.9,
            term_size=(80, 24),
        )
        self.assert_frame_fits(frame, 80, 24)
        self.assertIn("RUNNING · 处理中", frame)
        self.assertIn("阶段  执行与检查", frame)
        self.assertIn("已用  18 秒", frame)
        self.assertNotIn("python -m unittest", frame)

    def test_result_states_are_honest_responsive_and_sanitized(self) -> None:
        for status, label in (
            ("PASS", "PASS · 完成"),
            ("PARTIAL", "PARTIAL · 部分完成"),
            ("UNKNOWN", "UNKNOWN · 需要确认"),
            ("FAIL", "FAILED · 未完成"),
        ):
            with self.subTest(status=status):
                frame = auto_ui.build_auto_result_frame(
                    project=Path("a-very-long-project-name-for-founder-work"),
                    permission_name="只读规划",
                    result=auto_ui.AutoResult(
                        status,
                        "检查项目现在是否可以发布。",
                        "结果\x1b[2J不能控制终端。" * 12,
                        "没有足够证据确认已经完成",
                        "确认外部发布条件",
                    ),
                    term_size=(42, 14),
                )
                self.assert_frame_fits(frame, 42, 14)
                self.assertIn(label, frame)
                self.assertNotIn("\x1b[2J", frame)
                self.assertIn("Tab 返回", frame.splitlines()[-1])

    def test_summary_strips_markdown_paths_and_keeps_evidence_visible(self) -> None:
        result = auto_ui._goal_result(
            {
                "status": "UNKNOWN",
                "goal": "检查项目",
                "result": "[README](/absolute/private/path:12) 里有 **一项改进**。" * 20,
                "verification": {
                    "status": "UNKNOWN",
                    "evidence": [],
                    "needs_user": (
                        "No deterministic acceptance check was available; "
                        "confirm the result."
                    ),
                },
                "changes": {"paths": []},
                "human": {"needs_you": None},
            }
        )
        frame = auto_ui.build_auto_result_frame(
            project=self.project,
            permission_name="只读规划",
            result=result,
            term_size=(80, 24),
        )
        self.assertNotIn("/absolute/private/path", frame)
        self.assertNotIn("**", frame)
        self.assertIn("验证", frame)
        self.assertIn("需要你", frame)
        self.assertIn("没有可用的确定性验收检查", frame)

    def test_worker_report_is_primary_and_survives_unknown_with_code(self) -> None:
        response = (
            "I inspected the result path and found the 120-character truncation. "
            "The Worker response now remains first-class persisted data.\n\n"
            "Tests run:\n- python -m unittest tests.test_auto_ui — PASS.\n\n"
            "Remaining issue: no deterministic product acceptance check existed."
        )
        result = auto_ui._goal_result(
            {
                "status": "UNKNOWN",
                "goal": "repair reporting",
                "responsible_agent": "Codex",
                "agent_response": response,
                "result": "Evaluator-generated tiny summary that must not win.",
                "verification": {
                    "status": "UNKNOWN",
                    "evidence": [
                        {
                            "kind": "command",
                            "command": "python -m unittest tests.test_auto_ui",
                            "exit_code": 0,
                            "acceptance_check": False,
                        }
                    ],
                    "needs_user": "No deterministic acceptance check was available; confirm the result.",
                },
                "changes": {
                    "paths": [
                        "__pycache__/reporting.cpython-314.pyc",
                        "src/reporting.py",
                        "tests/test_reporting.py",
                    ],
                    "diff": (
                        "diff -- __pycache__/reporting.cpython-314.pyc\n"
                        "Binary file changed.\n"
                        "--- a/src/reporting.py\n+++ b/src/reporting.py\n"
                        "+agent_response = final_message"
                    ),
                },
                "human": {"needs_you": None},
            }
        )
        frame = auto_ui.build_auto_result_frame(
            project=self.project,
            permission_name="项目内自动修改",
            result=result,
            term_size=(100, 80),
        )

        self.assertIn("负责 Agent  Codex", frame)
        self.assertIn("I inspected the result path", frame)
        self.assertIn("Remaining issue", frame)
        self.assertNotIn("Evaluator-generated tiny summary", frame)
        self.assertIn("src/reporting.py", frame)
        self.assertLess(frame.index("src/reporting.py"), frame.index("__pycache__"))
        self.assertIn("agent_response = final_message", frame)
        self.assertNotIn("Binary file changed", frame)
        self.assertIn("python -m unittest tests.test_auto_ui", frame)
        self.assertIn("UNKNOWN · 需要确认", frame)

    def test_code_blocks_preserve_python_dunder_names(self) -> None:
        presented = auto_ui._present_text(
            "**Implementation**\n```python\nif __name__ == '__main__':\n    run()\n```"
        )
        self.assertIn("Implementation", presented)
        self.assertIn("if __name__ == '__main__':", presented)

    def test_project_ask_removes_backend_scaffolding_from_founder_result(self) -> None:
        value = auto_ui._ask_result(
            {
                "status": "PARTIAL",
                "question": "项目现状是什么？",
                "answer": (
                    "Recorded context (selected excerpts):\n\n"
                    "- The native UI is active. [1; ACCEPTED]\n\n"
                    "These excerpts may not fully answer the question; completeness "
                    "and conflicts are not verified. CANDIDATE material is unaccepted."
                ),
                "sources": [{"path": ".ai/PROJECT_STATE.md"}],
            }
        )
        self.assertEqual(value.result, "- The native UI is active.")
        self.assertNotIn("ACCEPTED", value.result)
        self.assertIn("完整性尚未验证", value.validation)


class AutoSessionTests(unittest.TestCase):
    def test_question_uses_project_ask_then_returns_to_input(self) -> None:
        question = "项目现状是什么？"
        term = FakeTerm(tuple(question) + ("enter", "enter") + tuple("/quit") + ("enter",))
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            with (
                patch.object(auto_ui, "ensure_project_state"),
                patch.object(auto_ui, "_term_size", return_value=(80, 24)),
                patch.object(
                    auto_ui,
                    "ask_project",
                    return_value={
                        "status": "PARTIAL",
                        "question": question,
                        "answer": "已有项目记录。",
                        "sources": [{"path": ".ai/PROJECT_STATE.md"}],
                    },
                ) as ask,
                patch.object(auto_ui, "run_goal") as work,
            ):
                outcome = auto_ui.run_auto_session(term, project, 1)

        self.assertEqual(outcome, auto_ui.AUTO_QUIT)
        ask.assert_called_once_with(project.resolve(), question)
        work.assert_not_called()
        self.assertTrue(any("PARTIAL · 部分完成" in frame for frame in term.frames))

    def test_goal_reuses_ceiling_and_shows_native_result(self) -> None:
        goal = "fix the readme"
        term = FakeTerm(tuple(goal) + ("enter", "q"))

        def completed(*args: object, **kwargs: object) -> tuple[int, dict]:
            kwargs["progress"]("executor session ready")
            return 0, {
                "status": "PASS",
                "goal": goal,
                "result": "README fixed.",
                "verification": {
                    "status": "PASS",
                    "evidence": [
                        {
                            "acceptance_check": True,
                            "exit_code": 0,
                        }
                    ],
                    "needs_user": None,
                },
                "changes": {"paths": ["README.md"]},
                "human": {"needs_you": None},
            }

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            with (
                patch.object(auto_ui, "ensure_project_state"),
                patch.object(auto_ui, "_term_size", return_value=(80, 24)),
                patch.object(auto_ui, "run_goal", side_effect=completed) as work,
            ):
                outcome = auto_ui.run_auto_session(term, project, 2)

        self.assertEqual(outcome, auto_ui.AUTO_QUIT)
        self.assertEqual(work.call_args.kwargs["permission_level"], 2)
        self.assertFalse(work.call_args.kwargs["read_only"])
        self.assertTrue(any("RUNNING · 处理中" in frame for frame in term.frames))
        self.assertTrue(any("PASS · 完成" in frame for frame in term.frames))


@unittest.skipIf(sys.platform == "win32", "POSIX pty only")
class PtyAutoSmokeTests(unittest.TestCase):
    def test_project_to_auto_to_question_is_one_tui_flow(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        temp_root = repo / ".test-tmp"
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            root = Path(directory)
            projects = root / "Projects"
            project = projects / "alpha"
            project.mkdir(parents=True)
            subprocess.run(
                ["git", "-C", str(project), "init", "-q"],
                check=True,
                capture_output=True,
            )
            script = (
                "import sys; sys.path.insert(0, %r)\n"
                "from pathlib import Path\n"
                "from unittest.mock import patch\n"
                "from flowfoundry.workspace.cli import auto_ui, tui\n"
                "tui.launcher.PROJECTS_ROOT = Path(%r)\n"
                "answer = {'status':'PARTIAL','question':'项目现状是什么？',"
                "'answer':'项目记录可用。','sources':[{'path':'state'}]}\n"
                "with patch.object(auto_ui, 'ask_project', return_value=answer), "
                "patch.object(tui, 'provider_availability', "
                "return_value={tui.PROVIDER_CODEX: True}), "
                "patch.object(tui.launcher, '_fast_determine_project', return_value=None):\n"
                "    raise SystemExit(tui.tui_main())\n"
                % (str(repo / "src"), str(projects))
            )
            master, slave = pty.openpty()
            proc = subprocess.Popen(
                [sys.executable, "-c", script],
                stdin=slave,
                stdout=slave,
                stderr=slave,
                env={**os.environ, "PYTHONPATH": str(repo / "src")},
                cwd=root,
                close_fds=True,
            )
            os.close(slave)

            output = b""
            state = 0
            markers = (
                "CC · Projects",
                "FlowFoundry · 自动路由",
                "Auto 权限上限",
                "READY · 就绪",
                "PARTIAL · 部分完成",
            )
            actions = (b"\r", b"\r", b"\r", "项目现状是什么？\r".encode(), b"q")
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline and proc.poll() is None:
                readable, _, _ = select.select([master], [], [], 0.2)
                if not readable:
                    continue
                try:
                    output += os.read(master, 8192)
                except OSError:
                    break
                text = output.decode("utf-8", errors="replace")
                if state < len(markers) and markers[state] in text:
                    os.write(master, actions[state])
                    state += 1
            timed_out = False
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
                timed_out = True
            finally:
                os.close(master)

            text = output.decode("utf-8", errors="replace")
            self.assertFalse(timed_out, f"PTY stopped at state {state}:\n{text[-2000:]}")
            self.assertEqual(proc.returncode, 0, text[-2000:])
            self.assertEqual(state, len(markers), text[-2000:])
            for marker in markers:
                self.assertIn(marker, text)
            self.assertIn("alpha · Auto", text)
            self.assertNotIn("FlowFoundry\r\nProject:", text)


if __name__ == "__main__":
    unittest.main()

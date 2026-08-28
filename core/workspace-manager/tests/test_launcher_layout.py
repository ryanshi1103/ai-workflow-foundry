"""Coverage for the cc launcher's content-aware adaptive layout engine.

The engine itself is pure (`flowfoundry.workspace.cli.layout`) and the
frame builders are strings-in/strings-out (`flowfoundry.workspace.cli.tui`),
so alignment contracts are asserted directly.  A PTY smoke test exercises
the raw-mode interactive loop end to end.

Plain ``unittest`` so the suite runs without third-party dependencies.
"""

from __future__ import annotations

import os
import pty
import re
import select
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from flowfoundry.workspace.cli import layout, tui

REPO_ROOT = Path(__file__).resolve().parents[3]

# Redraw escape codes (erase line, cursor hide) interleave with the frame
# in a captured PTY stream; strip them before measuring alignment.
_CSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def box_widths(frame: str) -> list[int]:
    return [
        layout.display_width(line)
        for line in frame.split("\n")
        if line.startswith(("╭", "│", "╰"))
    ]


def make_entries(names: list[str], branches: list[str]) -> list[tui.ProjectEntry]:
    return [
        tui.ProjectEntry(
            path=Path("/home/user/Projects") / name,
            name=name,
            branch=branch,
            dot=tui.DOT_CLEAN,
            dot_kind="clean",
        )
        for name, branch in zip(names, branches)
    ]


# ---------------------------------------------------------------------------
# Display width semantics
# ---------------------------------------------------------------------------


class DisplayWidthTests(unittest.TestCase):
    def test_counts_ascii_cjk_emoji_and_combining(self):
        self.assertEqual(layout.display_width("abc"), 3)
        self.assertEqual(layout.display_width("项目"), 4)  # CJK = 2 cells
        self.assertEqual(layout.display_width("a项目b"), 6)
        self.assertEqual(layout.display_width("●"), 1)
        self.assertEqual(layout.display_width("é"), 1)  # combining = 0 cells
        self.assertEqual(layout.display_width("\x1b[32mok\x1b[0m"), 2)  # SGR stripped
        self.assertEqual(layout.display_width("⚠"), 1)
        self.assertEqual(layout.display_width("…"), 1)

    def test_truncate_only_when_needed_and_respects_cells(self):
        self.assertEqual(layout.truncate("main", 10), "main")  # fits → untouched
        self.assertEqual(layout.truncate("portfolio-migration", 9), "portfoli…")
        # the contract is "at most width cells", never beyond it
        for width in (6, 9, 12):
            result = layout.truncate("只读规划模式模式", width)
            self.assertLessEqual(layout.display_width(result), width)
            self.assertTrue(result.endswith("…"))
        self.assertEqual(layout.truncate("abc", 0), "")

    def test_pad_aligns_by_display_width(self):
        self.assertEqual(layout.pad("项目", 6), "项目  ")
        self.assertEqual(layout.pad("项目", 6, align="right"), "  项目")
        self.assertEqual(layout.display_width(layout.pad("项目", 6)), 6)


# ---------------------------------------------------------------------------
# Column planning tiers
# ---------------------------------------------------------------------------

ROWS = [
    ("ai-workflow-foundry", "portfolio-migration", "●"),
    ("meeting-media-auto", "master", "●"),
    ("hunan-university-motivation-ppt", "slides-2026", "●"),
]


class ColumnPlanTests(unittest.TestCase):
    def test_full_columns_when_space_allows(self):
        plan = layout.plan_project_columns(ROWS, 200)
        self.assertTrue(plan.branch_visible())
        self.assertTrue(plan.show_status)
        # natural widths: name 31, branch 19, marker 2, gaps 4, status 1 = 57
        self.assertEqual(plan.inner_width, 57)

    def test_truncates_branch_on_medium_terminal(self):
        plan = layout.plan_project_columns(ROWS, 50)
        self.assertTrue(plan.branch_visible())
        self.assertTrue(plan.show_status)
        self.assertLess(plan.branch_width, 19)
        self.assertEqual(plan.inner_width, 50)

    def test_hides_branch_on_narrow_terminal(self):
        plan = layout.plan_project_columns(ROWS, 42)
        self.assertFalse(plan.branch_visible())
        self.assertTrue(plan.show_status)

    def test_hides_status_on_very_narrow_terminal(self):
        plan = layout.plan_project_columns(ROWS, 30)
        self.assertFalse(plan.branch_visible())
        self.assertFalse(plan.show_status)
        self.assertEqual(plan.inner_width, 30)

    def test_truncates_names_as_last_resort(self):
        plan = layout.plan_project_columns(ROWS, 20)
        self.assertEqual(plan.name_width, 18)  # 20 - marker 2

    def test_render_project_row_keeps_columns_aligned(self):
        plan = layout.plan_project_columns(ROWS, 200)
        widths = {
            layout.display_width(layout.render_project_row(r, plan)) for r in ROWS
        }
        self.assertEqual(len(widths), 1)  # same cell count on every row
        line = layout.render_project_row(ROWS[1], plan, selected=True)
        self.assertTrue(line.startswith("› "))


# ---------------------------------------------------------------------------
# Box renderer
# ---------------------------------------------------------------------------


class RenderBoxTests(unittest.TestCase):
    def test_lines_share_one_width_and_hug_content(self):
        frame = layout.render_box(
            "CC", ["› FlowFoundry", "  System"], footer="q 退出", min_width=10
        )
        lines = frame.split("\n")
        self.assertEqual(len(lines), 5)  # top, 2 rows, bottom, footer
        self.assertEqual(len(set(box_widths(frame))), 1)
        self.assertEqual(
            box_widths(frame)[0], layout.display_width("› FlowFoundry") + 4
        )

    def test_truncates_title_and_footer_to_cap(self):
        # width_cap bounds the inner content; the box adds 2 border cells/side.
        cap = 20
        frame = layout.render_box(
            "a very long title that cannot possibly fit",
            ["row"],
            footer="a footer that is far too long to ever fit on one line",
            width_cap=cap,
        )
        self.assertIn("…", frame.split("\n")[0])  # title truncated
        self.assertIn("…", frame.split("\n")[-1])  # footer truncated
        for line in frame.split("\n"):
            self.assertLessEqual(layout.display_width(line), cap + 4)

    def test_minimum_width_and_cjk_rows(self):
        frame = layout.render_box("CC", ["项目"])
        self.assertEqual(len(set(box_widths(frame))), 1)
        self.assertGreaterEqual(box_widths(frame)[0], layout.MARKER_WIDTH + 4)


# ---------------------------------------------------------------------------
# Frame builders (same code path as the live TUI)
# ---------------------------------------------------------------------------


class FrameBuilderTests(unittest.TestCase):
    def test_projects_frame_aligned_at_every_width(self):
        entries = make_entries(
            ["ai-workflow-foundry", "meeting-media-auto", "meeting-media-desktop"],
            ["portfolio-migration", "master", "product"],
        )
        for width in (40, 60, 80, 160):
            frame = tui.build_projects_frame(
                title="CC · Projects",
                entries=entries,
                selected=1,
                term_size=(width, 24),
                footer="↑↓ 选择  Enter 打开  / 搜索  Tab 更多  q 退出",
            )
            widths = set(box_widths(frame))
            self.assertEqual(len(widths), 1, f"misaligned at {width} cols")
            self.assertLessEqual(widths.pop(), width)

    def test_projects_frame_never_truncates_when_space_exists(self):
        entries = make_entries(["Hunan-University-Motivation-PPT"], ["slides-2026"])
        frame = tui.build_projects_frame(
            title="CC · Projects",
            entries=entries,
            selected=0,
            term_size=(160, 24),
            footer="",
        )
        self.assertIn("Hunan-University-Motivation-PPT", frame)
        self.assertNotIn("…", frame)

    def test_scroll_counter_and_compact_viewport(self):
        entries = make_entries([f"project-{i:02d}" for i in range(20)], ["main"] * 20)
        frame = tui.build_projects_frame(
            title="CC · Projects",
            entries=entries,
            selected=15,
            term_size=(80, 24),
            footer="↑↓ 选择  Enter 打开",
        )
        self.assertIn("↑↓ 16/20", frame)
        row_lines = [l for l in frame.split("\n") if l.startswith("│")]
        self.assertLess(len(row_lines), 20)  # compact viewport
        self.assertTrue(any("› project-15" in l for l in row_lines))

    def test_detail_frame_expands_for_branch_and_right_aligns_status(self):
        items = [("Auto", "DeepSeek · plan"), ("DeepSeek", "")]
        frame = tui.build_detail_frame(
            project=Path("ai-workflow-foundry"),
            branch="portfolio-migration",
            dot=tui.DOT_CLEAN,
            dot_kind="clean",
            items=items,
            selected=0,
            term_size=(120, 24),
            footer="",
        )
        self.assertIn("portfolio-migration", frame)
        self.assertNotIn("…", frame)
        line1 = frame.split("\n")[1]
        self.assertTrue(line1.rstrip(" │").endswith("● clean"))  # hugs the border
        self.assertEqual(len(set(box_widths(frame))), 1)

    def test_detail_frame_shrinks_branch_on_narrow_terminal(self):
        items = [("Auto", "DeepSeek · plan")]
        frame = tui.build_detail_frame(
            project=Path("ai-workflow-foundry"),
            branch="feature/very-long-branch-name-for-media-sync",
            dot=tui.DOT_CLEAN,
            dot_kind="clean",
            items=items,
            selected=0,
            term_size=(50, 24),
            footer="",
        )
        widths = set(box_widths(frame))
        self.assertEqual(len(widths), 1)
        self.assertLessEqual(widths.pop(), 50)
        self.assertIn("● clean", frame.split("\n")[1])

    def test_list_frame_aligns_cjk_metadata_columns(self):
        frame = tui.build_list_frame(
            title="项目 · Claude",
            items=[
                ("Manual", "default"),
                ("acceptEdits", "acceptEdits"),
                ("plan", "只读规划"),
                ("auto", "自动执行"),
            ],
            selected=2,
            term_size=(100, 24),
            footer="",
        )
        self.assertEqual(len(set(box_widths(frame))), 1)
        rows = [l for l in frame.split("\n") if l.startswith("│")]
        # both CJK metas share one column position
        self.assertEqual(rows[2].find("只读规划"), rows[3].find("自动执行"))


# ---------------------------------------------------------------------------
# Auto mode state
# ---------------------------------------------------------------------------


class AutoConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=REPO_ROOT / ".test-tmp")
        Path(self.temp.name).mkdir(parents=True, exist_ok=True)
        self.state_file = Path(self.temp.name) / "auto-config.json"

    def tearDown(self):
        self.temp.cleanup()

    def test_roundtrip_and_resolution(self):
        project = Path("/home/user/Projects/demo")
        avail_true = patch.object(
            tui, "provider_availability", lambda: {"c": True, "d": True, "o": True}
        )
        with patch.object(tui, "AUTO_CONFIG_FILE", self.state_file):
            # Nothing remembered → first available provider, safe default.
            with patch.object(
                tui, "provider_availability", lambda: {"c": True, "d": True, "o": False}
            ):
                self.assertEqual(tui.resolve_auto(project), ("c", "p"))
            # Remember a launch and it wins, with its mode.
            tui._record_launch(project, "o", "m")
            with avail_true:
                self.assertEqual(tui.resolve_auto(project), ("o", "m"))
            # Corrupted state file falls back instead of crashing.
            self.state_file.write_text("{not json", encoding="utf-8")
            self.assertEqual(tui.load_auto_config(), {})
            self.assertEqual(tui.resolve_auto(project), ("c", "p"))

    def test_skips_unavailable_remembered_provider(self):
        project = Path("/home/user/Projects/demo")
        with patch.object(tui, "AUTO_CONFIG_FILE", self.state_file):
            tui._record_launch(project, "o", "m")
            # Codex disappears → fall back to the first available provider.
            with patch.object(
                tui, "provider_availability", lambda: {"c": True, "d": False, "o": False}
            ):
                provider, mode = tui.resolve_auto(project)
        self.assertEqual(provider, "c")
        self.assertEqual(mode, "p")  # safe default for the new provider


class ViewportTests(unittest.TestCase):
    def test_window_follows_selection_and_clamps(self):
        self.assertEqual(tui._window(20, 0, 8), (0, 8))
        self.assertEqual(tui._window(20, 12, 8), (5, 8))
        self.assertEqual(tui._window(20, 19, 8), (12, 8))
        self.assertEqual(tui._window(5, 2, 8), (0, 5))


# ---------------------------------------------------------------------------
# PTY smoke test — the real interactive loop, fed real keystrokes
# ---------------------------------------------------------------------------


@unittest.skipIf(sys.platform == "win32", "POSIX pty only")
class PtySmokeTests(unittest.TestCase):
    def test_renders_aligned_and_quits_on_q(self):
        # Outside the repository: cwd inside a git repo would hit the
        # fast-path and skip the projects screen this test drives.
        with tempfile.TemporaryDirectory() as temp:
            projects = Path(temp) / "Projects"
            projects.mkdir()
            for name in ("alpha", "bravo", "charlie"):
                (projects / name).mkdir()
                subprocess.run(
                    ["git", "-C", str(projects / name), "init"],
                    capture_output=True,
                    check=False,
                )

            script = (
                "import sys; sys.path.insert(0, %r)\n"
                "from pathlib import Path\n"
                "from flowfoundry.workspace.cli import tui\n"
                "tui.launcher.PROJECTS_ROOT = Path(%r)\n"
                "sys.exit(tui.tui_main())\n"
                % (str(REPO_ROOT / "src"), str(projects))
            )
            master, slave = pty.openpty()
            proc = subprocess.Popen(
                [sys.executable, "-c", script],
                stdin=slave,
                stdout=slave,
                stderr=slave,
                env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
                cwd=str(temp),
                close_fds=True,
            )
            os.close(slave)

            output = b""
            sent_q = False
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline and proc.poll() is None:
                readable, _, _ = select.select([master], [], [], 0.2)
                if readable:
                    try:
                        chunk = os.read(master, 4096)
                    except OSError:  # EIO: slave closed, child exited
                        break
                    output += chunk
                    if b"CC \xc2\xb7 Projects" in output and not sent_q:
                        os.write(master, b"q")
                        sent_q = True
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                raise
            finally:
                os.close(master)

            self.assertEqual(proc.returncode, 0)
            text = output.decode("utf-8", errors="replace")
            self.assertIn("╭─ CC · Projects", text)
            self.assertIn("alpha", text)
            self.assertIn("charlie", text)
            # the rendered frame is aligned: every box line the same width
            clean = [_CSI_RE.sub("", l) for l in text.splitlines()]
            box_lines = [l for l in clean if l.startswith(("╭", "│", "╰"))]
            self.assertEqual(len({layout.display_width(l) for l in box_lines}), 1)


if __name__ == "__main__":
    unittest.main()

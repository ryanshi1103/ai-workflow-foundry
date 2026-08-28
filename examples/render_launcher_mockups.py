"""Render the six adaptive-layout scenarios for the cc launcher.

Every scenario goes through the exact frame builders the live TUI uses
(``flowfoundry.workspace.cli.tui``), then a verifier checks the layout
contracts:

* every box line (top border, rows, bottom border) has equal display width
* the box never exceeds the terminal width
* full names are never truncated when space exists
* column degradation follows the tier order (branch → status → name)

Exit code 0 means all scenarios verified.  The rendered examples are also
written to ``docs/launcher-layout-examples.md``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flowfoundry.workspace.cli import layout, tui  # noqa: E402

DOCS_TARGET = Path(__file__).resolve().parents[1] / "docs" / "launcher-layout-examples.md"

FOOTER_PROJECTS = "↑↓ 选择  Enter 打开  / 搜索  Tab 更多  q 退出"
FOOTER_DETAIL = "↑↓ 选择  Enter 启动  Tab 项目  q 退出"
FOOTER_MODES = "↑↓ 选择  Enter 启动  Tab 返回  q 返回"


def entry(name: str, branch: str = "", dot_kind: str = "clean") -> tui.ProjectEntry:
    dot = tui.DOT_CLEAN if dot_kind in ("clean", "dirty") else tui.DOT_NONE
    return tui.ProjectEntry(
        path=Path("/workspace/projects") / name,
        name=name,
        branch=branch,
        dot=dot,
        dot_kind=dot_kind,
    )


# ---------------------------------------------------------------------------
# Scenario data
# ---------------------------------------------------------------------------

SHORT_NAMES = [
    entry("FlowFoundry", "main"),
    entry("System", "master"),
    entry("VPN", "main"),
]

LONG_NAMES = [
    entry("Hunan-University-Motivation-PPT", "slides-2026"),
    entry("ai-workflow-foundry", "portfolio-migration", "dirty"),
    entry("meeting-media-desktop", "product"),
    entry("personal-knowledge-base-v2", "main"),
]

MANY_NAMES = [
    entry("ai-workflow-foundry", "portfolio-migration", "dirty"),
    entry("meeting-media-auto", "master"),
    entry("meeting-media-desktop", "product"),
    entry("Hunan-University-Motivation-PPT", "slides-2026"),
    entry("personal-knowledge-base-v2", "main"),
    entry("family-budget-sheets", "main"),
    entry("garden-planner", "develop"),
    entry("chess-clock", "master"),
    entry("bike-repair-log", "main"),
    entry("leetcode-notes", "study"),
    entry("recipe-box", "main"),
    entry("travel-log", "master"),
    entry("home-automation", "feature/sensors"),
    entry("study-flashcards", "main"),
    entry("web-clipper", "main"),
    entry("backup-scripts", "master"),
    entry("podcast-notes", "main"),
    entry("workout-tracker", "main"),
    entry("journal-archive", "main"),
    entry("language-drills", "main"),
]


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


class VerificationError(AssertionError):
    pass


def verify_box(frame: str, term_width: int, scenario: str) -> None:
    lines = frame.split("\n")
    box_lines = [l for l in lines if l.startswith(("╭", "│", "╰"))]
    if not box_lines:
        raise VerificationError(f"{scenario}: no box lines rendered")
    widths = {layout.display_width(l) for l in box_lines}
    if len(widths) != 1:
        raise VerificationError(
            f"{scenario}: box lines not aligned, widths={sorted(widths)}:\n" + frame
        )
    box_width = widths.pop()
    if box_width > term_width:
        raise VerificationError(
            f"{scenario}: box {box_width} exceeds terminal {term_width}"
        )
    for line in lines:
        if layout.display_width(line) > term_width:
            raise VerificationError(
                f"{scenario}: line exceeds terminal: {line!r}"
            )


def main() -> int:
    sections: list[tuple[str, str]] = []
    problems: list[str] = []

    def check(scenario: str, frame: str, term_width: int) -> None:
        try:
            verify_box(frame, term_width, scenario)
            sections.append((scenario, frame))
            print(f"VERIFIED  {scenario}")
        except VerificationError as exc:
            problems.append(str(exc))
            print(f"FAILED    {scenario}: {exc}")
            print(frame)

    # 1. Short names — the box hugs the content.
    frame = tui.build_projects_frame(
        title="CC",
        entries=SHORT_NAMES,
        selected=0,
        term_size=(100, 24),
        footer=FOOTER_PROJECTS,
    )
    check("1. short names (100×24)", frame, 100)

    # 2. Very long names on a wide terminal — no truncation at all.
    frame = tui.build_projects_frame(
        title="CC · Projects",
        entries=LONG_NAMES,
        selected=0,
        term_size=(160, 24),
        footer=FOOTER_PROJECTS,
    )
    check("2. very long names, wide (160×24)", frame, 160)

    # 3. Narrow 80-column terminal — branch column truncates, stays aligned.
    frame = tui.build_projects_frame(
        title="CC · Projects",
        entries=LONG_NAMES,
        selected=0,
        term_size=(80, 24),
        footer=FOOTER_PROJECTS,
    )
    check("3. narrow 80-col terminal", frame, 80)

    # 3b. Even narrower — branch column disappears, then status.
    for width, label in ((45, "3b. 45-col: branch hidden"), (30, "3c. 30-col: status hidden")):
        frame = tui.build_projects_frame(
            title="CC",
            entries=LONG_NAMES,
            selected=0,
            term_size=(width, 24),
            footer="Enter 打开  q 退出",
        )
        check(label, frame, width)

    # 4. Wide terminal with the full list.
    frame = tui.build_projects_frame(
        title="CC · Projects",
        entries=MANY_NAMES[:5],
        selected=2,
        term_size=(160, 24),
        footer=FOOTER_PROJECTS,
    )
    check("4. wide terminal, full columns (160×24)", frame, 160)

    # 5. Only three projects — no reserved empty rows.
    frame = tui.build_projects_frame(
        title="CC",
        entries=SHORT_NAMES,
        selected=1,
        term_size=(100, 40),
        footer=FOOTER_PROJECTS,
    )
    check("5. only 3 projects (100×40)", frame, 100)

    # 6. 15+ projects — compact scrolling viewport with a scroll counter.
    frame = tui.build_projects_frame(
        title="CC · Projects",
        entries=MANY_NAMES,
        selected=12,
        term_size=(80, 24),
        footer="↑↓ 选择  Enter 打开  / 搜索  Tab 更多  q 退出",
    )
    check("6. 20 projects, scrolling viewport (80×24)", frame, 80)

    # Project detail — branch left, status right-aligned, Auto row.
    items = [
        ("Auto", "DeepSeek · plan"),
        ("Codex", "不可用"),
        ("DeepSeek", ""),
        ("Claude", ""),
    ]
    frame = tui.build_detail_frame(
        project=Path("ai-workflow-foundry"),
        branch="portfolio-migration",
        dot=tui.DOT_CLEAN,
        dot_kind="clean",
        items=items,
        selected=0,
        term_size=(120, 24),
        footer=FOOTER_DETAIL,
    )
    check("detail screen (120×24)", frame, 120)

    # Detail on a narrow terminal — the branch slot shrinks, status survives.
    frame = tui.build_detail_frame(
        project=Path("ai-workflow-foundry"),
        branch="feature/very-long-branch-name-for-media-sync",
        dot=tui.DOT_CLEAN,
        dot_kind="clean",
        items=items,
        selected=0,
        term_size=(60, 24),
        footer=FOOTER_DETAIL,
    )
    check("detail screen, narrow (60×24)", frame, 60)

    # Permission screen — label + description columns.
    frame = tui.build_list_frame(
        title="ai-workflow-foundry · Claude",
        items=[
            ("Manual", "default"),
            ("acceptEdits", "acceptEdits"),
            ("plan", "只读规划"),
            ("auto", "自动执行"),
            ("bypass", "完全访问"),
        ],
        selected=2,
        term_size=(100, 24),
        footer=FOOTER_MODES,
        warn_indexes=frozenset({4}),
    )
    check("permission screen (100×24)", frame, 100)

    # Line input.
    frame = tui.build_input_frame(
        title="CC · 新建项目",
        prompt="名称",
        buffer="meeting-media-auto",
        cursor=5,
        term_size=(80, 24),
        footer="Enter 确认  Esc 取消",
    )
    check("line input (80×24)", frame, 80)

    # ------------------------------------------------------------------ docs
    md_lines = [
        "# CC Launcher — Adaptive Layout Examples",
        "",
        "Rendered by `examples/render_launcher_mockups.py` through the exact",
        "frame builders the live TUI uses (`flowfoundry.workspace.cli.tui`).",
        "Every scenario is machine-verified: all box lines share one display",
        "width (CJK-aware), nothing exceeds the terminal, and degradation",
        "follows the tier order (truncate branch → hide branch → hide status",
        "→ truncate name).",
        "",
    ]
    for scenario, frame in sections:
        md_lines.append(f"## {scenario}")
        md_lines.append("")
        md_lines.append("```")
        md_lines.append(frame)
        md_lines.append("```")
        md_lines.append("")
    DOCS_TARGET.write_text("\n".join(md_lines), encoding="utf-8")

    if problems:
        print(f"\n{len(problems)} scenario(s) FAILED verification")
        return 1
    print(f"\nAll {len(sections)} scenarios verified → {DOCS_TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

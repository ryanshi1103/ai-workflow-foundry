"""Render and verify representative Classic CC Auto states.

Every example uses the production frame builders in ``auto_ui``. Pass
``--write`` to refresh ``docs/auto-ui-examples.md`` after visual review.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flowfoundry.workspace.cli import auto_ui, layout  # noqa: E402


def scenarios() -> list[tuple[str, tuple[int, int], str]]:
    project = Path("ai-workflow-foundry")
    cjk = "检查这个项目并把今天最值得完成的事情做完，同时保留现有的经典 CC 启动体验。"
    english = (
        "Inspect the current project, identify the most important usability "
        "problem, fix it, and verify the full launcher flow without changing "
        "manual provider behavior."
    )
    return [
        (
            "1. empty question · 80×24",
            (80, 24),
            auto_ui.build_auto_question_frame(
                project=project,
                permission_name="项目内自动修改",
                buffer="",
                cursor=0,
                term_size=(80, 24),
            ),
        ),
        (
            "2. long CJK question · 80×24",
            (80, 24),
            auto_ui.build_auto_question_frame(
                project=project,
                permission_name="项目内自动修改",
                buffer=cjk,
                cursor=len(cjk),
                term_size=(80, 24),
            ),
        ),
        (
            "3. long English question · 120×30",
            (120, 30),
            auto_ui.build_auto_question_frame(
                project=project,
                permission_name="手动确认",
                buffer=english,
                cursor=len(english),
                term_size=(120, 30),
            ),
        ),
        (
            "4. running · 80×24",
            (80, 24),
            auto_ui.build_auto_running_frame(
                project=project,
                permission_name="项目内自动修改",
                goal="修掉当前最影响使用的问题，并运行相关测试。",
                phase="验证结果",
                elapsed_seconds=18,
                term_size=(80, 24),
            ),
        ),
        (
            "5. completed · 80×24",
            (80, 24),
            auto_ui.build_auto_result_frame(
                project=project,
                permission_name="项目内自动修改",
                result=auto_ui.AutoResult(
                    "PASS",
                    "修掉当前最影响使用的问题。",
                    "已修复 Auto 输入界面的视觉断层，并保留原有启动器和手动 provider 路径。",
                    "通过 4 项确定性验证；3 个项目路径有变化",
                    "无",
                ),
                term_size=(80, 24),
            ),
        ),
        (
            "6. partial · 80×18",
            (80, 18),
            auto_ui.build_auto_result_frame(
                project=project,
                permission_name="手动确认",
                result=auto_ui.AutoResult(
                    "PARTIAL",
                    "研究最适合的发布路径。",
                    "已经完成候选方案比较，但来源的新鲜度仍需要人工判断。",
                    "已有结果，但确定性验证尚不充分",
                    "确认最终发布时间",
                ),
                term_size=(80, 18),
            ),
        ),
        (
            "7. unknown · 80×18",
            (80, 18),
            auto_ui.build_auto_result_frame(
                project=project,
                permission_name="只读规划",
                result=auto_ui.AutoResult(
                    "UNKNOWN",
                    "检查项目现在是否可以发布。",
                    "现有记录不足以确认发布条件已经全部满足。",
                    "没有足够证据确认已经完成",
                    "确认外部发布条件",
                ),
                term_size=(80, 18),
            ),
        ),
        (
            "8. narrow + long project · 42×14",
            (42, 14),
            auto_ui.build_auto_result_frame(
                project=Path("a-very-long-project-name-for-founder-work"),
                permission_name="只读规划",
                result=auto_ui.AutoResult(
                    "UNKNOWN",
                    "检查项目现在是否可以发布。",
                    "现有记录不足以确认发布条件已经全部满足。",
                    "没有足够证据确认已经完成",
                    "确认外部发布条件",
                ),
                term_size=(42, 14),
            ),
        ),
    ]


def verify(frame: str, size: tuple[int, int], name: str) -> None:
    width, height = size
    lines = frame.splitlines()
    box = [line for line in lines if line.startswith(("╭", "│", "╰"))]
    widths = {layout.display_width(line) for line in box}
    if len(widths) != 1:
        raise AssertionError(f"{name}: box widths differ: {sorted(widths)}")
    if max(layout.display_width(line) for line in lines) > width:
        raise AssertionError(f"{name}: exceeds {width} columns")
    if len(lines) > height:
        raise AssertionError(f"{name}: exceeds {height} rows")


def main() -> int:
    rendered: list[str] = [
        "# Classic CC Auto — Native UI Examples",
        "",
        "These frames come from the same production builders used by the live TUI.",
        "",
    ]
    for name, size, frame in scenarios():
        verify(frame, size, name)
        print(f"VERIFIED  {name}")
        print(frame)
        print()
        rendered.extend((f"## {name}", "", "```text", frame, "```", ""))
    if "--write" in sys.argv[1:]:
        target = ROOT / "docs" / "auto-ui-examples.md"
        target.write_text("\n".join(rendered), encoding="utf-8")
        print(f"WROTE     {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

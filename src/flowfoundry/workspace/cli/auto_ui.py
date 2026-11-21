"""Native Classic CC question, running, and result screens for Auto mode.

The backend remains FlowFoundry's existing ask/goal path.  This module is a
thin TUI adapter over it: the same ``RawTerm`` lifecycle, rounded box renderer,
display-width rules, and footer vocabulary used by the launcher continue after
the Founder selects Auto.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...ask import ask_project
from ...daily import _is_question, ensure_project_state, latest_resumable_run
from ...goal_runner import run_goal
from ...permissions import session_permission
from .layout import display_width, pad, render_box, truncate, wrap_text
from .tui import (
    RawTerm,
    _SGR_BRIGHT,
    _SGR_CYAN,
    _SGR_GREEN,
    _SGR_YELLOW,
    _sgr,
    _term_size,
    colors_enabled,
    dim,
)

AUTO_BACK = "back"
AUTO_QUIT = "quit"

_ANSI_ESCAPE = re.compile(
    r"\x1b(?:\][^\x07]*(?:\x07|\x1b\\)|\[[0-?]*[ -/]*[@-~])"
)
_MARKDOWN_LINK = re.compile(r"\[([^\]]+)]\([^\n)]+\)")
_MARKDOWN_HEADING = re.compile(r"(?m)^#{1,6}\s+")
_MARKDOWN_CODE_FENCE = re.compile(r"(?m)^```[^\n]*$")
_BINARY_DIFF = re.compile(r"(?m)^diff -- [^\n]+\nBinary file changed\.\n?")

_STATUS_STYLE = {
    "READY": ("READY · 就绪", _SGR_GREEN),
    "RUNNING": ("RUNNING · 处理中", _SGR_CYAN),
    "PASS": ("PASS · 完成", _SGR_GREEN),
    "PARTIAL": ("PARTIAL · 部分完成", _SGR_YELLOW),
    "UNKNOWN": ("UNKNOWN · 需要确认", _SGR_CYAN),
    "FAIL": ("FAILED · 未完成", _SGR_YELLOW),
    "FAILED": ("FAILED · 未完成", _SGR_YELLOW),
}


@dataclass(frozen=True)
class AutoResult:
    """Founder-facing Worker report with evaluator metadata kept separate."""

    status: str
    goal: str
    result: str
    validation: str
    needs_you: str
    responsible_agent: str = "Codex"
    changed_files: tuple[str, ...] = ()
    diff: str = ""
    evidence: str = ""


def _safe_text(value: object, *, strip: bool = True) -> str:
    """Remove terminal control sequences before rendering backend text."""
    text = _ANSI_ESCAPE.sub("", str(value or ""))
    text = text.replace("\t", "    ").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = "".join(
        ch if ch == "\n" or (ord(ch) >= 0x20 and ord(ch) != 0x7F) else " "
        for ch in text
    )
    return cleaned.strip() if strip else cleaned


def _present_text(value: object) -> str:
    """Turn common Markdown into calm terminal prose without raw link paths."""
    text = _safe_text(value)
    presented: list[str] = []
    fenced = False
    for line in text.splitlines():
        if _MARKDOWN_CODE_FENCE.fullmatch(line):
            fenced = not fenced
            continue
        if fenced:
            presented.append(line)
            continue
        line = _MARKDOWN_LINK.sub(r"\1", line)
        line = _MARKDOWN_HEADING.sub("", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        line = re.sub(r"__([^_]+)__", r"\1", line)
        line = re.sub(r"`([^`\n]+)`", r"\1", line)
        presented.append(line)
    return "\n".join(presented).strip()


def _inner_width(project: Path, term_width: int) -> tuple[int, int]:
    """Return (content width, launcher-compatible terminal cap)."""
    cap = max(term_width - 6, 10)
    preferred = min(76, max(48, term_width - 24))
    natural = max(
        preferred, display_width(project.name) + display_width(" · Auto") + 2
    )
    return min(cap, natural, 76), cap


def _body_budget(term_height: int) -> int:
    # top border + bottom border + one footer line
    return max(3, term_height - 3)


def _status_text(status: str, *, colors: bool, compact: bool = False) -> str:
    label, color = _STATUS_STYLE.get(
        status.upper(), (f"{status.upper()} · 状态未知", _SGR_CYAN)
    )
    if compact:
        label = label.rsplit(" · ", 1)[-1]
    return _sgr("● " + label, color, colors)


def _header_rows(
    *, inner: int, permission_name: str, status: str, colors: bool
) -> list[str]:
    right = _status_text(status, colors=colors, compact=inner < 28)
    right_width = display_width(right)
    left = "  FlowFoundry"
    left_width = max(inner - right_width - 2, 0)
    first = pad(truncate(left, left_width), inner - right_width) + right
    permission = "  权限  " + _safe_text(permission_name)
    return [first, dim(truncate(permission, inner), colors)]


def _title(project: Path) -> str:
    return f"{_safe_text(project.name)} · Auto"


def _question_footer(term_width: int) -> str:
    if term_width < 54:
        return "Enter 提交  Tab 返回  Esc 退出"
    return "Enter 提交  /continue 继续  Tab 返回  Esc 退出"


def build_auto_question_frame(
    *,
    project: Path,
    permission_name: str,
    buffer: str,
    cursor: int,
    term_size: tuple[int, int],
    colors: bool = False,
) -> str:
    """Render the editable Auto goal surface with CJK-aware visual wrapping."""
    term_width, term_height = term_size
    inner, cap = _inner_width(project, term_width)
    budget = _body_budget(term_height)
    rows = _header_rows(
        inner=inner,
        permission_name=permission_name,
        status="READY",
        colors=colors,
    )

    cursor = min(max(cursor, 0), len(buffer))
    shown = _safe_text(
        buffer[:cursor] + "▊" + buffer[cursor:], strip=False
    ) or "▊"
    input_lines = wrap_text(shown, max(inner - 4, 1))

    # Header (2) + label (1) are essential. Blank separators and the hint are
    # progressively omitted on short terminals; the cursor's tail stays in view.
    optional_rows = 2 if budget >= 7 else 0
    input_budget = max(1, budget - len(rows) - 1 - optional_rows)
    if len(input_lines) > input_budget:
        input_lines = input_lines[-input_budget:]
        input_lines[0] = truncate("…" + input_lines[0], max(inner - 4, 1))

    if budget >= 7:
        rows.append("")
    rows.append(_sgr("  目标", _SGR_BRIGHT, colors))
    rows.extend("  " + line for line in input_lines)
    if budget >= 7 and len(rows) + 2 <= budget:
        rows.extend(
            [
                "",
                dim("  输入问题，或描述想完成的事情", colors),
            ]
        )
    rows = rows[:budget]
    return render_box(
        _title(project),
        [pad(row, inner) for row in rows],
        footer=dim(_question_footer(term_width), colors),
        width_cap=cap,
    )


def _running_footer(term_width: int) -> str:
    return "FlowFoundry 正在安全执行" if term_width < 46 else "FlowFoundry 正在安全执行，请稍候"


def build_auto_running_frame(
    *,
    project: Path,
    permission_name: str,
    goal: str,
    phase: str,
    elapsed_seconds: float,
    term_size: tuple[int, int],
    colors: bool = False,
) -> str:
    """Render truthful activity without logs, fake percentages, or internals."""
    term_width, term_height = term_size
    inner, cap = _inner_width(project, term_width)
    budget = _body_budget(term_height)
    rows = _header_rows(
        inner=inner,
        permission_name=permission_name,
        status="RUNNING",
        colors=colors,
    )
    remaining = max(budget - len(rows), 1)
    goal_lines = wrap_text(_safe_text(goal), max(inner - 4, 1))
    fixed = 3  # goal label, phase, elapsed/needs-you
    goal_budget = max(1, remaining - fixed - (2 if remaining >= 7 else 0))
    goal_lines = goal_lines[:goal_budget]
    if remaining >= 7:
        rows.append("")
    rows.append(_sgr("  当前目标", _SGR_BRIGHT, colors))
    rows.extend("  " + line for line in goal_lines)
    if remaining >= 7 and len(rows) < budget:
        rows.append("")
    if len(rows) < budget:
        rows.append("  阶段  " + truncate(_safe_text(phase), max(inner - 8, 1)))
    if len(rows) < budget:
        elapsed = max(0, int(elapsed_seconds))
        rows.append(dim(f"  已用  {elapsed} 秒    需要你  无", colors))
    return render_box(
        _title(project),
        [pad(row, inner) for row in rows[:budget]],
        footer=dim(_running_footer(term_width), colors),
        width_cap=cap,
    )


def _summary_text(text: str, *, details: bool, limit: int = 12_000) -> str:
    clean = _safe_text(text) or "没有产生可显示的结果。"
    if details or len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


def _compact_diff(text: str, *, details: bool) -> str:
    clean = _safe_text(text)
    if details or len(clean) <= 4_000:
        return clean
    return clean[:4_000].rstrip() + "\n… 按 d 查看更长差异 …"


def _important_diff(value: object) -> str:
    return _BINARY_DIFF.sub("", _safe_text(value)).strip()


def _section(label: str, text: str, width: int, colors: bool) -> list[str]:
    rows = [_sgr("  " + label, _SGR_BRIGHT, colors)]
    rows.extend("  " + line for line in wrap_text(_safe_text(text), max(width - 4, 1)))
    return rows


def _result_footer(term_width: int, *, details: bool, position: str) -> str:
    detail_label = "摘要" if details else "详情"
    if term_width < 58:
        base = f"↑↓  Enter 新目标  d {detail_label}  Tab 返回"
    else:
        base = f"↑↓ {position}  Enter 新目标  d {detail_label}  Tab 返回  q 退出"
    return base


def _render_auto_result(
    *,
    project: Path,
    permission_name: str,
    result: AutoResult,
    term_size: tuple[int, int],
    scroll: int,
    details: bool,
    colors: bool,
) -> tuple[str, int]:
    term_width, term_height = term_size
    inner, cap = _inner_width(project, term_width)
    budget = _body_budget(term_height)
    header = _header_rows(
        inner=inner,
        permission_name=permission_name,
        status=result.status,
        colors=colors,
    )
    header.append(
        _sgr(
            "  负责 Agent  " + truncate(_safe_text(result.responsible_agent), max(inner - 14, 1)),
            _SGR_BRIGHT,
            colors,
        )
    )
    content: list[str] = []
    content.extend(
        _section(
            f"{_safe_text(result.responsible_agent)} 的报告",
            _summary_text(result.result, details=details),
            inner,
            colors,
        )
    )
    if result.changed_files:
        content.append("")
        content.extend(
            _section(
                "修改的文件",
                "\n".join(f"• {path}" for path in result.changed_files),
                inner,
                colors,
            )
        )
    if result.diff:
        content.append("")
        content.extend(
            _section(
                "重要代码 / 差异",
                _compact_diff(result.diff, details=details),
                inner,
                colors,
            )
        )
    content.append("")
    content.extend(_section("验证", result.validation, inner, colors))
    if result.evidence:
        content.append("")
        content.extend(_section("证据", result.evidence, inner, colors))
    content.append("")
    content.extend(_section("需要你", result.needs_you or "无", inner, colors))
    content.append("")
    content.extend(_section("目标", result.goal, inner, colors))

    viewport = max(1, budget - len(header))
    max_scroll = max(0, len(content) - viewport)
    scroll = min(max(scroll, 0), max_scroll)
    visible = content[scroll : scroll + viewport]
    position = (
        f"{scroll + 1}/{max_scroll + 1}" if max_scroll else "全部"
    )
    frame = render_box(
        _title(project),
        [pad(row, inner) for row in [*header, *visible]],
        footer=dim(
            _result_footer(term_width, details=details, position=position), colors
        ),
        width_cap=cap,
    )
    return frame, max_scroll


def build_auto_result_frame(
    *,
    project: Path,
    permission_name: str,
    result: AutoResult,
    term_size: tuple[int, int],
    scroll: int = 0,
    details: bool = False,
    colors: bool = False,
) -> str:
    """Pure result-frame builder used by tests, mockups, and the live TUI."""
    frame, _ = _render_auto_result(
        project=project,
        permission_name=permission_name,
        result=result,
        term_size=term_size,
        scroll=scroll,
        details=details,
        colors=colors,
    )
    return frame


def _question_loop(
    term: RawTerm, project: Path, permission_name: str
) -> str | None:
    buffer = ""
    cursor = 0
    colors = colors_enabled()
    while True:
        term.redraw(
            build_auto_question_frame(
                project=project,
                permission_name=permission_name,
                buffer=buffer,
                cursor=cursor,
                term_size=_term_size(),
                colors=colors,
            )
        )
        key = term.read_key()
        if key == "enter":
            if buffer.strip():
                return buffer.strip()
            continue
        if key == "tab":
            return AUTO_BACK
        if key in ("esc", "eof"):
            return None
        if key == "backspace":
            if cursor > 0:
                buffer = buffer[: cursor - 1] + buffer[cursor:]
                cursor -= 1
        elif key == "left":
            cursor = max(cursor - 1, 0)
        elif key == "right":
            cursor = min(cursor + 1, len(buffer))
        elif key == "home":
            cursor = 0
        elif len(key) == 1 and key.isprintable():
            buffer = buffer[:cursor] + key + buffer[cursor:]
            cursor += 1


def _result_loop(
    term: RawTerm,
    project: Path,
    permission_name: str,
    result: AutoResult,
) -> str:
    scroll = 0
    details = False
    colors = colors_enabled()
    while True:
        frame, max_scroll = _render_auto_result(
            project=project,
            permission_name=permission_name,
            result=result,
            term_size=_term_size(),
            scroll=scroll,
            details=details,
            colors=colors,
        )
        scroll = min(scroll, max_scroll)
        term.redraw(frame)
        key = term.read_key()
        if key in ("up", "k"):
            scroll = max(scroll - 1, 0)
        elif key in ("down", "j"):
            scroll = min(scroll + 1, max_scroll)
        elif key == "pageup":
            scroll = max(scroll - 5, 0)
        elif key == "pagedown":
            scroll = min(scroll + 5, max_scroll)
        elif key == "d":
            details = not details
            scroll = 0
        elif key == "enter":
            return "new"
        elif key == "tab":
            return AUTO_BACK
        elif key in ("esc", "q", "eof"):
            return AUTO_QUIT


def _phase_for_progress(message: str) -> str:
    lowered = message.casefold()
    if lowered.startswith("checking:") or "check " in lowered:
        return "验证结果"
    if "turn complete" in lowered:
        return "整理结果"
    if "executor session ready" in lowered:
        return "执行目标"
    return "执行与检查"


def _draw_running(
    term: RawTerm,
    *,
    project: Path,
    permission_name: str,
    goal: str,
    phase: str,
    started: float,
) -> None:
    term.redraw(
        build_auto_running_frame(
            project=project,
            permission_name=permission_name,
            goal=goal,
            phase=phase,
            elapsed_seconds=time.monotonic() - started,
            term_size=_term_size(),
            colors=colors_enabled(),
        )
    )


def _ask_result(value: dict[str, Any]) -> AutoResult:
    sources = len(value.get("sources", ()))
    status = str(value.get("status", "UNKNOWN")).upper()
    answer = _present_text(value.get("answer"))
    answer = re.sub(
        r"\s*\[\d+;\s*(?:ACCEPTED|CANDIDATE)\]", "", answer
    )
    answer = answer.removeprefix("Recorded context (selected excerpts):").strip()
    disclaimer = (
        "These excerpts may not fully answer the question; completeness and "
        "conflicts are not verified. CANDIDATE material is unaccepted."
    )
    answer = answer.removesuffix(disclaimer).strip()
    if answer.startswith("No directly matching answer found"):
        answer = (
            "找到了相关项目记录，但没有直接匹配的答案。"
            if sources
            else "项目记录中没有找到直接匹配的答案。"
        )
    validation = (
        f"找到 {sources} 条项目记录；回答的完整性尚未验证"
        if sources
        else "没有找到直接匹配的项目记录"
    )
    needs = (
        "如需定论，请核对项目记录"
        if sources
        else "换一种问法，或先补充项目记录"
    )
    source_lines = []
    for source in value.get("sources", ()):
        if isinstance(source, dict):
            label = source.get("source") or source.get("path") or source.get("title")
            if label:
                source_lines.append(f"• {_safe_text(label)}")
    return AutoResult(
        status=status,
        goal=_safe_text(value.get("question")),
        result=answer,
        validation=validation,
        needs_you=needs,
        responsible_agent="项目记录检索",
        evidence="\n".join(source_lines[:8]),
    )


def _responsible_agent(value: dict[str, Any]) -> str:
    explicit = _safe_text(value.get("responsible_agent"))
    if explicit:
        return explicit
    executor = _safe_text(value.get("executor"))
    return {"codex": "Codex", "claude": "Claude", "deepseek": "DeepSeek"}.get(
        executor.casefold(), executor or "Agent"
    )


def _changed_paths(value: dict[str, Any]) -> tuple[str, ...]:
    changes = value.get("changes")
    changes = changes if isinstance(changes, dict) else {}
    paths = changes.get("paths")
    if not isinstance(paths, list):
        return ()
    cleaned = []
    for raw in paths:
        path = _safe_text(raw)
        # Read schema-v2 porcelain entries without preserving Git status flags.
        if len(path) >= 4 and path[2] == " ":
            path = path[3:]
        if path and path not in cleaned:
            cleaned.append(path)
    return tuple(
        sorted(
            cleaned,
            key=lambda path: (
                "__pycache__" in Path(path).parts
                or path.endswith((".pyc", ".pyo")),
                path,
            ),
        )
    )


def _verification_evidence(verification: dict[str, Any]) -> str:
    rows: list[str] = []
    evidence = verification.get("evidence")
    if not isinstance(evidence, list):
        return ""
    for item in evidence:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        if kind == "command":
            exit_code = item.get("exit_code")
            outcome = "PASS" if exit_code == 0 else ("ERROR" if exit_code is None else "FAIL")
            command = _safe_text(item.get("command"))
            if command:
                rows.append(f"• {outcome} · {command}")
        elif kind == "sources":
            rows.append(f"• 可追溯来源：{item.get('count', 0)}")
        elif kind == "executor" and item.get("succeeded") is False:
            rows.append("• Worker 执行未成功完成")
        elif kind:
            rows.append(f"• {_safe_text(kind)}")
    return "\n".join(rows)


def _goal_result(value: dict[str, Any]) -> AutoResult:
    status = str(value.get("status", "UNKNOWN")).upper()
    verification = value.get("verification")
    verification = verification if isinstance(verification, dict) else {}
    evidence = verification.get("evidence")
    evidence = evidence if isinstance(evidence, list) else []
    passed_checks = sum(
        1
        for item in evidence
        if isinstance(item, dict)
        and item.get("acceptance_check")
        and item.get("exit_code") == 0
    )
    changed = value.get("changes")
    changed = changed if isinstance(changed, dict) else {}
    paths = _changed_paths(value)
    changed_count = len(paths)
    if status == "PASS":
        validation = (
            f"PASS · 通过 {passed_checks} 项确定性验证"
            if passed_checks
            else "PASS · 确定性验证通过"
        )
    elif status == "PARTIAL":
        validation = "PARTIAL · 已有结果，但确定性验证尚不充分"
    elif status in {"FAIL", "FAILED"}:
        validation = "FAIL · 执行或验证未通过"
    else:
        validation = "UNKNOWN · 没有足够证据确认已经完成"
    if changed_count:
        validation += f"；{changed_count} 个项目路径有变化"

    human = value.get("human")
    human = human if isinstance(human, dict) else {}
    needs = _safe_text(human.get("needs_you") or verification.get("needs_user"))
    needs = {
        "No deterministic acceptance check was available; confirm the result.": (
            "没有可用的确定性验收检查；请确认结果"
        ),
        "Repository changes exist, but no acceptance test was observed.": (
            "项目已有变化，但没有观察到验收测试"
        ),
        "Review the executor error.": "检查本地执行错误后重试",
        "A deterministic check failed.": "一项确定性检查未通过",
    }.get(needs, needs)
    return AutoResult(
        status=status,
        goal=_safe_text(value.get("goal")),
        result=_present_text(
            value.get("agent_response")
            or value.get("result")
            or value.get("final_message")
        ),
        validation=validation,
        needs_you=needs or "无",
        responsible_agent=_responsible_agent(value),
        changed_files=paths,
        diff=_important_diff(changed.get("diff")),
        evidence=_verification_evidence(verification),
    )


def _error_result(goal: str, error: Exception) -> AutoResult:
    return AutoResult(
        status="FAILED",
        goal=goal,
        result="任务未能完成。",
        validation="没有产生可接受的完成证据",
        needs_you=_safe_text(error) or "检查本地执行环境后重试",
        responsible_agent="Codex",
    )


def _wants_continue(text: str) -> bool:
    normalized = text.casefold().strip().rstrip("。.!！")
    return normalized in {"/continue", "继续上次的任务", "继续上一次任务"}


def run_auto_session(term: RawTerm, project: Path, permission_level: int) -> str:
    """Run Auto inside the existing Classic CC terminal lifecycle."""
    project = project.resolve()
    permission = session_permission(permission_level)
    permission_name = str(permission["name"])
    ensure_project_state(project)
    os.environ["CC_ACTIVE_PROJECT"] = str(project)
    os.environ["CC_PROJECT_MODE"] = "existing"

    while True:
        text = _question_loop(term, project, permission_name)
        if text == AUTO_BACK:
            return AUTO_BACK
        if text is None or text.casefold() in {"/quit", "/exit"}:
            return AUTO_QUIT

        if text.casefold() == "/status":
            action = _result_loop(
                term,
                project,
                permission_name,
                AutoResult(
                    status="READY",
                    goal="查看当前状态",
                    result="当前没有任务在运行，可以输入新的问题或目标。",
                    validation="界面与项目均已就绪",
                    needs_you="无",
                ),
            )
            if action != "new":
                return action
            continue

        resume: str | None = None
        goal = text
        if _wants_continue(text):
            resume = latest_resumable_run(project)
            goal = "继续上一次任务"
            if resume is None:
                action = _result_loop(
                    term,
                    project,
                    permission_name,
                    AutoResult(
                        status="UNKNOWN",
                        goal=goal,
                        result="没有找到可继续的项目任务。",
                        validation="未发现带有可恢复会话的项目记录",
                        needs_you="输入一个新目标",
                    ),
                )
                if action != "new":
                    return action
                continue

        started = time.monotonic()
        phase = "查找项目记录" if _is_question(goal) else "理解目标"
        _draw_running(
            term,
            project=project,
            permission_name=permission_name,
            goal=goal,
            phase=phase,
            started=started,
        )
        try:
            if _is_question(goal):
                presented = _ask_result(ask_project(project, goal))
            else:
                def progress(message: str) -> None:
                    _draw_running(
                        term,
                        project=project,
                        permission_name=permission_name,
                        goal=goal,
                        phase=_phase_for_progress(message),
                        started=started,
                    )

                _, value = run_goal(
                    goal,
                    root=project,
                    runs_root=project / ".flowfoundry" / "do",
                    read_only=bool(permission["read_only"]),
                    permission_level=int(permission["level"]),
                    resume=resume,
                    progress=progress,
                )
                presented = _goal_result(value)
        except KeyboardInterrupt:
            raise
        except Exception as exc:  # present an intentional FAILED state, not a traceback
            presented = _error_result(goal, exc)

        action = _result_loop(term, project, permission_name, presented)
        if action != "new":
            return action

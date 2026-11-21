"""FlowFoundry goal session used by the classic ``cc`` launcher's Auto path.

This is deliberately a thin loop, not a second runtime: project questions and
goals are dispatched to the existing ``flowfoundry`` CLI after classic CC has
selected the project and session permission ceiling.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .permissions import SESSION_PERMISSION_CEILINGS, session_permission


def detect_project(start: Path | None = None) -> Path:
    """Resolve the current project without consulting global FlowFoundry state."""
    current = (start or Path.cwd()).expanduser().resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(current), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        root = result.stdout.strip()
        if root:
            return Path(root).resolve()
    except (OSError, subprocess.SubprocessError):
        pass
    return current


def ensure_project_state(root: Path) -> None:
    """Create only the two files needed for a first-use project."""
    ai = root / ".ai"
    ai.mkdir(exist_ok=True)
    state = ai / "PROJECT_STATE.md"
    latest = ai / "LATEST.md"
    if not state.exists():
        state.write_text(
            "# Project State\n\n"
            f"Project: {root.name}\n\n"
            "This project has no recorded FlowFoundry state yet.\n",
            encoding="utf-8",
        )
    if not latest.exists():
        latest.write_text(
            "# Latest Work\n\nNo substantial FlowFoundry work has been recorded yet.\n",
            encoding="utf-8",
        )


def _is_question(text: str) -> bool:
    lowered = text.casefold().strip()
    return (
        "?" in text
        or "？" in text
        or lowered.startswith(("what ", "why ", "where ", "how ", "which "))
        or any(token in text for token in ("什么", "为什么", "哪", "哪里", "怎么", "做到哪", "现状"))
    )


def _dispatch(root: Path, text: str) -> int:
    from .cli import main as flowfoundry_main

    args = ["ask" if _is_question(text) else "do", text, "--workspace", str(root)]
    return flowfoundry_main(args)


def latest_resumable_run(root: Path) -> str | None:
    """Return the newest valid project-local run that has a Codex thread."""
    candidates: list[tuple[str, str]] = []
    for result_path in (root / ".flowfoundry" / "do").glob("goal-*/result.json"):
        try:
            value = json.loads(result_path.read_text(encoding="utf-8"))
            if Path(str(value["project_root"])).resolve() != root.resolve():
                continue
            if not value.get("thread_id"):
                continue
            run_id = result_path.parent.name
            candidates.append((str(value.get("finished_at", "")), run_id))
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
            continue
    return max(candidates)[1] if candidates else None


def _choose_session_permission() -> dict[str, object] | None:
    """Keep the launcher's four permission ceilings, without model choice."""
    print("权限上限（本次会话）:")
    print("  1  只读规划")
    print("  2  项目内自动修改")
    print("  3  手动确认")
    print("  4  完全访问")
    print("  q  退出")
    options = {
        str(int(level)): dict(config)
        for level, config in SESSION_PERMISSION_CEILINGS.items()
    }
    while True:
        try:
            choice = input("请选择 (1/2/3/4/q): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if choice in {"q", "quit", "exit", "/quit", "/exit"}:
            return None
        if choice in options:
            return options[choice]
        print("无效选择，请重试。")


def _quick(prompt: str) -> int:
    """Run an explicitly non-project question without writing project state."""
    codex = os.environ.get("FLOWFOUNDRY_QUICK_EXECUTOR") or "codex"
    try:
        result = subprocess.run(
            [codex, "exec", "--json", "--sandbox", "read-only", "-"],
            input=prompt + "\n",
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Quick mode unavailable: {exc}", file=sys.stderr)
        return 2
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode:
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        return result.returncode
    return 0


def run(
    *,
    quick: bool = False,
    root: Path | None = None,
    permission_level: int | str | None = None,
) -> int:
    """Start the FlowFoundry goal loop, optionally with a launcher-set ceiling."""
    if quick:
        try:
            prompt = input("Quick question> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        return _quick(prompt) if prompt else 0

    project = detect_project(root)
    ensure_project_state(project)
    permission = (
        _choose_session_permission()
        if permission_level is None
        else session_permission(permission_level)
    )
    if permission is None:
        return 0
    print("FlowFoundry")
    print(f"Project: {project.name}")
    print(f"权限上限: {permission['name']}")
    print("Status: ready")
    print("\n输入目标或问题；输入 /status 查看状态，/quit 退出。\n")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not text:
            continue
        command = text.casefold()
        if command in {"/quit", "/exit", "q"}:
            return 0
        if command in {"/status", "status", "现在在干什么"}:
            from .cli import main as flowfoundry_main

            code = flowfoundry_main(["status", "--workspace", str(project)])
            if code:
                return code
            continue
        if command in {"/continue", "继续上次的任务"}:
            resume = latest_resumable_run(project)
            if resume is None:
                print("没有找到可继续的项目任务。")
                continue
            text = "继续上次的任务"
        else:
            resume = None
        if _is_question(text):
            code = _dispatch(project, text)
        else:
            from .cli import main as flowfoundry_main

            args = [
                "do",
                text,
                "--workspace",
                str(project),
                "--permission-level",
                str(permission["level"]),
            ]
            if permission["read_only"]:
                args.append("--read-only")
            if resume:
                args.extend(("--resume", resume))
            code = flowfoundry_main(args)
        if code and command.startswith("/"):
            return code


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--quick"]:
        return run(quick=True)
    return run()

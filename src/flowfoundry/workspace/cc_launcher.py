"""Python port of the ``cc`` unified launcher (Claude / DeepSeek / Codex).

Replaces the 1000-line bash script with a maintainable, testable Python
implementation.  Behaviour is intentionally identical so the daily user
experience does not change.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECTS_ROOT = Path.home() / "Projects"
RECENT_STATE_DIR = Path(
    os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
) / "cc-launcher"
RECENT_FILE = RECENT_STATE_DIR / "recent-projects"
TIMESTAMP_PATTERN = re.compile(
    r"^[0-9]{8}-[0-9]{6}-[a-z]+-[a-f0-9]{6}$"
)

# ---------------------------------------------------------------------------
# Helpers (ported 1:1 from bin/cc)
# ---------------------------------------------------------------------------

_is_remote = bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY"))


def is_timestamp_session_dir(name: str) -> bool:
    return bool(TIMESTAMP_PATTERN.match(name))


def has_git(path: Path) -> bool:
    try:
        subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            capture_output=True, timeout=5, check=True,
        )
        return True
    except Exception:
        return False


def has_ai_state(path: Path) -> bool:
    return (path / ".ai-session" / "project.json").is_file() or \
           (path / ".ai" / "project.json").is_file()


def project_indicators(path: Path) -> str:
    parts = []
    if has_git(path):
        parts.append("[Git]")
    else:
        parts.append("[非Git]")
    if has_ai_state(path):
        parts.append("[AI]")
    return " ".join(parts)


def project_picker_group(project_name: str) -> str:
    managed_file = Path(
        os.environ.get("CC_MANAGED_PROJECTS_FILE",
                       str(Path.home() / ".config" / "cc-projects" / "managed-projects"))
    )
    if not managed_file.is_file():
        return "primary"
    try:
        for line in managed_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if not parts or parts[0] != project_name:
                continue
            group = parts[1] if len(parts) > 1 else ""
            if group in ("managed", "archive"):
                return "managed"
            return "primary"
    except OSError:
        pass
    return "primary"


def add_to_recent(target_dir: Path) -> None:
    if not target_dir.is_dir():
        return
    name = target_dir.name
    if is_timestamp_session_dir(name):
        return
    target_s = str(target_dir)
    if "/.ai/sessions/" in target_s or "/.ai-session/sessions/" in target_s:
        return
    if not target_s.startswith(str(PROJECTS_ROOT)):
        return

    RECENT_STATE_DIR.mkdir(parents=True, exist_ok=True)

    entries: list[str] = []
    if RECENT_FILE.is_file():
        for line in RECENT_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line == target_s:
                continue
            if not Path(line).is_dir():
                continue
            existing_name = Path(line).name
            if is_timestamp_session_dir(existing_name):
                continue
            if "/.ai/sessions/" in line or "/.ai-session/sessions/" in line:
                continue
            entries.append(line)

    all_entries = [target_s] + entries
    RECENT_FILE.write_text("\n".join(all_entries[:20]) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Interactive menus
# ---------------------------------------------------------------------------

_input_fn: Callable[[str], str] = input  # injectable for tests
_prompt_closed = False


def _prompt(msg: str) -> str:
    global _prompt_closed
    _prompt_closed = False
    try:
        return _input_fn(msg).strip()
    except (EOFError, KeyboardInterrupt):
        _prompt_closed = True
        print()
        return ""


def _print_banner(title: str) -> None:
    print()
    print("╔══════════════════════════════════════════╗")
    for line in title.split("\n"):
        print(f"║  {line:<38}║")
    print("╚══════════════════════════════════════════╝")


def _show_remote_banner() -> None:
    if _is_remote:
        print()
        print("╔══════════════════════════════════════════════════════════╗")
        print("║  📱 SSH 远程会话                                        ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print("║  当前操作来自远程终端；全部启动器选项保持可用。         ║")
        print("║  完全访问模式需要额外输入 remote-yes。                  ║")
        print("╚══════════════════════════════════════════════════════════╝")


def _confirm_remote(mode_name: str) -> bool:
    if not _is_remote:
        return True
    print()
    print(f"远程高权限确认: {mode_name}")
    answer = _prompt("请输入 'remote-yes' 继续: ")
    if _prompt_closed:
        print("输入已关闭，已取消。")
        return False
    if answer != "remote-yes":
        print("远程高权限确认失败，已取消。")
        return False
    return True


def _choose_provider(project_dir: Path) -> str | None:
    print()
    _print_banner(f"Claude / DeepSeek / Codex 项目启动器\n\n项目: {project_dir}")
    print("║  选择工具:                               ║")
    print("║  c   Claude（Anthropic 原生）            ║")
    print("║  d   DeepSeek V4 Pro                     ║")
    print("║  o   OpenAI Codex（GPT-5.6 Sol）         ║")
    print("║  q   退出                                ║")
    print("╚══════════════════════════════════════════╝")
    print()
    choice = _prompt("请选择 (c/d/o/q): ").lower()
    if _prompt_closed:
        print("输入已关闭，已取消。")
        return "error"
    if choice == "q":
        print("已取消。")
        return None
    if choice in {"c", "d", "o"}:
        return choice
    print("无效选择，已取消。")
    return "error"


def _choose_permission_mode() -> dict | None:
    print()
    print("╔══════════════════════════════════════════╗")
    print("║  Claude / DeepSeek 全局项目启动器        ║")
    print("╠══════════════════════════════════════════╣")
    print("║  选择初始权限:                           ║")
    print("║  m   Manual                              ║")
    print("║  e   acceptEdits                         ║")
    print("║  p   plan (只分析，不修改)               ║")
    print("║  a   auto (自动执行)                     ║")
    print("║  b   bypassPermissions ⚠️                ║")
    print("║  q   返回                                ║")
    print("╚══════════════════════════════════════════╝")
    print()
    choice = _prompt("请选择 (m/e/p/a/b/q): ").lower()
    mode_map = {
        "m": ("default", "Manual", False),
        "e": ("acceptEdits", "acceptEdits", False),
        "p": ("plan", "plan (只分析)", False),
        "a": ("auto", "auto", False),
        "b": ("bypassPermissions", "bypassPermissions", True),
    }
    if choice == "q":
        return None  # signal: go back to provider selection
    if choice in mode_map:
        perm, name, bypass = mode_map[choice]
        return {"mode": perm, "name": name, "bypass": bypass}
    print("无效选择，已取消。")
    return {"error": True}


def _choose_codex_mode() -> dict | None:
    print()
    print("╔══════════════════════════════════════════╗")
    print("║  OpenAI Codex — GPT-5.6 Sol             ║")
    print("╠══════════════════════════════════════════╣")
    print("║  m   手动确认                            ║")
    print("║      workspace-write + on-request        ║")
    print("║  p   只读规划                            ║")
    print("║      read-only + never                   ║")
    print("║  a   项目内自动执行                      ║")
    print("║      workspace-write + never             ║")
    print("║  b   完全访问 ⚠                         ║")
    print("║      danger-full-access + never          ║")
    print("║  q   返回                                ║")
    print("╚══════════════════════════════════════════╝")
    print()
    choice = _prompt("请选择 (m/p/a/b/q): ").lower()
    profile_map = {
        "m": ("gpt56-sol-manual", "手动确认 (workspace-write + on-request)"),
        "p": ("gpt56-sol-readonly", "只读规划 (read-only + never)"),
        "a": ("gpt56-sol-auto", "项目内自动执行 (workspace-write + never)"),
        "b": ("gpt56-sol-full", "完全访问 ⚠️ (danger-full-access + never)"),
    }
    if choice == "q":
        return None  # back to provider
    if choice in profile_map:
        profile, name = profile_map[choice]
        return {"profile": profile, "name": name, "is_full": choice == "b"}
    print("无效选择，已取消。")
    return {"error": True}


def _codex_preflight(project_dir: Path, profile: str) -> bool:
    """Pre-launch checks for Codex.  Non-blocking on API reachability failure."""
    # Check binary
    codex_bin = _find_executable("codex")
    if not codex_bin:
        print("\n错误: Codex CLI 未安装或不在 PATH 中。", file=sys.stderr)
        print("请运行: npm install -g @openai/codex", file=sys.stderr)
        return False

    # Check version
    try:
        r = subprocess.run([codex_bin, "--version"], capture_output=True, text=True, timeout=10)
        ver = r.stdout.strip()
        ver_num = ver.removeprefix("codex-cli ").strip()
        parts = ver_num.split(".")
        major, minor = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        if major < 0 or (major == 0 and minor < 144):
            print(f"\n错误: Codex 版本过低。当前: {ver}，需要: >= 0.144.0", file=sys.stderr)
            return False
    except Exception:
        print("\n错误: 无法获取 Codex 版本。", file=sys.stderr)
        return False

    if not project_dir.is_dir():
        print(f"\n错误: 项目目录不存在: {project_dir}", file=sys.stderr)
        return False

    profile_file = Path.home() / ".codex" / f"{profile}.config.toml"
    if not profile_file.is_file():
        print(f"\n错误: Codex profile 文件不存在: {profile_file}", file=sys.stderr)
        return False

    content = profile_file.read_text(encoding="utf-8")
    if "gpt-5.6-sol" not in content:
        print(f"\n错误: profile 文件缺少 model = \"gpt-5.6-sol\": {profile_file}", file=sys.stderr)
        return False

    # API reachability (cached 24h, non-blocking)
    preflight_file = Path(os.environ.get("XDG_STATE_HOME",
                         str(Path.home() / ".local" / "state"))) / "cc-launcher" / "codex-preflight"
    try:
        preflight_file.parent.mkdir(parents=True, exist_ok=True)
        now = int(subprocess.check_output(["date", "+%s"], text=True, timeout=5).strip())
        last_check = 0
        if preflight_file.is_file():
            first_line = preflight_file.read_text(encoding="utf-8").split("\n")[0].strip()
            if first_line.isdigit():
                last_check = int(first_line)
        if (now - last_check) > 86400:
            _check_api_reachable()
            preflight_file.write_text(f"{now}\n{codex_bin}\n{ver}\n{profile}\n", encoding="utf-8")
    except Exception:
        pass  # non-blocking

    return True


def _check_api_reachable() -> bool:
    import urllib.request
    try:
        urllib.request.urlopen("https://api.openai.com/", timeout=8)
        return True
    except Exception:
        print("\n警告: 无法连接 OpenAI API；请检查 DNS、VPN 或网络出口。", file=sys.stderr)
        return False


def _find_executable(name: str) -> str | None:
    result = subprocess.run(["type", "-P", name], capture_output=True, text=True, timeout=5)
    path = result.stdout.strip()
    return path if path else None


# ---------------------------------------------------------------------------
# Project determination
# ---------------------------------------------------------------------------

def _browse_projects() -> Path | None:
    if not PROJECTS_ROOT.is_dir():
        print(f"\n错误: ~/Projects 目录不存在。", file=sys.stderr)
        return None

    dirs: list[Path] = []
    for d in sorted(PROJECTS_ROOT.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        if name.startswith("_") or name.startswith("."):
            continue
        if is_timestamp_session_dir(name):
            continue
        if name == "_recovery-review":
            continue
        if project_picker_group(name) != "primary":
            continue
        if has_git(d):
            dirs.insert(0, d)
        else:
            dirs.append(d)

    if not dirs:
        print("\n~/Projects 中没有找到任何项目目录。", file=sys.stderr)
        return None

    print()
    print("~/Projects 中的主项目 (Git 仓库优先):")
    print()
    for i, d in enumerate(dirs, 1):
        print(f"  {i:2d}  {d.name}  {project_indicators(d)}")
        print(f"      {d}")

    choice = _prompt("请选择编号: ")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(dirs):
            return dirs[idx]
    except ValueError:
        pass
    if choice.lower() == "q":
        print("已取消。")
        return None
    print("无效选择。", file=sys.stderr)
    return None


def _recent_menu() -> Path | None:
    RECENT_STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not RECENT_FILE.is_file() or RECENT_FILE.stat().st_size == 0:
        print("\n暂无最近项目。")
        return None

    entries: list[str] = []
    for line in RECENT_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        p = Path(line)
        if not p.is_dir():
            continue
        if is_timestamp_session_dir(p.name):
            continue
        if "/.ai/sessions/" in line or "/.ai-session/sessions/" in line:
            continue
        entries.append(line)

    if not entries:
        print("\n暂无最近项目。")
        return None

    max_show = min(len(entries), 10)
    print()
    print("最近项目:")
    print()
    for i in range(max_show):
        p = Path(entries[i])
        print(f"  {i+1:<2d} {p.name}  {project_indicators(p)}")
        print(f"      {p}")
        print()
    print("   b  返回主菜单")
    print("   q  退出")
    print()
    choice = _prompt("请选择编号: ")
    if choice.lower() in ("b", "q"):
        return None
    try:
        idx = int(choice) - 1
        if 0 <= idx < max_show:
            return Path(entries[idx])
    except ValueError:
        pass
    print("无效选择。", file=sys.stderr)
    return None


def _create_new_project() -> Path | None:
    while True:
        print()
        name = _prompt("请输入项目名称: ").strip()
        if not name:
            print("错误: 项目名称不能为空。", file=sys.stderr)
            continue
        if "/" in name or ".." in name or name.startswith("~"):
            print("错误: 项目名称不能包含路径分隔符或特殊字符。", file=sys.stderr)
            continue

        target = PROJECTS_ROOT / name
        print(f"\n将创建：\n  {target}\n")
        print("  1  创建并打开\n  2  重新输入\n  b  返回主菜单\n  q  退出\n")
        choice = _prompt("请选择 (1/2/b/q): ")
        if choice == "2":
            continue
        if choice.lower() == "b":
            return None
        if choice.lower() == "q":
            print("已取消。")
            return None
        if choice != "1":
            print("无效选择。", file=sys.stderr)
            continue

        if target.is_dir():
            print(f"\n项目已存在：\n  {target}\n")
            print("  1  直接打开已有项目\n  2  重新输入名称\n  b  返回主菜单\n  q  退出\n")
            sub = _prompt("请选择 (1/2/b/q): ")
            if sub == "1":
                print(f"\n打开现有项目: {target}")
                return target
            if sub == "2":
                continue
            if sub.lower() == "b":
                return None
            if sub.lower() == "q":
                print("已取消。")
                return None
            continue

        target.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(["git", "-C", str(target), "init"], capture_output=True, timeout=10)
        except Exception as e:
            print(f"警告: git init 失败，但目录已创建。{e}", file=sys.stderr)

        print(f"\n项目创建成功：\n  {target}")
        return target


def _manual_input() -> Path | None:
    print()
    raw = _prompt("请输入项目路径 (~ 会自动展开): ")
    raw = raw.replace("~", str(Path.home()))
    p = Path(raw).resolve()
    if not p.is_dir():
        print(f"错误: 目录不存在: {raw}", file=sys.stderr)
        return None
    if p.is_file():
        print(f"错误: 路径是普通文件，不是目录: {raw}", file=sys.stderr)
        return None
    print(f"解析后的路径: {p}")
    return p


def determine_project() -> Path | None:
    # Priority 0: _CC_HERE_MODE
    if os.environ.get("_CC_HERE_MODE") == "1":
        p = Path.cwd()
        print(f"\ncc-here 模式: 使用当前目录 {p}")
        return p

    # Priority 0b: _CC_PRESET_PROJECT
    preset = os.environ.get("_CC_PRESET_PROJECT", "")
    if preset and Path(preset).is_dir():
        p = Path(preset)
        print(f"\n使用预设项目: {p}")
        return p

    # Priority 1: current dir is inside a git repo
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5, check=True,
        )
        p = Path(r.stdout.strip())
        print(f"\n检测到 Git 项目: {p}")
        return p
    except Exception:
        pass

    # Priority 2: interactive menu
    while True:
        _print_banner("Claude / DeepSeek / Codex 项目启动器")
        print("║  当前目录不是 Git 仓库。请选择项目:      ║")
        print("║  1  当前目录")
        print("║  2  最近项目")
        print("║  3  从 ~/Projects 中选择项目")
        print("║  4  在 ~/Projects 中新建项目")
        print("║  5  手动输入项目路径")
        print("║  q  退出")
        print("╚══════════════════════════════════════════╝")
        print()
        choice = _prompt("请选择 (1/2/3/4/5/q): ")

        if choice == "1":
            return Path.cwd()
        if choice == "2":
            result = _recent_menu()
            if result:
                return result
        elif choice == "3":
            result = _browse_projects()
            if result:
                return result
        elif choice == "4":
            result = _create_new_project()
            if result:
                return result
        elif choice == "5":
            result = _manual_input()
            if result:
                return result
        elif choice.lower() == "q":
            print("已取消。")
            return None
        else:
            print("无效选择，请重试。", file=sys.stderr)


# ---------------------------------------------------------------------------
# Launch orchestration
# ---------------------------------------------------------------------------

def _launch_claude(project_dir: Path, provider: str, perm_mode: str,
                   bypass: bool, extra_args: list[str] | None = None) -> int:
    """Launch Claude or DeepSeek via the workspace manager's launcher."""
    from flowfoundry.workspace.launcher import launch_here

    config_dir = {
        "claude": str(Path.home() / ".claude-native"),
        "deepseek": str(Path.home() / ".claude-deepseek"),
    }.get(provider, str(Path.home() / ".claude-native"))

    os.environ["CLAUDE_CONFIG_DIR"] = config_dir

    if provider == "claude":
        for var in ("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY",
                     "ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL",
                     "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL",
                     "CLAUDE_CODE_SUBAGENT_MODEL", "CLAUDE_CODE_EFFORT_LEVEL"):
            os.environ.pop(var, None)

    os.environ["CC_ACTIVE_PROJECT"] = str(project_dir)
    if "CC_PROJECT_MODE" not in os.environ:
        os.environ["CC_PROJECT_MODE"] = "existing"

    claude_bin = _find_executable("claude") or "claude"
    if bypass:
        cmd_args = ["--permission-mode", "bypassPermissions"]
    else:
        cmd_args = ["--allow-dangerously-skip-permissions", "--permission-mode", perm_mode]
    if extra_args:
        cmd_args = list(extra_args) + cmd_args

    return launch_here(
        tool="claude",
        project_dir=project_dir,
        cli_path=claude_bin,
        extra_args=cmd_args,
        provider=provider,
        permission_mode=perm_mode,
    )


def _launch_codex(project_dir: Path, profile: str) -> int:
    """Launch Codex directly."""
    codex_bin = _find_executable("codex")
    if not codex_bin:
        print("错误：找不到可执行的 OpenAI Codex CLI。", file=sys.stderr)
        return 1

    os.environ["CC_ACTIVE_PROJECT"] = str(project_dir)
    os.environ["CC_PROJECT_MODE"] = "existing"

    os.chdir(project_dir)
    os.execv(codex_bin, [codex_bin, "--profile", profile])
    return 0  # unreachable after execv


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Run the interactive cc launcher and return exit code."""

    # Step 0: Determine project
    project_dir = determine_project()
    if project_dir is None:
        return 0

    _show_remote_banner()

    # Record to recent
    if os.environ.get("_CC_HERE_MODE") != "1":
        add_to_recent(project_dir)

    # Handle non-git projects
    if not has_git(project_dir):
        print(f"\n该目录不是 Git 仓库:\n  {project_dir}\n")
        print("  1  初始化 Git 后打开\n  2  直接打开，不初始化 Git\n  b  返回\n  q  退出\n")
        choice = _prompt("请选择 (1/2/b/q): ")
        if choice == "1":
            subprocess.run(["git", "-C", str(project_dir), "init"], capture_output=True, timeout=10)
        elif choice == "2":
            pass
        elif choice.lower() == "q":
            print("已取消。")
            return 0
        else:
            return main()  # restart menu

    # Step 1: Choose provider
    while True:
        provider = _choose_provider(project_dir)
        if provider is None:
            return 0
        if provider == "error":
            return 1
        if provider == "q":
            print("已取消。")
            return 0

        if provider == "o":
            # Codex path
            codex_cfg = _choose_codex_mode()
            if codex_cfg is None:
                continue  # back to provider
            if codex_cfg.get("error"):
                return 1
            if codex_cfg.get("is_full"):
                if not _confirm_remote("Codex danger-full-access"):
                    return 1

            # Confirm
            print()
            print("╔══════════════════════════════════════════╗")
            print("║  确认启动                                ║")
            print("╠══════════════════════════════════════════╣")
            print(f"║  项目: {project_dir}")
            print(f"║  工具: OpenAI Codex (GPT-5.6 Sol)")
            print(f"║  权限: {codex_cfg['name']}")
            print("╚══════════════════════════════════════════╝")
            print()
            answer = _prompt("请输入 'yes' 确认启动: ")
            if _prompt_closed:
                print("输入已关闭，已取消。")
                return 1
            if answer != "yes":
                print("已取消。")
                return 1

            if not _codex_preflight(project_dir, codex_cfg["profile"]):
                print()
                print("╔══════════════════════════════════════════════════════════╗")
                print("║  Codex 启动前检查失败                                   ║")
                print("║  1  返回工具菜单                                       ║")
                print("║  q  退出                                               ║")
                print("╚══════════════════════════════════════════════════════════╝")
                if _prompt("请选择 (1/q): ") == "1":
                    continue
                return 0

            return _launch_codex(project_dir, codex_cfg["profile"])

        else:
            # Claude / DeepSeek path
            perm_cfg = _choose_permission_mode()
            if perm_cfg is None:
                continue  # back to provider
            if perm_cfg.get("error"):
                return 1
            if perm_cfg.get("bypass") and not _confirm_remote("Claude/DeepSeek bypassPermissions"):
                return 1

            # Confirm
            print()
            print("╔══════════════════════════════════════════╗")
            print("║  确认启动                                ║")
            print("╠══════════════════════════════════════════╣")
            print(f"║  项目: {project_dir}")
            provider_name = {"c": "Claude (Anthropic 原生)", "d": "DeepSeek V4 Pro"}.get(provider, provider)
            print(f"║  模型: {provider_name}")
            print(f"║  权限: {perm_cfg['name']}")
            if not perm_cfg.get("bypass"):
                print("║  Shift+Tab 可切换权限模式                ║")
            print("╚══════════════════════════════════════════╝")
            print()
            answer = _prompt("请输入 'yes' 确认启动: ")
            if _prompt_closed:
                print("输入已关闭，已取消。")
                return 1
            if answer != "yes":
                print("已取消。")
                return 1

            prov = {"c": "claude", "d": "deepseek"}.get(provider, "claude")
            return _launch_claude(
                project_dir, prov, perm_cfg["mode"], perm_cfg["bypass"]
            )


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""aiproj — AI Project Manager CLI.

Usage:
  aiproj new claude [--model MODEL] [--provider PROVIDER] [--permission-mode MODE]
  aiproj new codex [--model MODEL] [--provider PROVIDER] [--permission-mode MODE]
  aiproj here claude [--dir PATH]
  aiproj here codex [--dir PATH]
  aiproj select codex
  aiproj open codex
  aiproj last codex
  aiproj launch-new --tool TOOL [--cli-path PATH] [--extra-args ...]
  aiproj launch-here --tool TOOL [--dir PATH]
  aiproj status
  aiproj latest
  aiproj list
  aiproj unfinished
  aiproj finalize SESSION_ID [--dir PATH]
  aiproj repair SESSION_ID [--dir PATH]
  aiproj recover
  aiproj doctor
  aiproj show-config
  aiproj uninstall-plan
"""

import os
import sys
from pathlib import Path

# Ensure package is importable
_script_dir = Path(__file__).resolve().parent.parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))


def run(argv=None):
    """Run the aiproj CLI and return an exit code (0 = success, 1/2 = error).

    Accepts an explicit argv list so it can be composed inside a unified CLI
    without spawning a subprocess or catching SystemExit.
    """
    args = list(sys.argv[1:]) if argv is None else list(argv)

    if not args:
        _usage()
        return 1

    cmd = args[0]

    if cmd in ("-h", "--help", "help"):
        _usage()
        return 0

    try:
        if cmd == "new":
            _cmd_new(args[1:])
        elif cmd == "here":
            _cmd_here(args[1:])
        elif cmd == "select":
            _cmd_select(args[1:])
        elif cmd == "open":
            _cmd_open(args[1:])
        elif cmd == "last":
            _cmd_last(args[1:])
        elif cmd == "launch-new":
            _cmd_launch_new(args[1:])
        elif cmd == "launch-here":
            _cmd_launch_here(args[1:])
        elif cmd == "status":
            _cmd_status()
        elif cmd == "latest":
            _cmd_latest()
        elif cmd == "list":
            _cmd_list(args[1:])
        elif cmd == "unfinished":
            _cmd_unfinished()
        elif cmd == "finalize":
            _cmd_finalize(args[1:])
        elif cmd == "repair":
            _cmd_repair(args[1:])
        elif cmd == "recover":
            _cmd_recover()
        elif cmd == "doctor":
            _cmd_doctor()
        elif cmd == "show-config":
            _cmd_show_config()
        elif cmd == "uninstall-plan":
            _cmd_uninstall_plan()
        elif cmd == "open-latest":
            _cmd_open_latest()
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            _usage()
            return 1
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1

    return 0


def main():
    """Main CLI entry point (backward-compat, calls sys.exit)."""
    sys.exit(run())


def _usage():
    print("""aiproj — AI Project Manager

Usage:
  aiproj new claude          Create new project and launch Claude
  aiproj new codex           Create new project and launch Codex
  aiproj here claude         Launch Claude in current directory
  aiproj here codex          Launch Codex in current directory
  aiproj select codex        Choose new/open/last/current interactively
  aiproj open codex          Choose and open an existing project
  aiproj last codex          Open the most recently updated project
  aiproj status              Show running/interrupted projects
  aiproj latest              Show most recent project
  aiproj list [N]            List recent projects (default 10)
  aiproj unfinished          List projects with outstanding tasks
  aiproj finalize SESSION_ID Idempotently finalize a session
  aiproj repair SESSION_ID   Re-parse and re-finalize a session
  aiproj recover             Scan and recover interrupted sessions
  aiproj doctor              Check installation health
  aiproj show-config         Show non-sensitive configuration
  aiproj uninstall-plan      Show uninstall and restore instructions
""")


def _cmd_new(args):
    """Create a new project and launch the CLI."""
    if not args:
        print(
            "Usage: aiproj new <claude|codex> [--workflow CONTRACT_ID]", file=sys.stderr
        )
        sys.exit(1)

    tool = args[0].lower()
    if tool not in ("claude", "codex"):
        print(f"Unknown tool: {tool}. Use 'claude' or 'codex'.", file=sys.stderr)
        sys.exit(1)

    from ..lifecycle.launcher import launch_new

    # Parse optional flags
    extra_args = []
    model = ""
    provider = ""
    permission_mode = ""
    workflow_contract = ""

    remaining = args[1:]
    i = 0
    while i < len(remaining):
        if remaining[i] == "--model" and i + 1 < len(remaining):
            model = remaining[i + 1]
            i += 2
        elif remaining[i] == "--provider" and i + 1 < len(remaining):
            provider = remaining[i + 1]
            i += 2
        elif remaining[i] == "--permission-mode" and i + 1 < len(remaining):
            permission_mode = remaining[i + 1]
            i += 2
        elif remaining[i] == "--workflow" and i + 1 < len(remaining):
            workflow_contract = remaining[i + 1]
            i += 2
            i += 2
        elif remaining[i] == "--":
            extra_args.extend(remaining[i + 1 :])
            break
        else:
            extra_args.append(remaining[i])
            i += 1

    exit_code = launch_new(
        tool=tool,
        extra_args=extra_args if extra_args else None,
        model=model,
        provider=provider,
        permission_mode=permission_mode,
        workflow_contract_id=workflow_contract or None,
    )
    sys.exit(exit_code)


def _cmd_here(args):
    """Launch CLI in current directory."""
    if not args:
        print("Usage: aiproj here <claude|codex>", file=sys.stderr)
        sys.exit(1)

    tool = args[0].lower()
    if tool not in ("claude", "codex"):
        print(f"Unknown tool: {tool}. Use 'claude' or 'codex'.", file=sys.stderr)
        sys.exit(1)

    from ..lifecycle.launcher import launch_here

    project_dir = None
    cli_path = None
    extra_args = []

    remaining = args[1:]
    i = 0
    while i < len(remaining):
        if remaining[i] == "--dir" and i + 1 < len(remaining):
            project_dir = Path(remaining[i + 1])
            i += 2
        elif remaining[i] == "--":
            extra_args.extend(remaining[i + 1 :])
            break
        else:
            extra_args.append(remaining[i])
            i += 1

    exit_code = launch_here(
        tool=tool,
        project_dir=project_dir,
        cli_path=cli_path,
        extra_args=extra_args if extra_args else None,
    )
    sys.exit(exit_code)


def _parse_tool_args(args, command):
    if not args or args[0].lower() not in ("claude", "codex", "deepseek"):
        print(f"Usage: aiproj {command} <claude|codex|deepseek>", file=sys.stderr)
        sys.exit(1)
    tool = args[0].lower()
    extra = args[1:]
    if extra and extra[0] == "--":
        extra = extra[1:]
    return tool, extra or None


def _cmd_select(args):
    """Show the zero-argument interactive project menu."""
    tool, extra_args = _parse_tool_args(args, "select")
    if not sys.stdin.isatty() or not sys.stdout.isatty() or os.environ.get("CI"):
        print("Project selection requires an interactive TTY.", file=sys.stderr)
        sys.exit(2)

    print("请选择项目：\n")
    print("[n] 新建项目")
    print("[o] 打开已有项目")
    print("[l] 最近一次项目")
    print("[h] 使用当前目录")
    print("[q] 取消")
    try:
        choice = input("请选择 [n/o/l/h/q]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if choice == "n":
        from ..lifecycle.launcher import launch_new

        sys.exit(launch_new(tool, extra_args=extra_args))
    if choice == "o":
        _launch_chosen_project(tool, extra_args)
        return
    if choice == "l":
        _launch_latest_project(tool, extra_args)
        return
    if choice == "h":
        from ..lifecycle.launcher import launch_here

        sys.exit(launch_here(tool, project_dir=Path.cwd(), extra_args=extra_args))
    if choice == "q":
        return
    print("无效选择。", file=sys.stderr)
    sys.exit(2)


def _launch_chosen_project(tool, extra_args=None):
    from ..lifecycle.launcher import launch_here
    from ..lifecycle.project import choose_project

    project_dir = choose_project()
    if project_dir is None:
        return
    sys.exit(launch_here(tool, project_dir=project_dir, extra_args=extra_args))


def _launch_latest_project(tool, extra_args=None):
    from ..lifecycle.launcher import launch_here
    from ..lifecycle.project import discover_projects

    projects = discover_projects()
    if not projects:
        print("没有找到已有项目。", file=sys.stderr)
        sys.exit(1)
    sys.exit(
        launch_here(tool, project_dir=Path(projects[0]["path"]), extra_args=extra_args)
    )


def _cmd_open(args):
    tool, extra_args = _parse_tool_args(args, "open")
    if not sys.stdin.isatty() or not sys.stdout.isatty() or os.environ.get("CI"):
        print("Opening by selection requires an interactive TTY.", file=sys.stderr)
        sys.exit(2)
    _launch_chosen_project(tool, extra_args)


def _cmd_last(args):
    tool, extra_args = _parse_tool_args(args, "last")
    _launch_latest_project(tool, extra_args)


def _cmd_launch_new(args):
    """Launch with pre-configured settings (for cc wrapper)."""
    tool = ""
    cli_path = None
    extra_args = []
    env = {}
    model = ""
    provider = ""
    permission_mode = ""

    i = 0
    while i < len(args):
        if args[i] == "--tool" and i + 1 < len(args):
            tool = args[i + 1]
            i += 2
        elif args[i] == "--cli-path" and i + 1 < len(args):
            cli_path = args[i + 1]
            i += 2
        elif args[i] == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        elif args[i] == "--provider" and i + 1 < len(args):
            provider = args[i + 1]
            i += 2
        elif args[i] == "--permission-mode" and i + 1 < len(args):
            permission_mode = args[i + 1]
            i += 2
        elif args[i] == "--env" and i + 1 < len(args):
            k, v = args[i + 1].split("=", 1)
            env[k] = v
            i += 2
        elif args[i] == "--":
            extra_args.extend(args[i + 1 :])
            break
        else:
            extra_args.append(args[i])
            i += 1

    if not tool:
        print("Error: --tool is required", file=sys.stderr)
        sys.exit(1)

    from ..lifecycle.launcher import launch_new

    exit_code = launch_new(
        tool=tool,
        cli_path=cli_path,
        extra_args=extra_args if extra_args else None,
        env=env if env else None,
        model=model,
        provider=provider,
        permission_mode=permission_mode,
    )
    sys.exit(exit_code)


def _cmd_launch_here(args):
    """Launch with pre-configured settings in current dir."""
    tool = ""
    project_dir = None
    cli_path = None
    extra_args = []
    env = {}
    model = ""
    provider = ""
    permission_mode = ""

    i = 0
    while i < len(args):
        if args[i] == "--tool" and i + 1 < len(args):
            tool = args[i + 1]
            i += 2
        elif args[i] == "--dir" and i + 1 < len(args):
            project_dir = Path(args[i + 1])
            i += 2
        elif args[i] == "--cli-path" and i + 1 < len(args):
            cli_path = args[i + 1]
            i += 2
        elif args[i] == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        elif args[i] == "--provider" and i + 1 < len(args):
            provider = args[i + 1]
            i += 2
        elif args[i] == "--permission-mode" and i + 1 < len(args):
            permission_mode = args[i + 1]
            i += 2
        elif args[i] == "--env" and i + 1 < len(args):
            k, v = args[i + 1].split("=", 1)
            env[k] = v
            i += 2
        elif args[i] == "--":
            extra_args.extend(args[i + 1 :])
            break
        else:
            extra_args.append(args[i])
            i += 1

    if not tool:
        print("Error: --tool is required", file=sys.stderr)
        sys.exit(1)

    from ..lifecycle.launcher import launch_here

    exit_code = launch_here(
        tool=tool,
        project_dir=project_dir,
        cli_path=cli_path,
        extra_args=extra_args if extra_args else None,
        env=env if env else None,
        model=model,
        provider=provider,
        permission_mode=permission_mode,
    )
    sys.exit(exit_code)


def _cmd_status():
    """Show running and interrupted projects."""
    from ..policy.runtime import read_json
    from ..sessions.recovery import scan_interrupted_projects

    interrupted = scan_interrupted_projects()
    if interrupted:
        print("Interrupted / running projects:")
        for p in interrupted:
            print(f"  {p['session_id']}  {p['tool']}  {p['status']}  {p['path']}")
    else:
        print("No interrupted projects found.")

    # Also show recent running
    index_path = (
        Path.home() / ".local" / "state" / "ai-project-manager" / "project-index.json"
    )
    index = read_json(index_path)
    if index:
        running = {
            k: v
            for k, v in index.get("projects", {}).items()
            if v.get("status") in ("running", "finalizing")
        }
        if running:
            print("\nRunning sessions (from index):")
            for sid, info in running.items():
                print(f"  {sid}  {info.get('tool', '?')}  {info['path']}")


def _cmd_latest():
    """Show most recent project."""
    from ..policy.runtime import read_json

    index_path = (
        Path.home() / ".local" / "state" / "ai-project-manager" / "project-index.json"
    )
    index = read_json(index_path)
    if index and index.get("projects"):
        sorted_projects = sorted(
            index["projects"].items(),
            key=lambda x: x[1].get("created", ""),
            reverse=True,
        )
        if sorted_projects:
            sid, info = sorted_projects[0]
            print(f"Session: {sid}")
            print(f"Path: {info['path']}")
            print(f"Tool: {info.get('tool', '?')}")
            print(f"Status: {info.get('status', '?')}")
            return
    print("No projects found.")


def _cmd_list(args):
    """List recent projects."""
    from ..policy.runtime import read_json

    limit = 10
    if args:
        try:
            limit = int(args[0])
        except ValueError:
            pass

    index_path = (
        Path.home() / ".local" / "state" / "ai-project-manager" / "project-index.json"
    )
    index = read_json(index_path)
    if index and index.get("projects"):
        sorted_projects = sorted(
            index["projects"].items(),
            key=lambda x: x[1].get("created", ""),
            reverse=True,
        )
        for sid, info in sorted_projects[:limit]:
            print(
                f"{sid}  {info.get('tool', '?'):8s}  {info.get('status', '?'):12s}  {info['path']}"
            )
    else:
        print("No projects found.")


def _cmd_unfinished():
    """List projects with unfinished tasks."""
    from ..policy.runtime import PROJECTS_ROOT

    if not PROJECTS_ROOT.exists():
        print("No projects found.")
        return

    for entry in sorted(PROJECTS_ROOT.iterdir(), reverse=True):
        if not entry.is_dir():
            continue
        tasks_path = entry / "docs" / "tasks.md"
        if tasks_path.exists():
            content = tasks_path.read_text(encoding="utf-8")
            if "## 未完成" in content:
                # Check if there are actual items under 未完成
                section = (
                    content.split("## 未完成")[1] if "## 未完成" in content else ""
                )
                section = section.split("##")[0] if "##" in section else section
                items = [
                    line
                    for line in section.split("\n")
                    if line.strip().startswith("- [ ]")
                ]
                if items:
                    print(f"{entry.name} — {len(items)} unfinished tasks")
                    for item in items[:5]:
                        print(f"  {item.strip()}")


def _cmd_finalize(args):
    """Idempotently finalize a session."""
    if not args:
        print("Usage: aiproj finalize SESSION_ID [--dir PATH]", file=sys.stderr)
        sys.exit(1)

    session_id = args[0]
    project_dir = Path.cwd()

    remaining = args[1:]
    i = 0
    while i < len(remaining):
        if remaining[i] == "--dir" and i + 1 < len(remaining):
            project_dir = Path(remaining[i + 1])
            i += 2
        else:
            i += 1

    from ..sessions.finalize import finalize_session

    result = finalize_session(project_dir, session_id)
    if result["success"]:
        print(f"Finalized: {result['status']}  commit: {result.get('commit', 'none')}")
    else:
        print(f"Finalize failed: {result.get('error', 'unknown')}", file=sys.stderr)
        sys.exit(1)


def _cmd_repair(args):
    """Re-parse and re-finalize a session."""
    if not args:
        print("Usage: aiproj repair SESSION_ID [--dir PATH]", file=sys.stderr)
        sys.exit(1)

    session_id = args[0]
    project_dir = Path.cwd()

    remaining = args[1:]
    i = 0
    while i < len(remaining):
        if remaining[i] == "--dir" and i + 1 < len(remaining):
            project_dir = Path(remaining[i + 1])
            i += 2
        else:
            i += 1

    from ..policy.runtime import atomic_write_json, read_json
    from ..sessions.finalize import finalize_session

    # Reset finalize state to allow re-finalize
    meta = read_json(project_dir / ".ai-session" / "project.json")
    if meta:
        meta["status"] = "running"
        meta["finalize_attempts"] = 0
        meta["final_commit"] = None
        atomic_write_json(project_dir / ".ai-session" / "project.json", meta)

    # Re-parse transcript
    result = finalize_session(project_dir, session_id)
    if result["success"]:
        print(f"Repaired: {result['status']}  commit: {result.get('commit', 'none')}")
    else:
        print(f"Repair failed: {result.get('error', 'unknown')}", file=sys.stderr)
        sys.exit(1)


def _cmd_recover():
    """Scan and recover interrupted sessions."""
    from ..sessions.recovery import recover_all

    results = recover_all()
    for r in results:
        status = (
            "OK"
            if r["result"].get("success")
            else f"FAILED: {r['result'].get('error')}"
        )
        print(f"{r['session_id']}: {status}")


def _cmd_doctor():
    """Check installation health."""
    import subprocess

    from ..policy.runtime import (
        CONFIG_DIR,
        INSTALL_DIR,
        STATE_DIR,
        find_real_executable,
    )

    print("=== AI Project Manager Doctor ===\n")

    checks = []

    # Check directories
    for desc, path in [
        ("Config dir", CONFIG_DIR),
        ("Install dir", INSTALL_DIR),
        ("State dir", STATE_DIR),
        ("Projects dir", Path.home() / "Projects"),
    ]:
        ok = path.exists() and path.is_dir()
        writable = ok and os.access(path, os.W_OK)
        checks.append((f"{desc}: {path}", ok and writable))

    # Check executables
    for tool in ["claude", "codex"]:
        path = find_real_executable(tool)
        ok = path is not None and Path(path).exists()
        checks.append((f"{tool} executable", ok, f"  {path}" if ok else "  NOT FOUND"))

    # Check Python
    checks.append(("Python 3", True, f"  {sys.version}"))

    # Check git
    try:
        result = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, timeout=5
        )
        checks.append(("Git", result.returncode == 0, f"  {result.stdout.strip()}"))
    except Exception:
        checks.append(("Git", False, "  NOT FOUND"))

    # Check shell integration
    shell_int = CONFIG_DIR / "shell-integration.sh"
    checks.append(("Shell integration", shell_int.exists(), f"  {shell_int}"))

    # Check bashrc
    bashrc = Path.home() / ".bashrc"
    if bashrc.exists():
        content = bashrc.read_text(encoding="utf-8")
        has_source = "ai-project-manager" in content
        checks.append(("bashrc sourcing", has_source))

    # Check hooks
    for config_dir_name in [".claude", ".claude-native", ".claude-deepseek"]:
        config_dir = Path.home() / config_dir_name
        if config_dir.exists():
            settings = config_dir / "settings.json"
            if settings.exists():
                from ..policy.runtime import read_json

                data = read_json(settings)
                has_hooks = data and "hooks" in data
                checks.append(
                    (
                        f"Hooks in {config_dir_name}",
                        has_hooks,
                        f"  {'Installed' if has_hooks else 'Not installed'}",
                    )
                )

    # Check Codex hooks
    codex_hooks = Path.home() / ".codex" / "hooks.json"
    checks.append(("Codex hooks.json", codex_hooks.exists()))

    # Print results
    all_ok = True
    for check in checks:
        name = check[0]
        ok = check[1]
        detail = check[2] if len(check) > 2 else ""
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")
        if detail:
            print(f"    {detail}")
        if not ok:
            all_ok = False

    print(f"\nOverall: {'Healthy' if all_ok else 'Issues found'}")


def _cmd_show_config():
    """Show non-sensitive configuration."""
    from ..policy.runtime import CONFIG_DIR, INSTALL_DIR

    print("=== AI Project Manager Configuration ===\n")
    print(f"Config dir:  {CONFIG_DIR}")
    print(f"Install dir: {INSTALL_DIR}")
    print(f"State dir:   {Path.home() / '.local' / 'state' / 'ai-project-manager'}")
    print(f"Projects:    {Path.home() / 'Projects'}")
    print(f"Python:      {sys.executable}")
    print("Version:     1.0.0")


def _cmd_uninstall_plan():
    """Show uninstall and restore instructions."""
    print("""=== Uninstall Plan ===

To remove AI Project Manager and restore original configuration:

1. Restore shell config (.bashrc):
   Remove the block between:
     # >>> ai-project-manager >>>
     ...
     # <<< ai-project-manager <<<
   Or restore from backup at:
     ~/.local/state/ai-project-manager/backups/

2. Restore cc script:
   Restore from backup.

3. Restore Claude settings:
   Restore settings.json files from backup.

4. Remove Codex hooks:
   Delete ~/.codex/hooks.json (if no other hooks exist).

5. Remove installed files:
   rm -rf ~/.local/share/ai-project-manager/
   rm -rf ~/.config/ai-project-manager/
   rm -f ~/.local/bin/aiproj

6. State data (optional):
   rm -rf ~/.local/state/ai-project-manager/

7. Existing project data:
   Projects in ~/Projects/ are NOT deleted by uninstall.
   Each project retains its .ai-session/ and docs/ files.

Backups are stored at:
  ~/.local/state/ai-project-manager/backups/YYYYMMDD-HHMMSS/

No remote push was performed. No system-level changes were made.
""")


def _cmd_open_latest():
    """Open the most recent project directory in the default file manager."""
    from ..policy.runtime import read_json

    index_path = (
        Path.home() / ".local" / "state" / "ai-project-manager" / "project-index.json"
    )
    index = read_json(index_path)
    if index and index.get("projects"):
        sorted_projects = sorted(
            index["projects"].items(),
            key=lambda x: x[1].get("created", ""),
            reverse=True,
        )
        if sorted_projects:
            _, info = sorted_projects[0]
            path = info["path"]
            if Path(path).exists():
                import subprocess

                subprocess.run(["xdg-open", path], check=False)
                print(f"Opened: {path}")
                return
    print("No projects found.")


if __name__ == "__main__":
    main()

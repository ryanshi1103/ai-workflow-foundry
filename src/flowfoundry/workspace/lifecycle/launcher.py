"""Launcher — create project, launch CLI, finalize on exit."""

import os
import subprocess
import sys
from pathlib import Path

from ..finalize import finalize_session
from ..git_manager import ensure_git_identity, git_init
from ..project import (
    _update_project_index,
    create_new_project,
    create_session_meta,
    read_project_meta,
)
from ..recovery import auto_recover_on_startup
from ..utils import (
    INTERNAL_ENV_VAR,
    atomic_write_json,
    find_real_executable,
    timestamp_iso,
)


def launch_new(
    tool: str,
    cli_path: str | None = None,
    extra_args: list[str] | None = None,
    env: dict | None = None,
    model: str = "",
    provider: str = "",
    permission_mode: str = "",
    workflow_contract_id: str | None = None,
) -> int:
    """Create a new project and launch the CLI tool interactively.

    **IMPORTANT**: If CC_ACTIVE_PROJECT is set in the environment, this
    function redirects to launch_here instead — the cc launcher has already
    determined the project directory, and we MUST NOT create a new one.

    Returns the CLI's exit code.
    """
    # CRITICAL: If cc launcher set CC_ACTIVE_PROJECT, redirect to launch_here
    cc_active = os.environ.get("CC_ACTIVE_PROJECT", "")
    if cc_active:
        cc_project = Path(cc_active)
        if cc_project.exists():
            print(
                f"  AI Project Manager: Using cc-selected project {cc_project}",
                file=sys.stderr,
            )
            return launch_here(
                tool=tool,
                project_dir=cc_project,
                cli_path=cli_path,
                extra_args=extra_args,
                env=env,
                model=model,
                provider=provider,
                permission_mode=permission_mode,
            )

    # Recover any previously interrupted sessions
    auto_recover_on_startup()

    # Find real executable
    if cli_path is None:
        cli_path = find_real_executable(tool)
    if not cli_path or not Path(cli_path).exists():
        print(f"Error: Could not find {tool} executable", file=sys.stderr)
        return 1

    # Get version
    cli_version = _get_cli_version(cli_path, tool)

    # Create project
    project_dir = create_new_project(
        tool=tool,
        model=model,
        provider=provider,
        permission_mode=permission_mode,
        cli_path=cli_path,
        cli_version=cli_version,
        workflow_contract_id=workflow_contract_id,
    )

    # Initialize git
    git_init(project_dir)
    ensure_git_identity(project_dir)

    # Set environment for project tracking
    child_env = os.environ.copy()
    child_env["AI_PROJECT_MANAGER_PROJECT"] = str(project_dir)
    child_env["AI_PROJECT_MANAGER_SESSION"] = project_dir.name  # temp name = session ID
    child_env["AI_PROJECT_MANAGER_TOOL"] = tool  # for hook tool detection
    if env:
        # Don't override critical project vars
        for k, v in env.items():
            if not k.startswith("AI_PROJECT_MANAGER_"):
                child_env[k] = v

    # Build args
    args = [cli_path]
    if extra_args:
        args.extend(extra_args)

    # Launch CLI interactively
    exit_code = 0
    try:
        print("", file=sys.stderr)
        print(
            f"  AI Project Manager: Created project {project_dir.name}", file=sys.stderr
        )
        print(f"  Project: {project_dir}", file=sys.stderr)
        print("", file=sys.stderr)

        os.chdir(str(project_dir))

        # Run the CLI
        result = subprocess.run(
            args,
            env=child_env,
            # Inherit stdin/stdout/stderr for interactive use
        )

        exit_code = result.returncode

    except KeyboardInterrupt:
        exit_code = 130  # Standard SIGINT exit code
    except Exception as e:
        print(f"Error launching {tool}: {e}", file=sys.stderr)
        exit_code = 1
    finally:
        # Always finalize
        if not _safe_finalize(project_dir, tool) and exit_code == 0:
            exit_code = 1

    return exit_code


def launch_here(
    tool: str,
    project_dir: Path | None = None,
    cli_path: str | None = None,
    extra_args: list[str] | None = None,
    env: dict | None = None,
    model: str = "",
    provider: str = "",
    permission_mode: str = "",
) -> int:
    """Launch the CLI in an existing project directory (continue session).

    **IMPORTANT**: CC_ACTIVE_PROJECT is the single source of truth.
    If set, it overrides project_dir and we MUST use that directory.
    We MUST NOT create a new top-level project in ~/Projects.
    """
    # CRITICAL: CC_ACTIVE_PROJECT is the single source of truth
    cc_active = os.environ.get("CC_ACTIVE_PROJECT", "")
    if cc_active:
        cc_project = Path(cc_active)
        if cc_project.exists():
            project_dir = cc_project.resolve()
            print(
                f"  AI Project Manager: Using CC_ACTIVE_PROJECT={project_dir}",
                file=sys.stderr,
            )

    if project_dir is None:
        project_dir = Path.cwd()

    project_dir = Path(project_dir).resolve()

    # Find real executable
    if cli_path is None:
        cli_path = find_real_executable(tool)
    if not cli_path or not Path(cli_path).exists():
        print(f"Error: Could not find {tool} executable", file=sys.stderr)
        return 1

    # Check if it's an ai-project-manager project
    meta = read_project_meta(project_dir)
    if not meta:
        # Initialize as a project if not already
        git_init(project_dir)
        ensure_git_identity(project_dir)
        from ..project import create_project_meta, create_project_structure

        create_project_structure(project_dir)
        cli_version = _get_cli_version(cli_path, tool)
        session_id = f"{timestamp_iso().replace(':', '').replace('-', '').replace('T', '-')}-{tool}-here"
        create_project_meta(
            project_dir=project_dir,
            tool=tool,
            session_id=session_id,
            model=model,
            provider=provider,
            permission_mode=permission_mode,
            cli_path=cli_path,
            cli_version=cli_version,
        )
        session_meta = create_session_meta(
            project_dir=project_dir,
            session_id=session_id,
            tool=tool,
            model=model,
            provider=provider,
            permission_mode=permission_mode,
            cli_path=cli_path,
            cli_version=cli_version,
        )
        session_meta["status"] = "running"
        atomic_write_json(
            project_dir / ".ai-session" / "sessions" / session_id / "meta.json",
            session_meta,
        )
        meta = read_project_meta(project_dir) or {}
        meta["status"] = "running"
        meta["last_updated"] = timestamp_iso()
        atomic_write_json(project_dir / ".ai-session" / "project.json", meta)
        _update_project_index(project_dir, session_id, tool, status="running")
    else:
        # Create a new session within existing project
        cli_version = _get_cli_version(cli_path, tool)
        from ..utils import generate_session_id

        session_id = generate_session_id(tool)
        session_meta = create_session_meta(
            project_dir=project_dir,
            session_id=session_id,
            tool=tool,
            model=model,
            provider=provider,
            permission_mode=permission_mode,
            cli_path=cli_path,
            cli_version=cli_version,
        )
        session_meta["status"] = "running"
        atomic_write_json(
            project_dir / ".ai-session" / "sessions" / session_id / "meta.json",
            session_meta,
        )
        # Update project meta
        meta["session_id"] = session_id
        meta["status"] = "running"
        meta["tool"] = tool
        meta["last_updated"] = timestamp_iso()
        atomic_write_json(project_dir / ".ai-session" / "project.json", meta)
        _update_project_index(project_dir, session_id, tool, status="running")

    # Set environment
    child_env = os.environ.copy()
    child_env["AI_PROJECT_MANAGER_PROJECT"] = str(project_dir)
    child_env["AI_PROJECT_MANAGER_SESSION"] = session_id
    child_env["AI_PROJECT_MANAGER_TOOL"] = tool
    if env:
        for k, v in env.items():
            if not k.startswith("AI_PROJECT_MANAGER_"):
                child_env[k] = v

    args = [cli_path]
    if extra_args:
        args.extend(extra_args)

    exit_code = 0
    try:
        os.chdir(str(project_dir))
        result = subprocess.run(args, env=child_env)
        exit_code = result.returncode
    except KeyboardInterrupt:
        exit_code = 130
    except Exception as e:
        print(f"Error launching {tool}: {e}", file=sys.stderr)
        exit_code = 1
    finally:
        if not _safe_finalize(project_dir, tool) and exit_code == 0:
            exit_code = 1

    return exit_code


def _safe_finalize(project_dir: Path, tool: str) -> bool:
    """Run finalize, catching all exceptions to ensure we don't crash."""
    try:
        r = finalize_session(project_dir=project_dir, tool=tool, use_ai=False)
        if not r.get("success"):
            print(
                f"Warning: finalize failed: {r.get('error', 'unknown error')}",
                file=sys.stderr,
            )
            return False
        return True
    except Exception as e:
        print(f"Warning: finalize failed: {e}", file=sys.stderr)
        return False


def _get_cli_version(cli_path: str, tool: str) -> str:
    """Get the CLI version string."""
    try:
        result = subprocess.run(
            [cli_path, "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            env={**os.environ, INTERNAL_ENV_VAR: "1"},
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output.split("\n")[0][:200]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return "unknown"


def is_non_interactive_args(tool: str, args: list[str]) -> bool:
    """Detect if args indicate non-interactive use (don't create project)."""
    if not args:
        return False

    # Version/help flags
    if any(a in args for a in ("--version", "-v", "-V", "--help", "-h", "help")):
        return True

    # Claude non-interactive
    if tool == "claude":
        non_interactive = {
            "-p",
            "--print",
            "-c",
            "--continue",
            "-r",
            "--resume",
            "--resume",
            "agents",
            "auth",
            "doctor",
            "gateway",
            "install",
            "mcp",
            "plugin",
            "plugins",
            "project",
            "setup-token",
            "update",
            "upgrade",
            "ultrareview",
        }
        if any(a in non_interactive for a in args):
            return True

    # Codex non-interactive
    if tool == "codex":
        non_interactive = {
            "exec",
            "e",
            "review",
            "login",
            "logout",
            "mcp",
            "plugin",
            "mcp-server",
            "app-server",
            "remote-control",
            "completion",
            "update",
            "doctor",
            "sandbox",
            "debug",
            "apply",
            "a",
            "resume",
            "archive",
            "delete",
            "unarchive",
            "fork",
            "cloud",
            "exec-server",
            "features",
            "help",
        }
        if any(a in non_interactive for a in args):
            return True

    return False

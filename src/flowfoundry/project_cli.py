"""``flowfoundry project`` subcommand group — delegates to workspace CLI.

All project subcommands use ``argparse.REMAINDER`` pass-through so every
legacy ``aiproj`` flag combination continues to work with zero re-parsing.
"""

from __future__ import annotations

import argparse


def add_project_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the ``project`` subcommand group."""
    project_parser = subparsers.add_parser(
        "project",
        help="project lifecycle management (create, launch, finalize, …)",
    )
    project_subs = project_parser.add_subparsers(dest="project_command")

    # Read-only / status commands
    project_subs.add_parser("status", help="show running and interrupted projects")
    project_subs.add_parser("latest", help="show most recent project")
    project_subs.add_parser("unfinished", help="list projects with outstanding tasks")
    project_subs.add_parser("doctor", help="check installation health")
    project_subs.add_parser("show-config", help="show non-sensitive configuration")
    project_subs.add_parser("uninstall-plan", help="show uninstall and restore instructions")
    project_subs.add_parser("recover", help="scan and recover interrupted sessions")

    list_p = project_subs.add_parser("list", help="list recent projects")
    list_p.add_argument("count", nargs="?", type=int, default=None)

    # Commands that accept REMAINDER args (pass-through to workspace CLI)
    for name in ("new", "here", "select", "open", "last",
                 "launch-new", "launch-here",
                 "finalize", "repair"):
        p = project_subs.add_parser(name, help=f"aiproj {name} pass-through")
        p.add_argument("args", nargs=argparse.REMAINDER)

    # launch (Python port of cc)
    launch_p = project_subs.add_parser("launch", help="interactive launcher (cc)")
    launch_p.add_argument("args", nargs=argparse.REMAINDER)

    # maintain (Python port of cc-projects-maintain)
    maintain_p = project_subs.add_parser("maintain", help="project maintenance")
    maintain_p.add_argument("--quick", action="store_true")
    maintain_p.add_argument("--deep", action="store_true")
    maintain_p.add_argument("--report", action="store_true")
    maintain_p.add_argument("--sync-managed", action="store_true")
    maintain_p.add_argument("--purge-quarantine", action="store_true")
    maintain_p.add_argument("--dry-run", action="store_true")


def dispatch_project(cmd: str, args: argparse.Namespace) -> int:
    """Route a project subcommand to the workspace CLI and return exit code."""
    from flowfoundry.workspace.cli import run as ws_run

    # Normalize: strip leading -h/--help captured by REMAINDER
    remainder = getattr(args, "args", None) or []

    # --- Commands with REMAINDER pass-through ---
    if cmd in ("new", "here", "select", "open", "last",
               "launch-new", "launch-here",
               "finalize", "repair"):
        return ws_run([cmd, *remainder])

    # --- Read-only commands ---
    if cmd in ("status", "latest", "unfinished", "doctor",
               "show-config", "uninstall-plan", "recover"):
        return ws_run([cmd])

    # --- list ---
    if cmd == "list":
        if getattr(args, "count", None):
            return ws_run(["list", str(args.count)])
        return ws_run(["list"])

    # --- launch (Python cc launcher) ---
    if cmd == "launch":
        from flowfoundry.workspace.cli.launcher import main as cc_main
        return cc_main()

    # --- maintain ---
    if cmd == "maintain":
        from flowfoundry.workspace.cli.maintenance import run_maintenance_cli
        return run_maintenance_cli(args)

    return 1  # unknown subcommand

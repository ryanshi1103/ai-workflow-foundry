"""FlowFoundry command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .coordinator import (
    approve_task,
    cancel_task,
    create_task,
    load_task,
    list_tasks,
    reconcile_all,
    result_for_task,
    task_summary,
    worker_main,
)
from .ask import ask_project
from .project_context import import_context
from .goal_runner import environment_status, project_root, run_goal


def _agent_response(value: dict[str, object]) -> str:
    return str(
        value.get("agent_response")
        or value.get("result")
        or value.get("final_message")
        or "No result was produced."
    )


def _print_worker_result(value: dict[str, object]) -> None:
    """Print the Worker report first and evaluator/evidence data separately."""
    agent = str(value.get("responsible_agent") or value.get("executor") or "Agent")
    if agent.casefold() == "codex":
        agent = "Codex"
    print(f"STATUS\n{value.get('status', 'UNKNOWN')}\n")
    print(f"RESPONSIBLE AGENT\n{agent}\n")
    print(f"AGENT RESPONSE\n{_agent_response(value)}\n")

    changes = value.get("changes")
    changes = changes if isinstance(changes, dict) else {}
    paths = changes.get("paths")
    if isinstance(paths, list) and paths:
        print("CHANGED FILES")
        for path in paths:
            print(f"- {path}")
        print()
    diff = changes.get("diff")
    if diff:
        print(f"IMPORTANT CODE / DIFF\n{diff}\n")

    verification = value.get("verification")
    verification = verification if isinstance(verification, dict) else {}
    print(f"VERIFICATION\n{verification.get('status', value.get('status', 'UNKNOWN'))}")
    evidence = verification.get("evidence")
    if isinstance(evidence, list) and evidence:
        print("\nEVIDENCE")
        for item in evidence:
            if not isinstance(item, dict):
                continue
            if item.get("kind") == "command":
                print(f"- exit {item.get('exit_code')}: {item.get('command', '')}")
            elif item.get("kind"):
                print(f"- {item.get('kind')}: {json.dumps(item, ensure_ascii=False)}")
    human = value.get("human")
    human = human if isinstance(human, dict) else {}
    needs = human.get("needs_you") or verification.get("needs_user") or "Nothing."
    print(f"\nWHAT NEEDS YOU\n{needs}")


def build_parser(*, include_legacy: bool = False) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flowfoundry",
        description="Give a goal to the smallest useful, evidence-producing execution path.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    do = subparsers.add_parser("do", help="complete one goal and evaluate the result")
    do.add_argument("goal")
    do.add_argument("--workspace", type=Path)
    do.add_argument("--runs-root", type=Path, default=Path(".flowfoundry/do"))
    do.add_argument("--read-only", action="store_true")
    do.add_argument("--permission-level", type=int, choices=(1, 2, 3, 4), default=None,
                    help=argparse.SUPPRESS)
    do.add_argument("--resume", metavar="RUN_ID")
    do.add_argument("--check", action="append", default=[])
    do.add_argument("--timeout", type=int, default=1800)
    do.add_argument("--dry-run", action="store_true")
    do.add_argument(
        "--background",
        action="store_true",
        help="queue a detached local worker and return immediately",
    )
    do.add_argument(
        "--priority",
        choices=("high", "normal", "low"),
        default="normal",
        help="priority for a background task",
    )
    do.add_argument(
        "--verbose",
        action="store_true",
        help="show executor details and retain raw debug logs",
    )

    validate = subparsers.add_parser("validate", help="check the direct goal path")
    validate.add_argument("--workspace", type=Path)

    status = subparsers.add_parser("status", help="show durable local work")
    status.add_argument("task_id", nargs="?")
    status.add_argument("--workspace", type=Path)

    result = subparsers.add_parser("result", help="show a completed task result")
    result.add_argument("task_id")
    result.add_argument("--workspace", type=Path)

    approve = subparsers.add_parser("approve", help="approve one waiting task")
    approve.add_argument("task_id")
    approve.add_argument("--workspace", type=Path)

    cancel = subparsers.add_parser("cancel", help="cancel one local worker")
    cancel.add_argument("task_id")
    cancel.add_argument("--workspace", type=Path)

    ask = subparsers.add_parser("ask", help="ask the project from accepted current context")
    ask.add_argument("question")
    ask.add_argument("--workspace", type=Path)
    ask.add_argument("--verbose", action="store_true")

    context = subparsers.add_parser("context", help="import explicit external context")
    context_sub = context.add_subparsers(dest="context_command", required=True)
    context_import = context_sub.add_parser("import", help="register a candidate context file")
    context_import.add_argument("source", type=Path)
    context_import.add_argument("--title")
    context_import.add_argument("--workspace", type=Path)

    control = subparsers.add_parser(
        "control-center",
        help="open the local Model Control Center on 127.0.0.1",
    )
    control.add_argument("--workspace", type=Path)
    control.add_argument("--host", default="127.0.0.1")
    control.add_argument("--port", type=int, default=4730)
    control.add_argument(
        "--once",
        action="store_true",
        help="print one JSON snapshot and exit without serving",
    )
    control.add_argument(
        "--check",
        action="store_true",
        help="run bounded start/probe/terminate/restart acceptance and exit",
    )
    control.add_argument(
        "--check-timeout",
        type=float,
        default=20.0,
        help="seconds allowed for each lifecycle acceptance cycle",
    )

    # Project management group (delegates to workspace CLI)
    from .project_cli import add_project_parser
    add_project_parser(subparsers)

    # Compatibility only: this command is intentionally absent from default help.
    if include_legacy:
        from .orchestration.cli import add_team_parser

        add_team_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw and raw[0] == "_coordinator-worker":
        worker_parser = argparse.ArgumentParser(add_help=False)
        worker_parser.add_argument("_coordinator-worker")
        worker_parser.add_argument("task_id")
        worker_parser.add_argument("--workspace", type=Path, required=True)
        worker_args = worker_parser.parse_args(raw)
        return worker_main(project_root(worker_args.workspace), worker_args.task_id)
    known = {
        "do",
        "validate",
        "status",
        "result",
        "approve",
        "cancel",
        "ask",
        "context",
        "project",
        "team",
        "control-center",
        "-h",
        "--help",
    }
    if raw and raw[0] not in known and not raw[0].startswith("-"):
        raw.insert(0, "do")
    args = build_parser(include_legacy=bool(raw and raw[0] == "team")).parse_args(raw)
    try:
        if args.command == "do":
            root = project_root(args.workspace)
            if args.background:
                if args.check or args.resume or args.dry_run:
                    raise ValueError("--background cannot be combined with --check, --resume, or --dry-run")
                task = create_task(root, args.goal, priority=args.priority, read_only=args.read_only,
                                   permission_level=args.permission_level)
                print(f"GOAL\n{task.parent_goal}\n")
                print(f"STATUS\n{task.status}\n")
                print(f"TASK\n{task.task_id}\n")
                print(
                    "WHAT WAS DONE\n"
                    "A local worker was detached; the coordinator is free for other goals.\n"
                )
                print(f"WHAT NEEDS YOU\n{task.error or 'Nothing. Use flowfoundry status to check progress.'}")
                return 0
            runs_root = args.runs_root
            if not runs_root.is_absolute():
                runs_root = root / runs_root
            if not args.dry_run:
                action = "Resuming" if args.resume else "Working"
                print(f"FlowFoundry: {action} on your goal…", file=sys.stderr, flush=True)
            code, result = run_goal(
                args.goal,
                root=root,
                runs_root=runs_root,
                read_only=args.read_only or args.permission_level == 1,
                permission_level=args.permission_level,
                resume=args.resume,
                checks=tuple(args.check),
                timeout_seconds=args.timeout,
                dry_run=args.dry_run,
                verbose=args.verbose,
                progress=(
                    None
                    if args.dry_run or not args.verbose
                    else lambda message: print(
                        f"FlowFoundry: {message}", file=sys.stderr, flush=True
                    )
                ),
            )
            if args.dry_run:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"GOAL\n{result['goal']}\n")
                _print_worker_result(result)
                if args.verbose:
                    print(
                        "\nDETAILS\n"
                        f"Executor: {result['executor']}\n"
                        f"Broker: {result['selection']['broker_status']}\n"
                        f"Run: {result['run_id']}\n"
                        f"Evidence: {runs_root / result['run_id'] / 'result.json'}"
                    )
            return code

        if args.command == "validate":
            root = project_root(args.workspace)
            status = environment_status(root)
            print(json.dumps(status, indent=2, ensure_ascii=False))
            return 0 if status["ready"] else 2

        if args.command == "status":
            root = project_root(args.workspace)
            if args.task_id:
                tasks = [task_summary(root, load_task(root, args.task_id))]
            else:
                tasks = [task_summary(root, task) for task in reconcile_all(root)]
            if not tasks:
                print("No local coordinator tasks.")
            else:
                for item in tasks:
                    live = "alive" if item.get("process_alive") else "not-running"
                    result = "available" if item.get("result_available") else "none"
                    print(f"{item['task_id']}  {item['status']}  process={live}  result={result}  {item['goal']}")
            return 0

        if args.command == "result":
            root = project_root(args.workspace)
            value = result_for_task(root, args.task_id)
            if "result" in value and "run_id" in value:
                _print_worker_result(value)
            else:
                print(json.dumps(value, indent=2, ensure_ascii=False))
            return 0

        if args.command == "approve":
            task = approve_task(project_root(args.workspace), args.task_id)
            print(f"{task.task_id}  {task.status}")
            return 0

        if args.command == "cancel":
            task = cancel_task(project_root(args.workspace), args.task_id)
            print(f"{task.task_id}  {task.status}")
            return 0

        if args.command == "ask":
            value = ask_project(project_root(args.workspace), args.question)
            print(f"ANSWER\n{value['answer']}\n")
            print("WHY / EVIDENCE")
            print("Answer grounded in bounded project context; accepted state and decisions take precedence.")
            print("\nPROJECT SOURCES")
            for index, source in enumerate(value["sources"], 1):
                date = f" ({source['date']})" if source.get("date") else ""
                print(f"[{index}] {source['source']} [{source['kind']}/{source['status']}]{date}")
            if value.get("errors"):
                print("\nUNCERTAINTY\n" + "; ".join(value["errors"]))
            if args.verbose:
                retrieval = value["retrieval"]
                print("\nDETAILS")
                print(f"Executor: {value['executor']}  AI calls: {value['ai_calls']}")
                print(f"Retrieved: {retrieval['snippets']} snippets / {retrieval['characters']} chars (~{retrieval['approximate_tokens']} tokens)")
            return 0 if value["status"] != "UNKNOWN" else 1

        if args.command == "context":
            if args.context_command == "import":
                metadata = import_context(project_root(args.workspace), args.source, title=args.title)
                print(f"Imported candidate context: {metadata['stored_path']}\nStatus: {metadata['status']}")
                return 0

        # --- Project management group ---
        if args.command == "project":
            from .project_cli import dispatch_project
            return dispatch_project(args.project_command, args)

        if args.command == "team":
            from .orchestration.cli import dispatch_team

            return dispatch_team(args)

        if args.command == "control-center":
            from .control_center.service import assert_loopback, serve_control_center
            from .control_center.snapshot import collect_snapshot

            root = project_root(args.workspace)
            if args.once and args.check:
                raise ValueError("--once and --check cannot be combined")
            if args.once:
                print(json.dumps(collect_snapshot(root=root), indent=2, ensure_ascii=False))
                return 0
            assert_loopback(args.host)
            if args.check:
                from .control_center.acceptance import run_control_center_acceptance

                report = run_control_center_acceptance(
                    root=root,
                    host=args.host,
                    port=args.port,
                    timeout_seconds=args.check_timeout,
                )
                print(json.dumps(report, indent=2, ensure_ascii=False))
                return 0
            server = serve_control_center(root=root, host=args.host, port=args.port)
            bound_host, bound_port = server.server_address[:2]
            print(
                "FlowFoundry Model Control Center\n"
                "Control Center:\n"
                f"http://{bound_host}:{bound_port}",
                file=sys.stderr,
                flush=True,
            )
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                # ``serve_forever`` has already been interrupted in this
                # thread.  BaseServer.shutdown() must be called from a
                # different thread and can deadlock when invoked here.
                pass
            finally:
                server.server_close()
            return 0

        return 0
    except (OSError, ValueError) as exc:
        print(f"flowfoundry: {exc}", file=sys.stderr)
        return 2

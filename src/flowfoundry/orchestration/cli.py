"""CLI integration for local-first team runs."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

from .aggregator import ResultAggregator
from .approvals import ApprovalGate
from .planner import RuleBasedPlanner
from .providers import FakeProvider, LocalCommandProvider
from .recovery import RecoveryManager
from .registry import default_registry
from .router import TaskRouter
from .scheduler import RunScheduler
from .workspace import RunWorkspace


def add_team_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    team = subparsers.add_parser("team", help="run resumable local multi-agent workflows")
    commands = team.add_subparsers(dest="team_command", required=True)

    run = commands.add_parser("run", help="start an offline-safe task plan")
    run.add_argument("task_file", type=Path)
    run.add_argument("--run-id")
    _add_root_and_provider(run)

    status = commands.add_parser("status", help="inspect persisted run state")
    status.add_argument("run_id")
    _add_root(status)

    resume = commands.add_parser("resume", help="recover and continue an interrupted run")
    resume.add_argument("run_id")
    _add_root_and_provider(resume)

    review = commands.add_parser("review", help="show persisted reviewer decisions")
    review.add_argument("run_id")
    _add_root(review)

    report = commands.add_parser("report", help="aggregate a run report")
    report.add_argument("run_id")
    _add_root(report)

    retry = commands.add_parser("retry", help="mark one failed task for an explicit retry")
    retry.add_argument("run_id")
    retry.add_argument("task_id")
    _add_root(retry)

    approve = commands.add_parser("approve", help="record an explicit human approval")
    approve.add_argument("run_id")
    approve.add_argument("task_id")
    approve.add_argument("--action", action="append", required=True)
    approve.add_argument("--actor", required=True)
    _add_root(approve)


def _add_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--runs-root", type=Path, default=Path(".flowfoundry/runs"))


def _add_root_and_provider(parser: argparse.ArgumentParser) -> None:
    _add_root(parser)
    parser.add_argument(
        "--enable-real-provider",
        action="store_true",
        help="explicitly allow configured local provider commands; never reads auth.json",
    )


def _new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"team-{stamp}-{secrets.token_hex(3)}"


def _scheduler(real_provider: bool) -> RunScheduler:
    registry = default_registry().synthetic()
    provider = LocalCommandProvider(enabled=True) if real_provider else FakeProvider()
    return RunScheduler(TaskRouter(registry), provider)


def dispatch_team(args: argparse.Namespace) -> int:
    try:
        command = args.team_command
        if command == "run":
            plan = RuleBasedPlanner().load(args.task_file)
            run_id = args.run_id or _new_run_id()
            workspace = RunWorkspace.create(args.runs_root, run_id, plan)
            _scheduler(args.enable_real_provider).run(workspace)
            ResultAggregator().aggregate(workspace)
            print(json.dumps(workspace.manifest(), indent=2, ensure_ascii=False))
            return 0

        workspace = RunWorkspace.open(args.runs_root, args.run_id)
        if command == "status":
            print(json.dumps(workspace.manifest(), indent=2, ensure_ascii=False))
        elif command == "resume":
            RecoveryManager().recover_interrupted(workspace)
            _scheduler(args.enable_real_provider).run(workspace)
            ResultAggregator().aggregate(workspace)
            print(json.dumps(workspace.manifest(), indent=2, ensure_ascii=False))
        elif command == "review":
            reviews = [
                workspace.read_json(str(path.relative_to(workspace.path)))
                for path in sorted(workspace.contained("reviews").glob("*.json"))
            ]
            print(json.dumps(reviews, indent=2, ensure_ascii=False))
        elif command == "report":
            print(json.dumps(ResultAggregator().aggregate(workspace), indent=2, ensure_ascii=False))
        elif command == "retry":
            manifest = RecoveryManager().retry_failed_task(workspace, args.task_id)
            print(json.dumps(manifest, indent=2, ensure_ascii=False))
        elif command == "approve":
            ApprovalGate().record_approval(
                workspace,
                args.task_id,
                tuple(args.action),
                args.actor,
            )
            print(f"approval recorded for {args.task_id}")
        return 0
    except (OSError, ValueError, KeyError, LookupError, json.JSONDecodeError) as exc:
        print(f"flowfoundry team: {exc}", file=sys.stderr)
        return 2

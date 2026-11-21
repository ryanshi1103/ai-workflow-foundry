"""Evidence-first outcome evaluation; executor claims never become PASS by themselves."""

from __future__ import annotations

import re
import shlex
from pathlib import PurePosixPath
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Sequence

from .selection import TaskKind


class EvaluationStatus(StrEnum):
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Evaluation:
    status: EvaluationStatus
    evidence: tuple[dict[str, Any], ...]
    needs_user: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "evidence": list(self.evidence),
            "needs_user": self.needs_user,
        }


_URL = re.compile(r"https?://[^\s)>\]]+")
_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")


def _is_acceptance_command(command: str, *, depth: int = 0) -> bool:
    """Recognize a conservative shell subset whose exit status proves a check.

    Command arguments and report text are not executed commands. Unsupported
    shell syntax supplies no acceptance evidence; it must never invent PASS.
    """
    if depth > 4:
        return False
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    if not words:
        return False
    executable = PurePosixPath(words[0]).name
    if executable in {"bash", "sh", "zsh"}:
        return (
            len(words) == 3
            and words[1] in {"-c", "-lc"}
            and _is_acceptance_command(words[2], depth=depth + 1)
        )
    # Reject pipelines, masked failures, substitutions, redirections and
    # multiline scripts. Even quoted occurrences are conservatively declined.
    if any(symbol in command for symbol in (";", "|", "\n", "\r", "<", ">", "`", "$", "(", ")")):
        return False
    segments = command.split("&&")
    if any("&" in segment for segment in segments):
        return False
    accepted = False
    for segment in segments:
        try:
            argv = shlex.split(segment)
        except ValueError:
            return False
        if argv and argv[0] == "env":
            argv = argv[1:]
        while argv and _ASSIGNMENT.match(argv[0]):
            argv = argv[1:]
        if not argv:
            return False
        name = PurePosixPath(argv[0]).name
        args = argv[1:]
        if name == "cd" and len(args) == 1:
            continue
        if any(arg in {"--help", "-h", "--version", "-V", "--collect-only", "--co"} for arg in args):
            return False
        if re.fullmatch(r"python(?:3(?:\.\d+)?)?", name):
            if len(args) < 2 or args[0] != "-m":
                return False
            name, args = args[1], args[2:]
        is_check = (
            name in {"pytest", "unittest", "mypy", "pyright"}
            or (name == "ruff" and args[:1] == ["check"])
            or (name in {"cargo", "go"} and args[:1] in (["check"], ["test"]))
            or (name == "make" and args[:1] in (["test"], ["build"], ["lint"], ["typecheck"]))
            or (name in {"npm", "pnpm", "yarn"} and (
                args[:1] in (["test"], ["build"], ["lint"], ["typecheck"])
                or args[:2] in (["run", "test"], ["run", "build"], ["run", "lint"], ["run", "typecheck"])
            ))
        )
        if not is_check:
            return False
        accepted = True
    return accepted


def _command_evidence(
    commands: Sequence[dict[str, Any]], checks: Sequence[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool, bool]:
    evidence: list[dict[str, Any]] = []
    latest_executor_checks: dict[str, tuple[bool, bool]] = {}
    latest_explicit_checks: dict[str, tuple[bool, bool]] = {}
    for index, item in enumerate((*commands, *checks)):
        command = str(item.get("command", ""))
        exit_code = item.get("exit_code")
        explicit_check = index >= len(commands)
        is_acceptance = _is_acceptance_command(command)
        is_check = explicit_check or is_acceptance or command == "git diff --check"
        if is_check:
            # Retain the history below, but let a successful rerun resolve the
            # same check. A different command cannot clear its failure.
            succeeded = exit_code == 0 and not item.get("error")
            target = latest_explicit_checks if explicit_check else latest_executor_checks
            target[command] = (is_acceptance and succeeded, not succeeded)
        if is_check or exit_code not in (0, None):
            evidence.append(
                {
                    "kind": "command",
                    "command": command,
                    "exit_code": exit_code,
                    "acceptance_check": is_acceptance,
                }
            )
            if item.get("error"):
                evidence[-1]["error"] = str(item["error"])
    all_checks = (*latest_executor_checks.values(), *latest_explicit_checks.values())
    acceptance_passed = any(passed for passed, _ in all_checks)
    explicit_acceptance_passed = any(
        passed for passed, _ in latest_explicit_checks.values()
    )
    explicit_failed = any(failed for _, failed in latest_explicit_checks.values())
    executor_failed = any(failed for _, failed in latest_executor_checks.values())
    # A caller-supplied acceptance check is the final acceptance run. If it
    # passes, exploratory failures retained from the executor remain evidence
    # but do not poison the outcome. Hygiene-only checks such as diff-check do
    # not have that authority.
    failed = explicit_failed or (executor_failed and not explicit_acceptance_passed)
    return evidence, acceptance_passed, failed


def evaluate_result(
    *,
    task_kind: TaskKind,
    executor_succeeded: bool,
    output: str,
    commands: Sequence[dict[str, Any]],
    checks: Sequence[dict[str, Any]],
    changed_paths: Sequence[str],
) -> Evaluation:
    evidence, acceptance_passed, command_failed = _command_evidence(commands, checks)
    if not executor_succeeded:
        evidence.append({"kind": "executor", "succeeded": False})
        return Evaluation(EvaluationStatus.FAIL, tuple(evidence), "Review the executor error.")
    if command_failed:
        return Evaluation(EvaluationStatus.FAIL, tuple(evidence), "A deterministic check failed.")

    if task_kind == TaskKind.RESEARCH:
        urls = tuple(dict.fromkeys(_URL.findall(output)))
        evidence.append({"kind": "sources", "count": len(urls), "urls": list(urls[:12])})
        if not urls:
            return Evaluation(
                EvaluationStatus.FAIL,
                tuple(evidence),
                "Research output has no traceable source URL.",
            )
        evidence.append(
            {
                "kind": "research_quality",
                "source_freshness": "not_fully_deterministic",
                "primary_source_status": "not_fully_deterministic",
                "contradiction_status": "not_fully_deterministic",
            }
        )
        return Evaluation(
            EvaluationStatus.PARTIAL,
            tuple(evidence),
            "Source presence is verified; freshness and claim quality still need judgment.",
        )

    if acceptance_passed:
        return Evaluation(EvaluationStatus.PASS, tuple(evidence), None)
    if task_kind == TaskKind.CODING and changed_paths:
        return Evaluation(
            EvaluationStatus.PARTIAL,
            tuple(evidence),
            "Repository changes exist, but no acceptance test was observed.",
        )
    return Evaluation(
        EvaluationStatus.UNKNOWN,
        tuple(evidence),
        "No deterministic acceptance check was available; confirm the result.",
    )

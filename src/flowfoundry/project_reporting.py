"""Canonical, low-ceremony handoff reports for substantial project work."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence


_SLUG = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class TaskReport:
    task: str
    slug: str
    status: str
    goal: str
    base_head: str
    final_judgment: str
    what_changed: Sequence[str]
    tests_run: Sequence[str]
    test_results: Sequence[str]
    failures: Sequence[str] = ()
    dogfood_results: Sequence[str] = ()
    benchmarks: Sequence[str] = ()
    external_software: Sequence[str] = ()
    deferred: Sequence[str] = ()
    remote_mutations: str = "NONE"
    next_actions: Sequence[str] = ()
    complete_result: str = ""


@dataclass(frozen=True)
class ReportPaths:
    report: Path
    latest: Path


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, timeout=20
    )
    return completed.stdout.strip() if completed.returncode == 0 else "UNKNOWN"


def _items(values: Sequence[str], empty: str = "NONE") -> str:
    return "\n".join(f"- {value}" for value in values) if values else f"- {empty}"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def _copy_to_clipboard(content: str) -> str:
    """Copy the complete report when a desktop clipboard helper is available."""
    for tool, args in (
        ("wl-copy", ()),
        ("xclip", ("-selection", "clipboard")),
        ("xsel", ("--clipboard", "--input")),
    ):
        executable = shutil.which(tool)
        if not executable:
            continue
        command = [executable, *args]
        try:
            subprocess.run(
                command,
                input=content,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                timeout=5,
            )
            return tool
        except (OSError, subprocess.SubprocessError):
            continue
    return "unavailable"


def _changed_files(root: Path) -> tuple[list[str], list[str], list[str]]:
    lines = _git(root, "status", "--short", "--untracked-files=all").splitlines()
    changed = [line for line in lines if line]
    added = [line[3:] for line in changed if line[:2].strip() in {"A", "??"}]
    removed = [line[3:] for line in changed if "D" in line[:2]]
    return changed, added, removed


def save_task_report(
    root: Path,
    report: TaskReport,
    *,
    now: datetime | None = None,
    copy_to_clipboard: bool = True,
) -> ReportPaths:
    """Write one canonical report and update the small latest-work pointer."""

    root = root.resolve()
    moment = now or datetime.now().astimezone()
    slug = _SLUG.sub("-", report.slug.casefold()).strip("-")[:48]
    if not slug:
        raise ValueError("report slug must contain letters or numbers")
    reports_root = root / ".ai" / "reports"
    reports_root.mkdir(parents=True, exist_ok=True)
    report_path = reports_root / f"{moment:%Y-%m-%d-%H%M}-{slug}.md"
    latest_path = root / ".ai" / "LATEST.md"
    if report_path.exists():
        raise FileExistsError(f"report already exists: {report_path}")

    branch = _git(root, "branch", "--show-current") or "DETACHED"
    final_head = _git(root, "rev-parse", "HEAD")
    changed, added, removed = _changed_files(root)
    relative_report = report_path.relative_to(root)
    complete_result_section = (
        "\n## Complete final result\n\n" + report.complete_result + "\n"
        if report.complete_result
        else ""
    )
    body = f"""# {report.task}

TASK: {report.task}

DATE: {moment.isoformat(timespec="minutes")}

BASE HEAD: {report.base_head}

BRANCH: {branch}

FINAL HEAD: {final_head}

STATUS: {report.status}

## Goal

{report.goal}

## What changed

{_items(report.what_changed)}

## Files changed

{_items(changed)}

## Files removed

{_items(removed)}

## Files added

{_items(added)}

## Tests run

{_items(report.tests_run)}

## Test results

{_items(report.test_results)}

## Failures

{_items(report.failures)}

## Dogfood results

{_items(report.dogfood_results)}

## Benchmarks

{_items(report.benchmarks)}

## External software used

{_items(report.external_software)}

## Deferred items

{_items(report.deferred)}

## Remote mutations

{report.remote_mutations}

## Final judgment

{report.final_judgment}
{complete_result_section}

## Next three actions

{_items(tuple(report.next_actions)[:3])}
"""
    _atomic_write(report_path, body)
    _atomic_write(
        latest_path,
        f"""# Latest Work

Latest report: `{relative_report}`

Task: {report.task}

Date: {moment.isoformat(timespec="minutes")}

Branch: {branch}

HEAD: {final_head}

Status: {report.status}

Final judgment: {report.final_judgment}
        """,
    )
    if copy_to_clipboard:
        _copy_to_clipboard(body)
    return ReportPaths(report=report_path, latest=latest_path)

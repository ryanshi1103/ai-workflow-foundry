"""Transcript and documentation output stages for session finalization."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ...lifecycle.git_manager import git_status
from ...policy.redact import redact_jsonl
from ...policy.runtime import (
    atomic_copy,
    atomic_write_json,
    compute_sha256,
    ensure_dir,
    read_json,
)
from ..transcript_claude import (
    extract_accomplishments as claude_accomplishments,
)
from ..transcript_claude import extract_conversation_markdown as claude_md
from ..transcript_claude import extract_decisions as claude_decisions
from ..transcript_claude import extract_first_prompt as claude_first_prompt
from ..transcript_claude import parse_claude_transcript
from ..transcript_codex import extract_accomplishments as codex_accomplishments
from ..transcript_codex import extract_conversation_markdown as codex_md
from ..transcript_codex import extract_decisions as codex_decisions
from ..transcript_codex import extract_first_prompt as codex_first_prompt
from ..transcript_codex import parse_codex_transcript


@dataclass(frozen=True)
class TranscriptSummary:
    """Deterministic metadata extracted from a provider transcript."""

    first_prompt: str
    accomplishments: list[str]
    decisions: list[str]

    @property
    def goal(self) -> str:
        return self.first_prompt[:300]


def sync_transcript(
    project_dir: Path,
    session_dir: Path,
    session_meta: dict | None,
) -> None:
    """Copy the provider transcript to private session storage."""
    if not session_meta or not session_dir:
        return
    transcript_source = session_meta.get("transcript_source", "")
    if not transcript_source:
        return
    source_path = Path(transcript_source)
    if not source_path.exists():
        return

    private_dir = project_dir / ".ai-session" / "private" / session_dir.name
    ensure_dir(private_dir)
    try:
        private_dir.chmod(0o700)
    except OSError:
        pass

    raw_destination = private_dir / "transcript.raw.jsonl"
    try:
        atomic_copy(source_path, raw_destination)
        raw_destination.chmod(0o600)
    except OSError:
        pass


def update_transcript_hash(
    session_dir: Path,
    session_meta: dict | None,
) -> None:
    """Compute and persist the private transcript hash."""
    if not session_dir or not session_meta:
        return
    raw_destination = (
        session_dir.parent.parent
        / "private"
        / session_dir.name
        / "transcript.raw.jsonl"
    )
    if not raw_destination.exists():
        return

    transcript_hash = compute_sha256(raw_destination)
    session_meta["transcript_hash"] = transcript_hash
    (session_dir / "transcript.sha256").write_text(
        f"{transcript_hash}  transcript.raw.jsonl\n",
        encoding="utf-8",
    )
    atomic_write_json(session_dir / "meta.json", session_meta)


def parse_transcript(session_dir: Path, tool: str) -> list[dict]:
    """Parse a private or redacted transcript for the selected tool."""
    if not session_dir:
        return []
    private_raw = (
        session_dir.parent.parent
        / "private"
        / session_dir.name
        / "transcript.raw.jsonl"
    )
    transcript_path = private_raw if private_raw.exists() else None
    if not transcript_path:
        redacted = session_dir / "transcript.redacted.jsonl"
        if redacted.exists():
            transcript_path = redacted
    if not transcript_path:
        return []
    if tool == "codex":
        return parse_codex_transcript(transcript_path)
    return parse_claude_transcript(transcript_path)


def ensure_redacted_transcript(project_dir: Path, session_dir: Path) -> None:
    """Generate the tracked redacted transcript if it does not exist."""
    if not session_dir:
        return
    redacted_destination = session_dir / "transcript.redacted.jsonl"
    if redacted_destination.exists():
        return
    private_raw = (
        project_dir
        / ".ai-session"
        / "private"
        / session_dir.name
        / "transcript.raw.jsonl"
    )
    if not private_raw.exists():
        return
    _line_count, had_sensitive = redact_jsonl(private_raw, redacted_destination)
    session_meta = read_json(session_dir / "meta.json")
    if session_meta:
        session_meta["redaction_applied"] = had_sensitive
        atomic_write_json(session_dir / "meta.json", session_meta)


def summarize_transcript(events: list[dict], tool: str) -> TranscriptSummary:
    """Extract the first prompt, accomplishments, and decisions."""
    if tool == "codex":
        first_prompt = codex_first_prompt(events)
        accomplishments = codex_accomplishments(events)
        decisions = codex_decisions(events)
    else:
        first_prompt = claude_first_prompt(events)
        accomplishments = claude_accomplishments(events)
        decisions = claude_decisions(events)
    if not first_prompt:
        raise RuntimeError("Transcript parsing produced no real user prompt")
    return TranscriptSummary(first_prompt, accomplishments, decisions)


def generate_conversation(
    project_dir: Path,
    session_dir: Path,
    events: list[dict],
    tool: str,
) -> None:
    """Generate conversation.md from parsed transcript events."""
    if not session_dir or not events:
        return
    docs_session_dir = project_dir / "docs" / "sessions" / session_dir.name
    ensure_dir(docs_session_dir)
    content = codex_md(events, "Codex") if tool == "codex" else claude_md(events, "Claude")
    (docs_session_dir / "conversation.md").write_text(content, encoding="utf-8")


def write_session_docs(
    project_dir: Path,
    session_id: str,
    tool: str,
    summary: TranscriptSummary,
    status: str,
) -> None:
    """Write deterministic per-session documentation."""
    docs_session_dir = project_dir / "docs" / "sessions" / session_id
    ensure_dir(docs_session_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    summary_lines = [
        f"# Session {session_id} Summary",
        "",
        f"**Tool:** {tool}",
        f"**Status:** {status}",
        f"**Generated:** {timestamp}",
        "",
        "## Goal",
        "",
        summary.goal,
        "",
        "## Completed",
        "",
    ]
    summary_lines.extend(f"- {item}" for item in summary.accomplishments[:30])
    if not summary.accomplishments:
        summary_lines.append("- (None extracted)")
    summary_lines.extend(["", "## Decisions", ""])
    summary_lines.extend(f"- {item}" for item in summary.decisions[:20])
    if not summary.decisions:
        summary_lines.append("- (None extracted)")
    summary_lines.extend(["", "## Status", "", status])
    (docs_session_dir / "summary.md").write_text(
        "\n".join(summary_lines), encoding="utf-8"
    )

    decision_lines = [
        f"# Session {session_id} Decisions",
        "",
        "## 当前有效决定",
        "",
    ]
    decision_lines.extend(f"- {item}" for item in summary.decisions[:30])
    if not summary.decisions:
        decision_lines.append("- (No decisions extracted)")
    (docs_session_dir / "decisions.md").write_text(
        "\n".join(decision_lines), encoding="utf-8"
    )

    task_lines = [f"# Session {session_id} Tasks", "", "## 已完成", ""]
    task_lines.extend(f"- [x] {item}" for item in summary.accomplishments[:30])
    task_lines.extend(["", "## 未完成", "", "- (None recorded)"])
    (docs_session_dir / "tasks.md").write_text(
        "\n".join(task_lines), encoding="utf-8"
    )
    (docs_session_dir / "status.md").write_text(
        f"# Status: {status}\n\nSession: {session_id}\nGenerated: {timestamp}\n",
        encoding="utf-8",
    )


def merge_project_docs(
    project_dir: Path,
    session_id: str,
    summary: TranscriptSummary,
    status: str,
) -> None:
    """Merge session data into project-level documents."""
    docs_dir = project_dir / "docs"
    ensure_dir(docs_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    _merge_summary(
        docs_dir,
        session_id,
        summary.goal,
        summary.accomplishments,
        status,
        timestamp,
    )
    _merge_decisions(docs_dir, session_id, summary.decisions)
    _merge_tasks(docs_dir, session_id, summary.accomplishments)
    _merge_files_changed(docs_dir, project_dir, session_id, timestamp)


def _merge_summary(
    docs_dir: Path,
    session_id: str,
    goal: str,
    accomplishments: list[str],
    status: str,
    timestamp: str,
) -> None:
    summary_path = docs_dir / "summary.md"
    if not summary_path.exists():
        summary_path.write_text(
            "# Project Summary\n\n## Sessions\n\n", encoding="utf-8"
        )
    content = summary_path.read_text(encoding="utf-8")
    marker = f"### {session_id}"
    entry = [
        "",
        marker,
        f"**Status:** {status} | **Updated:** {timestamp}",
        f"**Goal:** {goal[:300]}",
        "",
    ]
    if accomplishments:
        entry.append("**Key accomplishments:**")
        entry.extend(f"- {item}" for item in accomplishments[:10])
        entry.append("")
    entry_text = "\n".join(entry)
    if marker in content:
        start = content.rfind("\n", 0, content.index(marker)) + 1
        next_entry = content.find("\n### ", start + 1)
        end = next_entry if next_entry >= 0 else len(content)
        content = (
            content[:start]
            + entry_text.lstrip("\n")
            + "\n"
            + content[end:].lstrip("\n")
        )
    else:
        insert_pos = content.find("## Sessions")
        if insert_pos >= 0:
            insert_pos = content.find("\n", insert_pos) + 1
            content = content[:insert_pos] + entry_text + content[insert_pos:]
        else:
            content += entry_text
    summary_path.write_text(content, encoding="utf-8")


def _merge_decisions(
    docs_dir: Path,
    session_id: str,
    decisions: list[str],
) -> None:
    decision_path = docs_dir / "decisions.md"
    if not decision_path.exists():
        decision_path.write_text(
            "# Project Decisions\n\n## 当前有效决定\n\n"
            "## 已替代决定\n\n## 待确认决定\n\n",
            encoding="utf-8",
        )
    if not decisions:
        return
    content = decision_path.read_text(encoding="utf-8")
    section = content.find("## 当前有效决定")
    if section < 0:
        return
    insert_pos = content.find("\n", section) + 1
    additions = (
        "\n".join(
            f"<!-- session:{session_id} -->\n- {decision}"
            for decision in decisions[:20]
        )
        + "\n"
    )
    decision_path.write_text(
        content[:insert_pos] + additions + content[insert_pos:], encoding="utf-8"
    )


def _merge_tasks(
    docs_dir: Path,
    session_id: str,
    accomplishments: list[str],
) -> None:
    tasks_path = docs_dir / "tasks.md"
    if not tasks_path.exists():
        tasks_path.write_text(
            "# Project Tasks\n\n## 已完成\n\n## 进行中\n\n## 未完成\n\n"
            "## 已取消\n\n## 等待用户确认\n\n",
            encoding="utf-8",
        )
    if not accomplishments:
        return
    content = tasks_path.read_text(encoding="utf-8")
    section = content.find("## 已完成")
    if section < 0:
        return
    insert_pos = content.find("\n", section) + 1
    additions = (
        "\n".join(
            f"<!-- session:{session_id} -->\n- [x] {item}"
            for item in accomplishments[:20]
        )
        + "\n"
    )
    tasks_path.write_text(
        content[:insert_pos] + additions + content[insert_pos:], encoding="utf-8"
    )


def _merge_files_changed(
    docs_dir: Path,
    project_dir: Path,
    session_id: str,
    timestamp: str,
) -> None:
    files_path = docs_dir / "files-changed.md"
    if not files_path.exists():
        files_path.write_text("# Files Changed\n\n", encoding="utf-8")
    state = git_status(project_dir)
    all_files = state["staged_files"] + state["changed_files"] + state["untracked_files"]
    if not all_files:
        return
    content = files_path.read_text(encoding="utf-8")
    entry = [f"## {session_id} ({timestamp})", ""]
    entry.extend(f"- {name}" for name in all_files[:50])
    entry.append("")
    files_path.write_text(content + "\n".join(entry), encoding="utf-8")


def update_readme(project_dir: Path, goal: str, status: str, tool: str) -> None:
    """Update the project README with the final session state."""
    readme_path = project_dir / "README.md"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    if not readme_path.exists():
        readme_path.write_text(
            f"# Project ({tool})\n\n## 项目目标\n\n{goal}\n\n"
            f"## 当前状态\n\n{status}\n\n## 最后更新时间\n\n{timestamp}\n",
            encoding="utf-8",
        )
        return
    content = readme_path.read_text(encoding="utf-8")
    content = re.sub(r"## 当前状态\n\n.*?\n", f"## 当前状态\n\n{status}\n", content)
    content = re.sub(
        r"## 最后更新时间\n\n.*",
        f"## 最后更新时间\n\n{timestamp}",
        content,
    )
    readme_path.write_text(content, encoding="utf-8")

"""Session finalization — document generation, merging, git commit, project renaming."""

import re
from datetime import datetime, timezone
from pathlib import Path

from ..git_manager import (
    build_commit_message,
    git_add_all_safe,
    git_commit,
    git_status,
)
from ..project import update_project_status
from ..redact import redact_jsonl
from ..transcript_claude import (
    extract_accomplishments as claude_accomplishments,
)
from ..transcript_claude import (
    extract_conversation_markdown as claude_md,
)
from ..transcript_claude import (
    extract_decisions as claude_decisions,
)
from ..transcript_claude import (
    extract_first_prompt as claude_first_prompt,
)
from ..transcript_claude import (
    parse_claude_transcript,
)
from ..transcript_codex import (
    extract_accomplishments as codex_accomplishments,
)
from ..transcript_codex import (
    extract_conversation_markdown as codex_md,
)
from ..transcript_codex import (
    extract_decisions as codex_decisions,
)
from ..transcript_codex import (
    extract_first_prompt as codex_first_prompt,
)
from ..transcript_codex import (
    parse_codex_transcript,
)
from ..utils import (
    atomic_copy,
    atomic_write_json,
    compute_sha256,
    compute_text_hash,
    ensure_dir,
    file_lock,
    read_json,
    sanitize_project_title,
    timestamp_iso,
)


def finalize_session(
    project_dir: Path,
    session_id: str | None = None,
    tool: str = "claude",
    use_ai: bool = False,
) -> dict:
    """Main finalization routine. Idempotent.

    Returns a result dict with status information.
    """
    result = {
        "success": False,
        "status": "unknown",
        "commit": None,
        "session_id": session_id,
        "error": None,
    }

    project_dir = Path(project_dir).resolve()
    if not project_dir.exists():
        result["error"] = f"Project directory does not exist: {project_dir}"
        return result

    # Get lock
    lock_file = project_dir / ".ai-session" / "finalize.lock"
    try:
        with file_lock(lock_file, timeout=30.0):
            return _finalize_impl(project_dir, session_id, tool, use_ai, result)
    except TimeoutError:
        result["error"] = (
            "Could not acquire finalize lock (another finalize in progress?)"
        )
        return result


def _finalize_impl(
    project_dir: Path, session_id: str | None, tool: str, use_ai: bool, result: dict
) -> dict:
    """Internal finalize implementation (lock already held)."""

    # Read project meta
    meta = read_json(project_dir / ".ai-session" / "project.json")
    if not meta:
        result["error"] = "No project.json found"
        return result

    # Check if already finalized.  The commit id deliberately lives outside
    # tracked metadata to avoid a commit referring to its own hash.
    if meta.get("status") in ("completed", "interrupted"):
        private_final = (
            read_json(
                project_dir
                / ".ai-session"
                / "private"
                / (session_id or meta.get("session_id", ""))
                / "finalization.json"
            )
            or {}
        )
        result["success"] = True
        result["status"] = meta["status"]
        result["commit"] = private_final.get("final_commit")
        result["message"] = "Session already finalized"
        return result

    # Find session
    if not session_id:
        session_id = meta.get("session_id", "")
    if not session_id:
        result["error"] = "No session_id found"
        return result

    session_dir = project_dir / ".ai-session" / "sessions" / session_id
    session_meta = (
        read_json(session_dir / "meta.json") if session_dir.exists() else None
    )

    # Determine tool
    actual_tool = meta.get("tool", tool)

    try:
        # Step 1: Sync transcript
        _final_sync_transcript(project_dir, session_dir, session_meta, actual_tool)

        # Step 2: Compute transcript hash, then discard stale in-memory meta.
        _update_transcript_hash(session_dir, session_meta)
        session_meta = read_json(session_dir / "meta.json") or {}

        # Step 3: Parse transcript and generate conversation.md
        events = _parse_transcript(session_dir, actual_tool)

        # Step 4: Generate redacted transcript if needed
        _ensure_redacted_transcript(project_dir, session_dir, actual_tool)

        # Step 5: Generate conversation.md
        _generate_conversation_md(project_dir, session_dir, events, actual_tool)

        # Step 6: Extract metadata
        first_prompt = _extract_first_prompt(events, actual_tool)
        accomplishments = _extract_accomplishments(events, actual_tool)
        decisions = _extract_decisions(events, actual_tool)
        if not first_prompt:
            raise RuntimeError("Transcript parsing produced no real user prompt")
        goal = first_prompt[:300]

        # Step 7: Determine status
        final_status = "completed"

        # Step 8: Update session documents
        _update_session_docs(
            project_dir,
            session_dir,
            session_id,
            events,
            actual_tool,
            goal,
            accomplishments,
            decisions,
            final_status,
        )

        # Step 9: Merge into project-level docs
        _merge_project_docs(
            project_dir,
            session_id,
            goal,
            accomplishments,
            decisions,
            final_status,
            actual_tool,
        )

        # Step 10: Update README
        _update_readme(project_dir, goal, final_status, actual_tool)

        # Step 11: Write every tracked final field before staging. final_commit
        # is intentionally excluded and stored in ignored/global state later.
        transcript_hash = session_meta.get("transcript_hash")
        first_prompt_hash = compute_text_hash(first_prompt)
        final_fields = {
            "end_time": timestamp_iso(),
            "summary_success": True,
            "summary_mode": "deterministic",
            "first_prompt_hash": first_prompt_hash,
            "transcript_hash": transcript_hash,
            "redaction_applied": bool(session_meta.get("redaction_applied", False)),
            "finalize_attempts": max(
                int(meta.get("finalize_attempts", 0)),
                int(session_meta.get("finalize_attempts", 0)),
            )
            + 1,
            "last_error": None,
            "final_commit": None,
        }
        if not transcript_hash:
            raise RuntimeError("Transcript hash was not generated")
        if not update_project_status(
            project_dir,
            final_status,
            session_id=session_id,
            tool=actual_tool,
            metadata=final_fields,
        ):
            raise RuntimeError("Could not synchronize final metadata")
        meta = read_json(project_dir / ".ai-session" / "project.json") or meta
        session_meta = read_json(session_dir / "meta.json") or session_meta

        # Step 12: Safe staging and commit.
        commit_result = _do_git_commit(
            project_dir,
            session_id,
            actual_tool,
            meta,
            goal,
            accomplishments,
            decisions,
            final_status,
            session_meta,
        )
        final_commit = commit_result.get("commit")
        if not commit_result.get("success"):
            _write_staging_problems(
                project_dir, session_id, commit_result.get("stage_result", {})
            )
            update_project_status(
                project_dir, "failed", session_id=session_id, tool=actual_tool
            )
            result.update(
                status="failed",
                error=commit_result.get("error", "safe staging failed"),
                stage_result=commit_result.get("stage_result"),
            )
            return result

        # Step 13: Persist the hash only in ignored private state and the
        # global index. Tracked files are never touched after the commit.
        _record_final_commit(project_dir, session_id, actual_tool, final_commit)

        result["success"] = True
        result["status"] = final_status
        result["commit"] = final_commit
        return result

    except Exception as e:
        # Record error but don't lose data
        result["error"] = str(e)
        current_session = read_json(session_dir / "meta.json") or {}
        failure_fields = {
            "end_time": timestamp_iso(),
            "summary_success": False,
            "summary_mode": "deterministic",
            "first_prompt_hash": current_session.get("first_prompt_hash")
            or meta.get("first_prompt_hash"),
            "transcript_hash": current_session.get("transcript_hash")
            or meta.get("transcript_hash"),
            "redaction_applied": bool(current_session.get("redaction_applied", False)),
            "finalize_attempts": max(
                int(meta.get("finalize_attempts", 0)),
                int(current_session.get("finalize_attempts", 0)),
            )
            + 1,
            "last_error": str(e),
            "final_commit": None,
        }
        update_project_status(
            project_dir,
            "failed",
            session_id=session_id,
            tool=actual_tool,
            metadata=failure_fields,
        )
        result["status"] = "failed"
        return result


def _record_final_commit(
    project_dir: Path, session_id: str, tool: str, final_commit: str | None
) -> None:
    """Record a commit id without modifying files contained in that commit."""
    from ..utils import GLOBAL_LOCK_FILE, STATE_DIR

    private_dir = project_dir / ".ai-session" / "private" / session_id
    ensure_dir(private_dir, 0o700)
    atomic_write_json(
        private_dir / "finalization.json",
        {
            "session_id": session_id,
            "status": "completed",
            "final_commit": final_commit,
            "recorded_at": timestamp_iso(),
        },
    )
    index_path = STATE_DIR / "project-index.json"
    with file_lock(GLOBAL_LOCK_FILE):
        index = read_json(index_path) or {"projects": {}}
        entry = index.setdefault("projects", {}).setdefault(session_id, {})
        entry.update(
            {
                "path": str(project_dir),
                "tool": tool,
                "status": "completed",
                "final_commit": final_commit,
                "last_updated": timestamp_iso(),
            }
        )
        atomic_write_json(index_path, index)


def _final_sync_transcript(
    project_dir: Path, session_dir: Path, session_meta: dict | None, tool: str
) -> None:
    """Final transcript sync — copy raw to private, compute hash."""
    if not session_meta or not session_dir:
        return

    transcript_source = session_meta.get("transcript_source", "")
    if not transcript_source:
        return

    src_path = Path(transcript_source)
    if not src_path.exists():
        return

    # Copy raw transcript to private
    private_dir = project_dir / ".ai-session" / "private" / session_dir.name
    ensure_dir(private_dir)
    try:
        private_dir.chmod(0o700)
    except OSError:
        pass

    raw_dest = private_dir / "transcript.raw.jsonl"
    try:
        atomic_copy(src_path, raw_dest)
        raw_dest.chmod(0o600)
    except OSError:
        pass


def _update_transcript_hash(session_dir: Path, session_meta: dict | None) -> None:
    """Compute and save transcript hash."""
    if not session_dir or not session_meta:
        return

    raw_dest = (
        session_dir.parent.parent
        / "private"
        / session_dir.name
        / "transcript.raw.jsonl"
    )
    if not raw_dest.exists():
        return

    transcript_hash = compute_sha256(raw_dest)
    session_meta["transcript_hash"] = transcript_hash

    hash_file = session_dir / "transcript.sha256"
    hash_file.write_text(f"{transcript_hash}  transcript.raw.jsonl\n", encoding="utf-8")
    atomic_write_json(session_dir / "meta.json", session_meta)


def _parse_transcript(session_dir: Path, tool: str) -> list[dict]:
    """Parse transcript based on tool type."""
    if not session_dir:
        return []

    # Try raw transcript first, then redacted
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
    else:
        return parse_claude_transcript(transcript_path)


def _ensure_redacted_transcript(
    project_dir: Path, session_dir: Path, tool: str
) -> None:
    """Ensure redacted transcript exists."""
    if not session_dir:
        return

    redacted_dest = session_dir / "transcript.redacted.jsonl"
    if redacted_dest.exists():
        return

    private_raw = (
        project_dir
        / ".ai-session"
        / "private"
        / session_dir.name
        / "transcript.raw.jsonl"
    )
    if private_raw.exists():
        line_count, had_sensitive = redact_jsonl(private_raw, redacted_dest)
        session_meta = read_json(session_dir / "meta.json")
        if session_meta:
            session_meta["redaction_applied"] = had_sensitive
            atomic_write_json(session_dir / "meta.json", session_meta)


def _extract_first_prompt(events: list[dict], tool: str) -> str | None:
    """Extract first user prompt from events."""
    if tool == "codex":
        return codex_first_prompt(events)
    return claude_first_prompt(events)


def _extract_accomplishments(events: list[dict], tool: str) -> list[str]:
    """Extract accomplishments from events."""
    if tool == "codex":
        return codex_accomplishments(events)
    return claude_accomplishments(events)


def _extract_decisions(events: list[dict], tool: str) -> list[str]:
    """Extract decisions from events."""
    if tool == "codex":
        return codex_decisions(events)
    return claude_decisions(events)


def _generate_conversation_md(
    project_dir: Path, session_dir: Path, events: list[dict], tool: str
) -> None:
    """Generate conversation.md from parsed events."""
    if not session_dir or not events:
        return

    docs_session_dir = project_dir / "docs" / "sessions" / session_dir.name
    ensure_dir(docs_session_dir)

    if tool == "codex":
        md_content = codex_md(events, "Codex")
    else:
        md_content = claude_md(events, "Claude")

    convo_path = docs_session_dir / "conversation.md"
    convo_path.write_text(md_content, encoding="utf-8")


def _update_session_docs(
    project_dir: Path,
    session_dir: Path,
    session_id: str,
    events: list[dict],
    tool: str,
    goal: str,
    accomplishments: list[str],
    decisions: list[str],
    status: str,
) -> None:
    """Update per-session documentation."""
    if not session_dir:
        return

    docs_session_dir = project_dir / "docs" / "sessions" / session_id
    ensure_dir(docs_session_dir)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # summary.md
    summary = [
        f"# Session {session_id} Summary",
        "",
        f"**Tool:** {tool}",
        f"**Status:** {status}",
        f"**Generated:** {ts}",
        "",
        "## Goal",
        "",
        goal,
        "",
        "## Completed",
        "",
    ]
    for item in accomplishments[:30]:
        summary.append(f"- {item}")
    if not accomplishments:
        summary.append("- (None extracted)")
    summary.extend(["", "## Decisions", ""])
    for item in decisions[:20]:
        summary.append(f"- {item}")
    if not decisions:
        summary.append("- (None extracted)")
    summary.extend(["", "## Status", "", status])

    (docs_session_dir / "summary.md").write_text("\n".join(summary), encoding="utf-8")

    # decisions.md
    dec_content = [
        f"# Session {session_id} Decisions",
        "",
        "## 当前有效决定",
        "",
    ]
    for item in decisions[:30]:
        dec_content.append(f"- {item}")
    if not decisions:
        dec_content.append("- (No decisions extracted)")
    (docs_session_dir / "decisions.md").write_text(
        "\n".join(dec_content), encoding="utf-8"
    )

    # tasks.md
    tasks_content = [
        f"# Session {session_id} Tasks",
        "",
        "## 已完成",
        "",
    ]
    for item in accomplishments[:30]:
        tasks_content.append(f"- [x] {item}")
    tasks_content.append("")
    tasks_content.append("## 未完成")
    tasks_content.append("")
    tasks_content.append("- (None recorded)")
    (docs_session_dir / "tasks.md").write_text(
        "\n".join(tasks_content), encoding="utf-8"
    )

    # status.md
    (docs_session_dir / "status.md").write_text(
        f"# Status: {status}\n\nSession: {session_id}\nGenerated: {ts}\n",
        encoding="utf-8",
    )


def _merge_project_docs(
    project_dir: Path,
    session_id: str,
    goal: str,
    accomplishments: list[str],
    decisions: list[str],
    status: str,
    tool: str,
) -> None:
    """Merge session data into project-level aggregated documents."""
    docs_dir = project_dir / "docs"
    ensure_dir(docs_dir)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    _merge_summary(docs_dir, session_id, goal, accomplishments, status, ts)
    _merge_decisions(docs_dir, session_id, decisions, ts)
    _merge_tasks(docs_dir, session_id, accomplishments, ts)
    _merge_files_changed(docs_dir, project_dir, session_id, ts)


def _merge_summary(
    docs_dir: Path,
    session_id: str,
    goal: str,
    accomplishments: list[str],
    status: str,
    ts: str,
) -> None:
    """Merge into project summary.md."""
    summary_path = docs_dir / "summary.md"
    if not summary_path.exists():
        summary_path.write_text(
            "# Project Summary\n\n## Sessions\n\n", encoding="utf-8"
        )

    content = summary_path.read_text(encoding="utf-8")

    # Replace an existing generated entry as well as adding a new one.  This
    # repairs prior failed summaries and makes regeneration deterministic.
    session_marker = f"### {session_id}"
    entry = [
        "",
        f"### {session_id}",
        f"**Status:** {status} | **Updated:** {ts}",
        f"**Goal:** {goal[:300]}",
        "",
    ]
    if accomplishments:
        entry.append("**Key accomplishments:**")
        for acc in accomplishments[:10]:
            entry.append(f"- {acc}")
        entry.append("")
    entry_text = "\n".join(entry)
    if session_marker in content:
        start = content.index(session_marker)
        start = content.rfind("\n", 0, start) + 1
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
    docs_dir: Path, session_id: str, decisions: list[str], ts: str
) -> None:
    """Merge into project decisions.md."""
    dec_path = docs_dir / "decisions.md"
    if not dec_path.exists():
        dec_path.write_text(
            "# Project Decisions\n\n## 当前有效决定\n\n## 已替代决定\n\n## 待确认决定\n\n",
            encoding="utf-8",
        )

    if not decisions:
        return

    content = dec_path.read_text(encoding="utf-8")
    current_section = content.find("## 当前有效决定")
    if current_section < 0:
        return

    # Insert new decisions after the section header
    insert_pos = content.find("\n", current_section) + 1
    new_decisions = (
        "\n".join([f"<!-- session:{session_id} -->\n- {d}" for d in decisions[:20]])
        + "\n"
    )

    content = content[:insert_pos] + new_decisions + content[insert_pos:]
    dec_path.write_text(content, encoding="utf-8")


def _merge_tasks(
    docs_dir: Path, session_id: str, accomplishments: list[str], ts: str
) -> None:
    """Merge into project tasks.md."""
    tasks_path = docs_dir / "tasks.md"
    if not tasks_path.exists():
        tasks_path.write_text(
            "# Project Tasks\n\n## 已完成\n\n## 进行中\n\n## 未完成\n\n## 已取消\n\n## 等待用户确认\n\n",
            encoding="utf-8",
        )

    if not accomplishments:
        return

    content = tasks_path.read_text(encoding="utf-8")
    completed_section = content.find("## 已完成")
    if completed_section < 0:
        return

    insert_pos = content.find("\n", completed_section) + 1
    new_tasks = (
        "\n".join(
            [
                f"<!-- session:{session_id} -->\n- [x] {acc}"
                for acc in accomplishments[:20]
            ]
        )
        + "\n"
    )

    content = content[:insert_pos] + new_tasks + content[insert_pos:]
    tasks_path.write_text(content, encoding="utf-8")


def _merge_files_changed(
    docs_dir: Path, project_dir: Path, session_id: str, ts: str
) -> None:
    """Record files changed in this session."""
    files_path = docs_dir / "files-changed.md"
    if not files_path.exists():
        files_path.write_text("# Files Changed\n\n", encoding="utf-8")

    status = git_status(project_dir)
    all_files = (
        status["staged_files"] + status["changed_files"] + status["untracked_files"]
    )

    if not all_files:
        return

    content = files_path.read_text(encoding="utf-8")
    entry = [
        f"## {session_id} ({ts})",
        "",
    ]
    for f in all_files[:50]:
        entry.append(f"- {f}")
    entry.append("")

    content += "\n".join(entry)
    files_path.write_text(content, encoding="utf-8")


def _update_readme(project_dir: Path, goal: str, status: str, tool: str) -> None:
    """Update project README.md with current state."""
    readme_path = project_dir / "README.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if not readme_path.exists():
        readme_path.write_text(
            f"# Project ({tool})\n\n## 项目目标\n\n{goal}\n\n"
            f"## 当前状态\n\n{status}\n\n## 最后更新时间\n\n{ts}\n",
            encoding="utf-8",
        )
        return

    content = readme_path.read_text(encoding="utf-8")

    # Update status line
    content = re.sub(r"## 当前状态\n\n.*?\n", f"## 当前状态\n\n{status}\n", content)

    # Update timestamp
    content = re.sub(r"## 最后更新时间\n\n.*", f"## 最后更新时间\n\n{ts}", content)

    readme_path.write_text(content, encoding="utf-8")


def _do_git_commit(
    project_dir: Path,
    session_id: str,
    tool: str,
    meta: dict,
    goal: str,
    accomplishments: list[str],
    decisions: list[str],
    status: str,
    session_meta: dict | None,
) -> dict:
    """Stage files and create git commit."""
    gs = git_status(project_dir)
    if not gs["is_repo"]:
        return {
            "success": True,
            "commit": None,
            "stage_result": {
                "ok": True,
                "added": [],
                "skipped": [],
                "blocked": [],
                "errors": [],
                "index_committed": False,
                "nothing_to_commit": True,
            },
        }

    # Stage all safe files
    stage_result = git_add_all_safe(project_dir)
    safe = (
        stage_result.get("ok") is True
        and stage_result.get("index_committed") is True
        and stage_result.get("nothing_to_commit") is False
        and not stage_result.get("blocked")
        and not stage_result.get("errors")
    )
    if stage_result.get("ok") is True and stage_result.get("nothing_to_commit") is True:
        return {"success": True, "commit": None, "stage_result": stage_result}
    if not safe:
        return {
            "success": False,
            "commit": None,
            "stage_result": stage_result,
            "error": "safe staging blocked or failed",
        }

    # Get title from goal
    title = _derive_title(goal, tool)

    # Get transcript hash
    transcript_hash = ""
    if session_meta:
        transcript_hash = session_meta.get("transcript_hash", "")

    # Build commit message
    subject, body = build_commit_message(
        tool=tool,
        title=title,
        session_id=session_id,
        model=meta.get("model", ""),
        provider=meta.get("provider_or_profile", ""),
        status=status,
        start_time=meta.get("start_time", ""),
        end_time=timestamp_iso(),
        goal=goal[:300],
        decisions=decisions[:10],
        completed=accomplishments[:15],
        files_changed=stage_result["added"][:30],
        transcript_hash=transcript_hash,
        redaction=session_meta.get("redaction_applied", False)
        if session_meta
        else False,
        summary_mode=meta.get("summary_mode", "deterministic"),
    )

    h = git_commit(project_dir, subject, body)
    if not h:
        return {
            "success": False,
            "commit": None,
            "stage_result": stage_result,
            "error": "git commit failed",
        }
    return {"success": True, "commit": h, "stage_result": stage_result}


def _write_staging_problems(
    project_dir: Path, session_id: str, stage_result: dict
) -> None:
    p = project_dir / "docs/problems-and-solutions.md"
    ensure_dir(p.parent)
    if not p.exists():
        p.write_text("# Problems and Solutions\n\n", encoding="utf-8")
    lines = [f"\n## Safe staging failure ({session_id})", ""]
    for c in ("blocked", "errors"):
        lines.extend(f"- {c}: {x}" for x in stage_result.get(c, []))
    with p.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _derive_title(goal: str, tool: str) -> str:
    """Derive a short title from the first prompt."""
    if not goal:
        return f"{tool} session"

    # Remove common prefixes
    title = goal.strip()
    # Truncate to a reasonable title length
    if len(title) > 60:
        title = title[:57] + "..."

    # Sanitize
    title = sanitize_project_title(title, max_len=60)
    return title if title else f"{tool} session"


def _rename_project_if_possible(project_dir: Path, first_prompt: str) -> None:
    """Attempt to rename the project based on the first prompt."""
    from ..project import rename_project

    title = _derive_title(first_prompt, "")
    if not title or title in ("session", "claude session", "codex session"):
        return

    # Only rename if still has temp name pattern
    orig_name = project_dir.name
    # Temp name pattern: YYYYMMDD-HHMMSS-tool-shortid
    if not re.match(r"\d{8}-\d{6}-[a-z]+-[a-f0-9]{6}$", orig_name):
        return  # Already renamed

    rename_project(project_dir, title)

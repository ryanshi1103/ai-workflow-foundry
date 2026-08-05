"""Git and post-finalization hooks for the finalization pipeline."""

from __future__ import annotations

import re
from pathlib import Path

from ...lifecycle.git_manager import (
    build_commit_message,
    git_add_all_safe,
    git_commit,
    git_status,
)
from ...policy.runtime import (
    atomic_write_json,
    ensure_dir,
    file_lock,
    read_json,
    sanitize_project_title,
    timestamp_iso,
)


def run_git_finalize_hook(
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
    """Safely stage and commit the tracked finalization output."""
    git_state = git_status(project_dir)
    if not git_state["is_repo"]:
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

    transcript_hash = session_meta.get("transcript_hash", "") if session_meta else ""
    subject, body = build_commit_message(
        tool=tool,
        title=derive_title(goal, tool),
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
        redaction=(
            session_meta.get("redaction_applied", False) if session_meta else False
        ),
        summary_mode=meta.get("summary_mode", "deterministic"),
    )

    commit_hash = git_commit(project_dir, subject, body)
    if not commit_hash:
        return {
            "success": False,
            "commit": None,
            "stage_result": stage_result,
            "error": "git commit failed",
        }
    return {
        "success": True,
        "commit": commit_hash,
        "stage_result": stage_result,
    }


def record_final_commit(
    project_dir: Path,
    session_id: str,
    tool: str,
    final_commit: str | None,
) -> None:
    """Record a commit id without modifying files contained in that commit."""
    from ...policy.runtime import GLOBAL_LOCK_FILE, STATE_DIR

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


def write_staging_problems(
    project_dir: Path,
    session_id: str,
    stage_result: dict,
) -> None:
    """Append safe-staging failures to project documentation."""
    problems_path = project_dir / "docs/problems-and-solutions.md"
    ensure_dir(problems_path.parent)
    if not problems_path.exists():
        problems_path.write_text("# Problems and Solutions\n\n", encoding="utf-8")
    lines = [f"\n## Safe staging failure ({session_id})", ""]
    for category in ("blocked", "errors"):
        lines.extend(
            f"- {category}: {item}" for item in stage_result.get(category, [])
        )
    with problems_path.open("a", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")


def derive_title(goal: str, tool: str) -> str:
    """Derive a short, filesystem-safe title from the first prompt."""
    if not goal:
        return f"{tool} session"
    title = goal.strip()
    if len(title) > 60:
        title = title[:57] + "..."
    title = sanitize_project_title(title, max_len=60)
    return title if title else f"{tool} session"


def rename_project_if_possible(project_dir: Path, first_prompt: str) -> None:
    """Rename a temporary project from its first prompt when safe."""
    from ...lifecycle.project import rename_project

    title = derive_title(first_prompt, "")
    if not title or title in ("session", "claude session", "codex session"):
        return
    if not re.match(r"\d{8}-\d{6}-[a-z]+-[a-f0-9]{6}$", project_dir.name):
        return
    rename_project(project_dir, title)

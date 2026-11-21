"""Failure recording for recoverable finalization attempts."""

from __future__ import annotations

from pathlib import Path

from ...lifecycle.project import update_project_status
from ...policy.runtime import read_json, timestamp_iso


def record_finalization_failure(
    project_dir: Path,
    session_dir: Path,
    session_id: str,
    tool: str,
    project_meta: dict,
    error: Exception | str,
) -> None:
    """Persist enough failure metadata for a later retry or recovery."""
    message = str(error)
    current_session = read_json(session_dir / "meta.json") or {}
    failure_fields = {
        "end_time": timestamp_iso(),
        "summary_success": False,
        "summary_mode": "deterministic",
        "first_prompt_hash": current_session.get("first_prompt_hash")
        or project_meta.get("first_prompt_hash"),
        "transcript_hash": current_session.get("transcript_hash")
        or project_meta.get("transcript_hash"),
        "redaction_applied": bool(current_session.get("redaction_applied", False)),
        "finalize_attempts": max(
            int(project_meta.get("finalize_attempts", 0)),
            int(current_session.get("finalize_attempts", 0)),
        )
        + 1,
        "last_error": message,
        "final_commit": None,
    }
    update_project_status(
        project_dir,
        "failed",
        session_id=session_id,
        tool=tool,
        metadata=failure_fields,
    )

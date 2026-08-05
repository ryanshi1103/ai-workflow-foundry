"""Validation and context resolution for session finalization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...policy.runtime import read_json


@dataclass(frozen=True)
class FinalizationContext:
    """Validated inputs required by the finalization pipeline."""

    project_dir: Path
    session_id: str
    session_dir: Path
    project_meta: dict
    session_meta: dict | None
    tool: str


def initial_result(session_id: str | None) -> dict:
    """Return the stable public result shape for a finalization attempt."""
    return {
        "success": False,
        "status": "unknown",
        "commit": None,
        "session_id": session_id,
        "error": None,
    }


def validate_project_path(project_dir: Path, result: dict) -> Path | None:
    """Resolve and validate a project path, updating ``result`` on failure."""
    resolved = Path(project_dir).resolve()
    if not resolved.exists():
        result["error"] = f"Project directory does not exist: {resolved}"
        return None
    return resolved


def resolve_context(
    project_dir: Path,
    session_id: str | None,
    default_tool: str,
    result: dict,
) -> FinalizationContext | None:
    """Resolve metadata and session paths or return a terminal result."""
    meta = read_json(project_dir / ".ai-session" / "project.json")
    if not meta:
        result["error"] = "No project.json found"
        return None

    resolved_session_id = session_id or meta.get("session_id", "")
    if meta.get("status") in ("completed", "interrupted"):
        private_final = (
            read_json(
                project_dir
                / ".ai-session"
                / "private"
                / resolved_session_id
                / "finalization.json"
            )
            or {}
        )
        result.update(
            success=True,
            status=meta["status"],
            commit=private_final.get("final_commit"),
            message="Session already finalized",
        )
        return None

    if not resolved_session_id:
        result["error"] = "No session_id found"
        return None

    session_dir = (
        project_dir / ".ai-session" / "sessions" / resolved_session_id
    )
    session_meta = (
        read_json(session_dir / "meta.json") if session_dir.exists() else None
    )
    return FinalizationContext(
        project_dir=project_dir,
        session_id=resolved_session_id,
        session_dir=session_dir,
        project_meta=meta,
        session_meta=session_meta,
        tool=meta.get("tool", default_tool),
    )

"""Recovery — scan for interrupted sessions and recover them."""

import os
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

from .utils import (
    PROJECTS_ROOT, read_json, atomic_write_json, timestamp_iso,
    file_lock, ensure_dir, STATE_DIR,
)
from .finalize import finalize_session


def scan_interrupted_projects() -> list[dict]:
    """Scan ~/Projects for projects with running/interrupted status."""
    interrupted = []

    if not PROJECTS_ROOT.exists():
        return interrupted

    for entry in PROJECTS_ROOT.iterdir():
        if not entry.is_dir():
            continue

        project_file = entry / ".ai-session" / "project.json"
        if not project_file.exists():
            continue

        meta = read_json(project_file)
        if not meta:
            continue

        status = meta.get("status", "")
        if status not in ("running", "finalizing", "interrupted"):
            continue

        # Check if it's really stale
        session_id = meta.get("session_id", "")
        if _is_session_stale(entry, session_id):
            interrupted.append({
                "path": str(entry),
                "session_id": session_id,
                "tool": meta.get("tool", "unknown"),
                "status": status,
                "start_time": meta.get("start_time", ""),
                "model": meta.get("model", ""),
            })

    return interrupted


def _is_session_stale(project_dir: Path, session_id: str) -> bool:
    """Check if a session is genuinely stale (not still running in another terminal).

    Uses heartbeat file and process checking.
    """
    if not session_id:
        return True

    session_dir = project_dir / ".ai-session" / "sessions" / session_id
    if not session_dir.exists():
        return True

    # Check heartbeat
    heartbeat_path = session_dir / "heartbeat"
    if heartbeat_path.exists():
        try:
            heartbeat_text = heartbeat_path.read_text(encoding='utf-8').strip()
            # Parse ISO timestamp
            hb_time = datetime.fromisoformat(heartbeat_text)
            # If heartbeat is recent (within 5 minutes), session may still be alive
            age = datetime.now(timezone.utc) - hb_time.replace(tzinfo=timezone.utc)
            if age < timedelta(minutes=5):
                return False  # Too recent, might still be running
        except (ValueError, OSError):
            pass

    # Check if the transcript source is still being written to
    meta = read_json(project_dir / ".ai-session" / "project.json")
    if meta:
        transcript_source = meta.get("transcript_source", "")
        if transcript_source:
            tp = Path(transcript_source)
            if tp.exists():
                mtime = datetime.fromtimestamp(tp.stat().st_mtime, tz=timezone.utc)
                age = datetime.now(timezone.utc) - mtime
                if age < timedelta(minutes=5):
                    return False  # Transcript recently modified

    # Check for running CLI processes that might own this session
    # (Simple check — look for processes with the session_id in their env or args)
    try:
        import subprocess
        result = subprocess.run(
            ["pgrep", "-f", f"claude|codex"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return False  # Claude/Codex processes are running
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return True  # No evidence of a live session


def recover_interrupted(project_dir: Path, session_id: str) -> dict:
    """Recover an interrupted session — finalize with what we have."""
    project_dir = Path(project_dir)

    lock_file = project_dir / ".ai-session" / "recover.lock"
    try:
        with file_lock(lock_file, timeout=30.0):
            meta = read_json(project_dir / ".ai-session" / "project.json")
            if not meta:
                return {"success": False, "error": "No project.json found"}

            # Mark as interrupted (atomic update)
            from .project import update_project_status
            update_project_status(project_dir, "interrupted",
                                 session_id=session_id,
                                 tool=meta.get("tool", "claude"))
            meta = read_json(project_dir / ".ai-session" / "project.json") or meta
            if meta:
                meta["last_error"] = meta.get("last_error", "") + "; recovered after interruption"
                atomic_write_json(project_dir / ".ai-session" / "project.json", meta)

            # Run finalize (it's idempotent)
            result = finalize_session(
                project_dir=project_dir,
                session_id=session_id,
                tool=meta.get("tool", "claude"),
                use_ai=False,
            )

            # Update index
            _update_index_status(session_id, "interrupted")

            return result

    except TimeoutError:
        return {"success": False, "error": "Could not acquire lock for recovery"}


def _update_index_status(session_id: str, status: str) -> None:
    """Update project status in the global index."""
    index_path = STATE_DIR / "project-index.json"
    index = read_json(index_path)
    if index and "projects" in index and session_id in index["projects"]:
        index["projects"][session_id]["status"] = status
        index["projects"][session_id]["last_updated"] = timestamp_iso()
        atomic_write_json(index_path, index)


def recover_all() -> list[dict]:
    """Scan and recover all interrupted projects."""
    results = []
    interrupted = scan_interrupted_projects()
    for proj in interrupted:
        result = recover_interrupted(Path(proj["path"]), proj["session_id"])
        results.append({
            "path": proj["path"],
            "session_id": proj["session_id"],
            "result": result,
        })
    return results


def auto_recover_on_startup() -> None:
    """Automatically recover interrupted sessions at startup.
    Safe to call — won't recover sessions that are still running.
    """
    recover_all()

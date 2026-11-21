"""Orchestration for the session finalization pipeline."""

from __future__ import annotations

from pathlib import Path

from ...lifecycle.project import update_project_status
from ...policy.runtime import (
    compute_text_hash,
    file_lock,
    read_json,
    timestamp_iso,
)
from .hooks import record_final_commit, run_git_finalize_hook, write_staging_problems
from .output import (
    ensure_redacted_transcript,
    generate_conversation,
    merge_project_docs,
    parse_transcript,
    summarize_transcript,
    sync_transcript,
    update_readme,
    update_transcript_hash,
    write_session_docs,
)
from .recovery import record_finalization_failure
from .validation import initial_result, resolve_context, validate_project_path


def finalize_session(
    project_dir: Path,
    session_id: str | None = None,
    tool: str = "claude",
    use_ai: bool = False,
) -> dict:
    """Finalize one session using deterministic, idempotent stages.

    ``use_ai`` remains part of the public API for compatibility. The current
    pipeline deliberately uses deterministic summarization.
    """
    del use_ai
    result = initial_result(session_id)
    resolved_project = validate_project_path(project_dir, result)
    if resolved_project is None:
        return result

    lock_file = resolved_project / ".ai-session" / "finalize.lock"
    try:
        with file_lock(lock_file, timeout=30.0):
            return _run_pipeline(
                resolved_project,
                session_id,
                tool,
                result,
            )
    except TimeoutError:
        result["error"] = (
            "Could not acquire finalize lock (another finalize in progress?)"
        )
        return result


def _run_pipeline(
    project_dir: Path,
    session_id: str | None,
    tool: str,
    result: dict,
) -> dict:
    context = resolve_context(project_dir, session_id, tool, result)
    if context is None:
        return result

    meta = context.project_meta
    session_meta = context.session_meta
    try:
        sync_transcript(project_dir, context.session_dir, session_meta)
        update_transcript_hash(context.session_dir, session_meta)
        session_meta = read_json(context.session_dir / "meta.json") or {}

        events = parse_transcript(context.session_dir, context.tool)
        ensure_redacted_transcript(project_dir, context.session_dir)
        generate_conversation(
            project_dir,
            context.session_dir,
            events,
            context.tool,
        )
        summary = summarize_transcript(events, context.tool)
        final_status = "completed"

        write_session_docs(
            project_dir,
            context.session_id,
            context.tool,
            summary,
            final_status,
        )
        merge_project_docs(
            project_dir,
            context.session_id,
            summary,
            final_status,
        )
        update_readme(project_dir, summary.goal, final_status, context.tool)

        transcript_hash = session_meta.get("transcript_hash")
        final_fields = {
            "end_time": timestamp_iso(),
            "summary_success": True,
            "summary_mode": "deterministic",
            "first_prompt_hash": compute_text_hash(summary.first_prompt),
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
            session_id=context.session_id,
            tool=context.tool,
            metadata=final_fields,
        ):
            raise RuntimeError("Could not synchronize final metadata")

        meta = read_json(project_dir / ".ai-session" / "project.json") or meta
        session_meta = (
            read_json(context.session_dir / "meta.json") or session_meta
        )
        hook_result = run_git_finalize_hook(
            project_dir,
            context.session_id,
            context.tool,
            meta,
            summary.goal,
            summary.accomplishments,
            summary.decisions,
            final_status,
            session_meta,
        )
        final_commit = hook_result.get("commit")
        if not hook_result.get("success"):
            write_staging_problems(
                project_dir,
                context.session_id,
                hook_result.get("stage_result", {}),
            )
            update_project_status(
                project_dir,
                "failed",
                session_id=context.session_id,
                tool=context.tool,
            )
            result.update(
                status="failed",
                error=hook_result.get("error", "safe staging failed"),
                stage_result=hook_result.get("stage_result"),
            )
            return result

        record_final_commit(
            project_dir,
            context.session_id,
            context.tool,
            final_commit,
        )
        result.update(success=True, status=final_status, commit=final_commit)
        return result
    except Exception as error:
        result.update(error=str(error), status="failed")
        record_finalization_failure(
            project_dir,
            context.session_dir,
            context.session_id,
            context.tool,
            meta,
            error,
        )
        return result

"""Hook event handling — CLI-agnostic hook processing.

Handles hook events from both Claude Code and Codex:
- Receives stdin JSON from the CLI
- Records events to the session
- Manages session binding (CLI session_id → project session)
"""

import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

from .utils import (
    ensure_dir, atomic_write_json, read_json, atomic_copy,
    compute_sha256, compute_text_hash, timestamp_iso,
    INTERNAL_ENV_VAR, generate_short_id,
)
from .redact import redact_jsonl

_HOOK_LOGGER=None
def _get_hook_logger():
 global _HOOK_LOGGER
 if _HOOK_LOGGER is not None:return _HOOK_LOGGER
 l=logging.getLogger("ai-project-manager.hooks");l.setLevel(logging.INFO);l.propagate=False
 if l.handlers:_HOOK_LOGGER=l;return l
 try:
  d=Path.home()/".local/state/ai-project-manager/logs";d.mkdir(parents=True,exist_ok=True);h=logging.FileHandler(d/"hook-events.log",encoding="utf-8");h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"));l.addHandler(h)
 except (OSError,PermissionError):l.addHandler(logging.NullHandler())
 _HOOK_LOGGER=l;return l


def handle_hook_event():
    """Main entry point for hook events from Claude Code or Codex.

    Reads stdin JSON, dispatches to the right handler.
    Called by hook_entry.py.
    """
    # ── Debug logging (does not pollute AI context) ──
    _hook_log = _get_hook_logger()
    try:_hook_log.info("Hook invoked: pid=%s cwd=%s",os.getpid(),os.getcwd())
    except (OSError,ValueError):pass
    
    # Anti-recursion guard
    if os.environ.get(INTERNAL_ENV_VAR) == '1':
        sys.exit(0)

    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)
        event = json.loads(raw_input)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    event_type = event.get("hook_event_name", event.get("event", ""))
    if not event_type:
        sys.exit(0)

    # Determine tool from event or environment
    tool = _detect_tool(event)
    cwd = event.get("cwd", os.getcwd())
    session_id = event.get("session_id", "")

    # Find project — try multiple strategies in order
    project_dir = _find_project_by_cwd(Path(cwd))
    if not project_dir:
        project_dir = _find_project_by_env()
    if not project_dir:
        project_dir = _find_project_by_state(session_id)
    if not project_dir:
        # Last resort: check common project indicators in cwd
        for indicator in ["AGENTS.md", "CLAUDE.md", ".ai-session"]:
            if (Path(cwd) / indicator).exists():
                project_dir = Path(cwd)
                break
    if not project_dir:
        _hook_log.warning(
            "Could not find project: cwd=%s session_id=%s project_env_set=%s",cwd,session_id,bool(os.environ.get('AI_PROJECT_MANAGER_PROJECT'))
        )
        sys.exit(0)

    # Dispatch to event handler
    if event_type == "SessionStart":
        _handle_session_start(event, project_dir, tool)
    elif event_type == "UserPromptSubmit":
        _handle_user_prompt_submit(event, project_dir)
    elif event_type in ("Stop", "SubagentStop"):
        _handle_stop(event, project_dir, tool)
    elif event_type == "SessionEnd":
        _handle_session_end(event, project_dir)
    else:
        # Unknown event — silently ignore
        pass

    sys.exit(0)


def _detect_tool(event: dict) -> str:
    """Detect which tool generated this hook event using multiple signals."""
    # 1. Check environment variable (most reliable)
    env_tool = os.environ.get("AI_PROJECT_MANAGER_TOOL", "")
    if env_tool in ("claude", "codex"):
        return env_tool

    # 2. Check transcript path
    transcript = event.get("transcript_path", "")
    if transcript and "codex" in transcript.lower():
        return "codex"

    # 3. Check for Codex-specific fields
    if "workspace" in event or "agent_session_id" in event:
        return "codex"

    # 4. Check for Claude-specific fields
    if "permission_mode" in event:
        return "claude"

    # 5. Default
    env_tool_fallback = os.environ.get("AI_PROJECT_MANAGER_TOOL", "claude")
    return env_tool_fallback


def _find_project_by_cwd(cwd: Path) -> Path | None:
    """Find the ai-project-manager project by walking up from cwd.

    **IMPORTANT**: CC_ACTIVE_PROJECT is the single source of truth.
    If set, we use it directly — no walking, no guessing.
    """
    # Priority 0: CC_ACTIVE_PROJECT is the authoritative project directory
    cc_active = os.environ.get("CC_ACTIVE_PROJECT", "")
    if cc_active:
        cc_path = Path(cc_active)
        if cc_path.exists():
            # If it has .ai-session, use it directly
            if (cc_path / ".ai-session" / "project.json").exists():
                return cc_path
            # Even without .ai-session, trust CC_ACTIVE_PROJECT
            # launch_here will initialize it
            return cc_path

    current = cwd.resolve()
    while current != current.parent:
        project_file = current / ".ai-session" / "project.json"
        if project_file.exists():
            return current
        current = current.parent
    return None


def _find_project_by_env() -> Path | None:
    """Find project from environment variable AI_PROJECT_MANAGER_PROJECT."""
    # CC_ACTIVE_PROJECT takes priority
    cc_active = os.environ.get("CC_ACTIVE_PROJECT", "")
    if cc_active:
        pp = Path(cc_active)
        if pp.exists():
            return pp

    env_proj = os.environ.get("AI_PROJECT_MANAGER_PROJECT", "")
    if env_proj:
        pp = Path(env_proj)
        if pp.exists() and (pp / ".ai-session" / "project.json").exists():
            return pp
    return None


def _find_project_by_state(session_id: str) -> Path | None:
    """Find project by looking up session_id in global state index."""
    if not session_id:
        return None
    try:
        state_dir = Path.home() / ".local" / "state" / "ai-project-manager"
        index_path = state_dir / "project-index.json"
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
            projects = index.get("projects", {})
            # Search by session_id
            for sid, info in projects.items():
                if sid == session_id:
                    pp = Path(info.get("path", ""))
                    if pp.exists():
                        return pp
            # Also search for project whose session_id matches
            for sid, info in projects.items():
                pp = Path(info.get("path", ""))
                proj_file = pp / ".ai-session" / "project.json"
                if proj_file.exists():
                    try:
                        with open(proj_file, 'r', encoding='utf-8') as f2:
                            meta = json.load(f2)
                        if meta.get("session_id") == session_id:
                            return pp
                    except (OSError,ValueError,json.JSONDecodeError):continue
    except (OSError,ValueError,json.JSONDecodeError):return None
    return None


def _find_session_dir(project_dir: Path) -> Path | None:
    """Find the current session directory within a project.

    Tries to match by project.json's session_id first, then falls back to
    most recent directory.
    """
    sessions_dir = project_dir / ".ai-session" / "sessions"
    if not sessions_dir.exists():
        return None

    # Read project meta to get the expected session_id
    meta = read_json(project_dir / ".ai-session" / "project.json")
    expected_sid = meta.get("session_id", "") if meta else ""

    # Collect session directories
    session_dirs = sorted(
        [d for d in sessions_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,
    )

    if not session_dirs:
        return None

    # Try exact match first
    if expected_sid:
        for d in session_dirs:
            if d.name == expected_sid:
                return d

    # Fall back to most recent
    return session_dirs[0]


def _handle_session_start(event: dict, project_dir: Path, tool: str) -> None:
    """Handle SessionStart hook event.

    **IMPORTANT**: This hook MUST NOT create new top-level projects.
    It only updates metadata in the existing project directory.
    Session metadata is written into the project's .ai-session/sessions/ directory.
    """
    cli_session_id = event.get("session_id", "")
    transcript_path = event.get("transcript_path", "")
    cwd = event.get("cwd", "")
    model = event.get("model", "")
    permission_mode = event.get("permission_mode", "")

    # Update project meta with CLI session ID
    meta = read_json(project_dir / ".ai-session" / "project.json")
    if meta:
        meta["cli_session_id"] = cli_session_id
        meta["transcript_source"] = transcript_path
        meta["model"] = model or meta.get("model", "")
        meta["permission_mode"] = permission_mode or meta.get("permission_mode", "")
        meta["status"] = "running"
        atomic_write_json(project_dir / ".ai-session" / "project.json", meta)

    # Update session meta
    session_dir = _find_session_dir(project_dir)
    if session_dir:
        session_meta = read_json(session_dir / "meta.json")
        if session_meta:
            session_meta["cli_session_id"] = cli_session_id
            session_meta["transcript_source"] = transcript_path
            session_meta["model"] = model or session_meta.get("model", "")
            session_meta["permission_mode"] = permission_mode or session_meta.get("permission_mode", "")
            session_meta["status"] = "running"
            session_meta["start_time"] = timestamp_iso()
            atomic_write_json(session_dir / "meta.json", session_meta)

    # Record event
    _record_event(session_dir, "SessionStart", event)

    # Update heartbeat
    _update_heartbeat(session_dir)


def _handle_user_prompt_submit(event: dict, project_dir: Path) -> None:
    """Handle UserPromptSubmit hook event."""
    prompt = event.get("prompt", "")
    session_dir = _find_session_dir(project_dir)

    if not session_dir:
        return

    # If this is the first real prompt, compute hash and store
    if prompt and prompt.strip():
        session_meta = read_json(session_dir / "meta.json")
        if session_meta and not session_meta.get("first_prompt_hash"):
            prompt_hash = compute_text_hash(prompt)
            session_meta["first_prompt_hash"] = prompt_hash
            atomic_write_json(session_dir / "meta.json", session_meta)

    # Record event
    _record_event(session_dir, "UserPromptSubmit", event)

    # Update heartbeat
    _update_heartbeat(session_dir)


def _handle_stop(event: dict, project_dir: Path, tool: str) -> None:
    """Handle Stop hook event — sync transcript, record last message."""
    session_dir = _find_session_dir(project_dir)
    if not session_dir:
        return

    # Record event
    _record_event(session_dir, "Stop", event)

    # Sync transcript
    _sync_transcript(project_dir, session_dir, tool)

    # Update heartbeat
    _update_heartbeat(session_dir)


def _handle_session_end(event: dict, project_dir: Path) -> None:
    """Handle SessionEnd hook event — final sync, mark end."""
    # Defer real finalize to the outer launcher
    # Just record the event and do a final transcript sync
    session_dir = _find_session_dir(project_dir)
    if not session_dir:
        return

    _record_event(session_dir, "SessionEnd", event)

    # Mark ending in meta
    session_meta = read_json(session_dir / "meta.json")
    if session_meta:
        session_meta["end_time"] = timestamp_iso()
        session_meta["status"] = "finalizing"
        atomic_write_json(session_dir / "meta.json", session_meta)

    # Sync transcript one more time
    _sync_transcript(project_dir, session_dir, "claude")


def _sync_transcript(project_dir: Path, session_dir: Path, tool: str) -> None:
    """Copy and redact the current transcript."""
    session_meta = read_json(session_dir / "meta.json")
    if not session_meta:
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

    # Compute SHA-256
    transcript_hash = compute_sha256(src_path)

    # Create redacted version
    redacted_dest = session_dir / "transcript.redacted.jsonl"
    line_count, had_sensitive = redact_jsonl(src_path, redacted_dest)

    # Update meta
    session_meta["transcript_hash"] = transcript_hash
    session_meta["redaction_applied"] = had_sensitive
    atomic_write_json(session_dir / "meta.json", session_meta)

    # Write hash file
    hash_file = session_dir / "transcript.sha256"
    hash_file.write_text(f"{transcript_hash}  transcript.redacted.jsonl\n", encoding='utf-8')


def _record_event(session_dir: Path, event_type: str, event_data: dict) -> None:
    """Append an event to the session's events.jsonl."""
    if not session_dir:
        return
    event_path = session_dir / "events.jsonl"
    ensure_dir(session_dir)

    record = {
        "timestamp": timestamp_iso(),
        "event": event_type,
        "data": {
            k: v for k, v in event_data.items()
            if k not in ("raw", "full_event")
        },
    }

    # Don't store full prompt content in events (sensitive)
    if event_type == "UserPromptSubmit" and "prompt" in record.get("data", {}):
        prompt = record["data"]["prompt"]
        record["data"]["prompt_length"] = len(prompt)
        record["data"].pop("prompt",None)

    try:
        with open(event_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            f.flush()
    except (PermissionError, OSError) as e:
        try:
            _hook_log = _get_hook_logger()
            _hook_log.error(f"Failed to write event: {e} path={event_path}")
        except (OSError,ValueError):
            _get_hook_logger().error("event-write-error path=%s",event_path)


def _update_heartbeat(session_dir: Path) -> None:
    """Update the heartbeat timestamp."""
    if not session_dir:
        return
    heartbeat_path = session_dir / "heartbeat"
    try:
        heartbeat_path.write_text(timestamp_iso(), encoding='utf-8')
    except (PermissionError, OSError):
        pass


# ─── Hook configuration generation ───────────────────────────────────────────

HOOK_ENTRY_SCRIPT = "/home/ryan/.local/libexec/ai-project-manager-hook"

CLAUDE_HOOKS = {
    "SessionStart": [
        {
            "matcher": "startup|resume",
            "hooks": [
                {
                    "type": "command",
                    "command": HOOK_ENTRY_SCRIPT,
                    "timeout": 120,
                }
            ],
        }
    ],
    "UserPromptSubmit": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": HOOK_ENTRY_SCRIPT,
                    "timeout": 60,
                }
            ],
        }
    ],
    "Stop": [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": HOOK_ENTRY_SCRIPT,
                    "timeout": 60,
                }
            ],
        }
    ],
    "SessionEnd": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": HOOK_ENTRY_SCRIPT,
                    "timeout": 60,
                }
            ],
        }
    ],
}

CODEX_HOOKS = {
    "SessionStart": [
        {
            "matcher": "startup|resume",
            "hooks": [
                {
                    "type": "command",
                    "command": HOOK_ENTRY_SCRIPT,
                    "statusMessage": "AI Project Manager: session start",
                }
            ],
        }
    ],
    "UserPromptSubmit": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": HOOK_ENTRY_SCRIPT,
                    "statusMessage": "AI Project Manager: recording prompt",
                }
            ],
        }
    ],
    "Stop": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": HOOK_ENTRY_SCRIPT,
                    "timeout": 30,
                    "statusMessage": "AI Project Manager: syncing",
                }
            ],
        }
    ],
}


def merge_claude_hooks(existing_settings: dict) -> dict:
    """Deep-merge our hooks into existing Claude settings, preserving all existing hooks."""
    import copy
    settings = copy.deepcopy(existing_settings)

    if "hooks" not in settings:
        settings["hooks"] = {}

    existing_hooks = settings["hooks"]

    for event, our_hook_list in CLAUDE_HOOKS.items():
        if event not in existing_hooks:
            existing_hooks[event] = []

        # Check if our hook is already installed (by command pattern)
        our_commands = set()
        for our_hook_group in our_hook_list:
            for h in our_hook_group.get("hooks", []):
                our_commands.add(h.get("command", ""))

        # Filter out any existing hooks that are ours (prevent duplication)
        filtered = []
        for existing_group in existing_hooks[event]:
            if isinstance(existing_group, dict):
                existing_commands = set()
                for h in existing_group.get("hooks", []):
                    existing_commands.add(h.get("command", ""))
                if not existing_commands.intersection(our_commands):
                    filtered.append(existing_group)
            else:
                filtered.append(existing_group)

        # Append our hooks
        filtered.extend(our_hook_list)
        existing_hooks[event] = filtered

    return settings


def generate_codex_hooks_json() -> dict:
    """Generate Codex hooks.json content."""
    return {"hooks": CODEX_HOOKS}

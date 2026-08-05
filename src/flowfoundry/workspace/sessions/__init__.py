"""Stable canonical API for session finalization, hooks, and recovery."""

from .finalize import finalize_session
from .hooks import generate_codex_hooks_json, handle_hook_event, merge_claude_hooks
from .recovery import (
    auto_recover_on_startup,
    recover_all,
    recover_interrupted,
    scan_interrupted_projects,
)

__all__ = [
    "auto_recover_on_startup",
    "finalize_session",
    "generate_codex_hooks_json",
    "handle_hook_event",
    "merge_claude_hooks",
    "recover_all",
    "recover_interrupted",
    "scan_interrupted_projects",
]

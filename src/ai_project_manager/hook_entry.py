#!/usr/bin/env python3
"""Entry point for Claude Code and Codex hooks.

This module is called by the CLI via the secure launcher script:
  ~/.local/libexec/ai-project-manager-hook

It reads the hook event JSON from stdin and processes it.
"""

import sys
import os
import logging

# Add the parent directory to path for direct script execution
_script_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_script_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from ai_project_manager.hooks import handle_hook_event

if __name__ == "__main__":
    try:
        handle_hook_event()
    except Exception as e:
        # Last-resort error logging — must NOT pollute AI context
        try:
            log_dir = os.path.expanduser("~/.local/state/ai-project-manager/logs")
            os.makedirs(log_dir, exist_ok=True)
            l=logging.getLogger("ai-project-manager.hook-crash");l.propagate=False
            if not l.handlers:l.addHandler(logging.FileHandler(os.path.join(log_dir,"hook-crash.log"),encoding="utf-8"))
            l.error("CRASH type=%s",type(e).__name__)
        except (OSError,PermissionError,ValueError):logging.getLogger("ai-project-manager.hook-crash").addHandler(logging.NullHandler())
        sys.exit(0)

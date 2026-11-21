#!/usr/bin/env python3
"""Entry point for Claude Code and Codex hooks.

This module is called by the CLI via the secure launcher script:
  ~/.local/libexec/ai-project-manager-hook

It reads the hook event JSON from stdin and processes it.
"""

import logging
import os

from .hooks import handle_hook_event


def main() -> int:
    """Process one hook event without leaking failures into model context."""
    try:
        handle_hook_event()
        return 0
    except Exception as e:
        # Last-resort error logging — must NOT pollute AI context
        try:
            log_dir = os.path.expanduser("~/.local/state/ai-project-manager/logs")
            os.makedirs(log_dir, exist_ok=True)
            logger = logging.getLogger("ai-project-manager.hook-crash")
            logger.propagate = False
            if not logger.handlers:
                logger.addHandler(
                    logging.FileHandler(
                        os.path.join(log_dir, "hook-crash.log"), encoding="utf-8"
                    )
                )
            logger.error("CRASH type=%s", type(e).__name__)
        except (OSError, PermissionError, ValueError):
            logging.getLogger("ai-project-manager.hook-crash").addHandler(
                logging.NullHandler()
            )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

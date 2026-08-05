"""Compatibility entry point for workspace session hooks."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.sessions.hook_entry")
sys.modules[__name__] = _implementation

if __name__ == "__main__":
    raise SystemExit(_implementation.main())

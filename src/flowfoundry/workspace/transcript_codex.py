"""Compatibility alias for Codex transcript processing."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.sessions.transcript_codex")
sys.modules[__name__] = _implementation

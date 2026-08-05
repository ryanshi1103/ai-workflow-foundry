"""Compatibility alias for :mod:`flowfoundry.workspace.sessions.finalize`."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.sessions.finalize")
sys.modules[__name__] = _implementation

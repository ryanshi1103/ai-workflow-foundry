"""Compatibility alias for :mod:`flowfoundry.workspace.sessions.hooks`."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.sessions.hooks")
sys.modules[__name__] = _implementation

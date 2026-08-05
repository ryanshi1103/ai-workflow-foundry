"""Compatibility alias for :mod:`flowfoundry.workspace.sessions.recovery`."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.sessions.recovery")
sys.modules[__name__] = _implementation

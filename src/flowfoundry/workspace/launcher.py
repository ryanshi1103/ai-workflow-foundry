"""Compatibility alias for :mod:`flowfoundry.workspace.lifecycle.launcher`."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.lifecycle.launcher")
sys.modules[__name__] = _implementation

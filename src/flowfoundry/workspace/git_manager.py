"""Compatibility alias for :mod:`flowfoundry.workspace.lifecycle.git_manager`."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.lifecycle.git_manager")
sys.modules[__name__] = _implementation

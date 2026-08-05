"""Compatibility alias for :mod:`flowfoundry.workspace.lifecycle.project`."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.lifecycle.project")
sys.modules[__name__] = _implementation

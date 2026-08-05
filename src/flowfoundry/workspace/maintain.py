"""Compatibility alias for :mod:`flowfoundry.workspace.maintenance.projects`."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.maintenance.projects")
sys.modules[__name__] = _implementation

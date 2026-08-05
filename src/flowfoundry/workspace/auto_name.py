"""Compatibility alias for :mod:`flowfoundry.workspace.lifecycle.auto_name`."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.lifecycle.auto_name")
sys.modules[__name__] = _implementation

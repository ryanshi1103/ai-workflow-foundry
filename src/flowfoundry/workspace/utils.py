"""Compatibility alias for :mod:`flowfoundry.workspace.policy.runtime`."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.policy.runtime")
sys.modules[__name__] = _implementation

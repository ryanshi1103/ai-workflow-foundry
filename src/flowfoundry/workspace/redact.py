"""Compatibility alias for :mod:`flowfoundry.workspace.policy.redact`."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.policy.redact")
sys.modules[__name__] = _implementation

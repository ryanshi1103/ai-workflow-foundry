"""Compatibility alias for :mod:`flowfoundry.workspace.cli.maintenance`."""

import sys
from importlib import import_module

_implementation = import_module("flowfoundry.workspace.cli.maintenance")
sys.modules[__name__] = _implementation

if __name__ == "__main__":
    raise SystemExit(_implementation.main())

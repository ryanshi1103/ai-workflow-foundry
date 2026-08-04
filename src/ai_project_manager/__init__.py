"""Backward-compatibility shim — re-exports flowfoundry.workspace as ai_project_manager.

After the workspace manager was merged into the flowfoundry package, this shim
keeps all existing imports working::

    import ai_project_manager
    from ai_project_manager import auto_name, maintain
    from ai_project_manager.cli import main
    python3 -m ai_project_manager.cli

It eagerly aliases every flowfoundry.workspace.* module into sys.modules so
that both package-relative and submodule imports resolve correctly.
"""

import importlib
import sys
from pathlib import Path

_workspace_pkg = importlib.import_module("flowfoundry.workspace")
sys.modules[__name__] = _workspace_pkg

_ws_dir = Path(_workspace_pkg.__file__).resolve().parent
for _py_file in sorted(_ws_dir.glob("*.py")):
    _stem = _py_file.stem
    if _stem == "__init__":
        continue
    try:
        _mod = importlib.import_module(f"flowfoundry.workspace.{_stem}")
        sys.modules[f"ai_project_manager.{_stem}"] = _mod
    except ImportError:
        pass

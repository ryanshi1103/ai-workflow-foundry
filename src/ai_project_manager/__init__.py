"""Backward-compatible aliases for the canonical FlowFoundry workspace modules.

After the workspace manager was merged into the flowfoundry package, this shim
keeps all existing imports working::

    import ai_project_manager
    from ai_project_manager import auto_name, maintain
    from ai_project_manager.cli import main
    python3 -m ai_project_manager.cli

The compatibility package maps historical names directly to canonical
subpackage implementations. It does not depend on the removed root-level
``flowfoundry.workspace`` shims.
"""

import importlib
import sys

_workspace_pkg = importlib.import_module("flowfoundry.workspace")
sys.modules[__name__] = _workspace_pkg

_CANONICAL_MODULES = {
    "auto_name": "flowfoundry.workspace.lifecycle.auto_name",
    "cc_launcher": "flowfoundry.workspace.cli.launcher",
    "cli": "flowfoundry.workspace.cli",
    "finalize": "flowfoundry.workspace.sessions.finalize",
    "git_manager": "flowfoundry.workspace.lifecycle.git_manager",
    "hook_entry": "flowfoundry.workspace.sessions.hook_entry",
    "hooks": "flowfoundry.workspace.sessions.hooks",
    "launcher": "flowfoundry.workspace.lifecycle.launcher",
    "maintain": "flowfoundry.workspace.maintenance.projects",
    "maintain_cli": "flowfoundry.workspace.cli.maintenance",
    "project": "flowfoundry.workspace.lifecycle.project",
    "recovery": "flowfoundry.workspace.sessions.recovery",
    "redact": "flowfoundry.workspace.policy.redact",
    "transcript_claude": "flowfoundry.workspace.sessions.transcript_claude",
    "transcript_codex": "flowfoundry.workspace.sessions.transcript_codex",
    "utils": "flowfoundry.workspace.policy.runtime",
}

for _legacy_name, _canonical_name in _CANONICAL_MODULES.items():
    _module = importlib.import_module(_canonical_name)
    sys.modules[f"ai_project_manager.{_legacy_name}"] = _module
    setattr(_workspace_pkg, _legacy_name, _module)

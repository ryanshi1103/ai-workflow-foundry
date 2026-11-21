"""Stable canonical API for project and launch lifecycle operations."""

from importlib import import_module

from .git_manager import ensure_git_identity, git_init, git_status
from .project import (
    choose_project,
    create_new_project,
    create_project_meta,
    create_project_structure,
    create_session_meta,
    discover_project_directories,
    discover_projects,
    discover_selectable_projects,
    read_project_meta,
    rename_project,
    update_project_status,
    validate_status_transition,
)

__all__ = [
    "choose_project",
    "create_new_project",
    "create_project_meta",
    "create_project_structure",
    "create_session_meta",
    "discover_project_directories",
    "discover_projects",
    "discover_selectable_projects",
    "ensure_git_identity",
    "git_init",
    "git_status",
    "is_non_interactive_args",
    "launch_here",
    "launch_new",
    "read_project_meta",
    "rename_project",
    "update_project_status",
    "validate_status_transition",
]

_LAUNCH_EXPORTS = {"is_non_interactive_args", "launch_here", "launch_new"}


def __getattr__(name: str):
    """Load launcher exports lazily to keep session imports cycle-free."""
    if name not in _LAUNCH_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(".launcher", __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | _LAUNCH_EXPORTS)

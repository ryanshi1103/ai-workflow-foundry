"""Sanitized MediaFlow application boundary.

The private product owns media processing, databases, provider configuration,
and release packaging.  This module intentionally describes only the portable
workflow and validates paths that cross the public adapter boundary.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any


class MediaFlowContractError(ValueError):
    """Raised when public MediaFlow adapter input violates the safety contract."""


_CONTRACT: dict[str, Any] = {
    "schema_version": 1,
    "id": "mediaflow",
    "display_name": "Huiying / MediaFlow",
    "source_boundary": "private-product",
    "platforms": ["linux_web", "windows_desktop", "android_companion"],
    "workflow": [
        "discover_controlled_inputs",
        "inspect_media",
        "propose_timeline",
        "human_review",
        "approve_export",
        "finalize_output",
    ],
    "shared_core": [
        "file_discovery",
        "media_pipeline",
        "task_state",
        "naming_and_output_rules",
        "safe_paths",
        "configuration",
        "error_model",
    ],
    "policy": {
        "local_first": True,
        "inputs_immutable": True,
        "outputs_no_overwrite": True,
        "synthetic_public_fixtures_only": True,
        "human_review_required": True,
        "export_approval_separate": True,
        "provider_access_explicit": True,
    },
}


def mediaflow_contract() -> dict[str, Any]:
    """Return a detached copy of the public application contract."""

    return deepcopy(_CONTRACT)


def validate_controlled_relative_path(value: str) -> PurePosixPath:
    """Validate a portable path without touching the filesystem.

    Public workflows exchange paths relative to an explicitly controlled root.
    Absolute POSIX/Windows paths, parent traversal, empty segments, and backslash
    aliases are rejected before the private application resolves a real path.
    """

    if not isinstance(value, str) or not value.strip():
        raise MediaFlowContractError("path must be a non-empty string")
    if "\\" in value:
        raise MediaFlowContractError("path must use portable forward slashes")

    path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise MediaFlowContractError("absolute paths are not allowed")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise MediaFlowContractError("path traversal is not allowed")
    return path


__all__ = [
    "MediaFlowContractError",
    "mediaflow_contract",
    "validate_controlled_relative_path",
]

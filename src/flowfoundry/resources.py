"""Locate repository resources in a source checkout or an installed distribution."""

from __future__ import annotations

import sys
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2]
INSTALLED_ROOT = Path(sys.prefix).resolve() / "share" / "flowfoundry"


def resource_root() -> tuple[Path, bool]:
    """Return `(root, is_source_checkout)` for packaged catalog resources."""

    if (SOURCE_ROOT / "catalog").is_dir():
        return SOURCE_ROOT, True
    if (INSTALLED_ROOT / "catalog").is_dir():
        return INSTALLED_ROOT, False
    return SOURCE_ROOT, False


def resource_path(*parts: str) -> Path:
    root, _ = resource_root()
    return root.joinpath(*parts)

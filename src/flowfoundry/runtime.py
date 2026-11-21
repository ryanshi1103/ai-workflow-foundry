"""Small project execution-environment resolver.

The core remains language-neutral: the first implementation only prepends an
existing project-local ``.venv/bin`` to PATH and selects its Python launcher
when present. No environment is created or mutated globally.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def resolve_project_execution_environment(root: Path) -> dict[str, Any]:
    root = root.resolve()
    inherited = os.environ.copy()
    bin_dir = root / ".venv" / "bin"
    valid = (bin_dir / "python").is_file() and os.access(bin_dir / "python", os.X_OK)
    if valid:
        inherited["PATH"] = str(bin_dir) + os.pathsep + inherited.get("PATH", "")
    return {
        "env": inherited,
        "path_prefix": str(bin_dir) if valid else "",
        "python": str(bin_dir / "python") if valid else None,
        "source": ".venv/bin" if valid else "inherited environment",
        "cwd": str(root),
    }

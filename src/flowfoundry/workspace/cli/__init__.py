"""Workspace command entry points.

The package exports the legacy ``flowfoundry.workspace.cli`` callable surface
so installed ``aiproj`` entry points continue to work during the migration.
"""

from .project import main, run

__all__ = ["main", "run"]

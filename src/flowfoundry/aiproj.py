"""Entry point for the ``aiproj`` console script — delegates to workspace CLI."""

from flowfoundry.workspace.cli import run


def main(argv=None):
    return run(argv)

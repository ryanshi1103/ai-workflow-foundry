"""Command-line interface for the FlowFoundry catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .catalog import CatalogError, get_component, load_catalog, validate_catalog


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flowfoundry",
        description="Inspect and validate FlowFoundry workflow components.",
    )
    parser.add_argument("--catalog", type=Path, help="use an alternate catalog directory")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="list registered components")
    show_parser = subparsers.add_parser("show", help="show one component manifest")
    show_parser.add_argument("component_id")
    subparsers.add_parser("validate", help="validate manifests and bundled paths")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "list":
            for component in load_catalog(args.catalog):
                print(
                    f"{component['id']:<34} "
                    f"{component['kind']:<22} "
                    f"{component['maturity']:<12} "
                    f"{component['integration']['mode']}"
                )
            return 0
        if args.command == "show":
            print(json.dumps(get_component(args.component_id, args.catalog), indent=2, ensure_ascii=False))
            return 0

        components = validate_catalog(args.catalog)
        print(f"validated {len(components)} FlowFoundry components")
        return 0
    except CatalogError as exc:
        print(f"flowfoundry: {exc}", file=sys.stderr)
        return 2

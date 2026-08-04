"""Command-line interface for the FlowFoundry catalog and workflow contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .catalog import CatalogError, get_component, load_catalog, validate_catalog
from .capability_registry import (
    check_workflow_capabilities,
    cross_reference_catalog,
    load_capability_registry,
)
from .workflow_contract import (
    cross_reference_stages,
    load_workflow_contracts,
    validate_workflow_contract,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flowfoundry",
        description="Inspect and validate FlowFoundry workflow components and contracts.",
    )
    parser.add_argument("--catalog", type=Path, help="use an alternate catalog directory")
    parser.add_argument(
        "--contracts", type=Path, help="use an alternate workflow contracts directory"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="list registered components")
    show_parser = subparsers.add_parser("show", help="show one component manifest")
    show_parser.add_argument("component_id")
    subparsers.add_parser("validate", help="validate manifests, bundled paths, and workflow contracts")

    # Workflow contract subcommands
    wf_list = subparsers.add_parser("workflows", help="list registered workflow contracts")
    wf_show = subparsers.add_parser("workflow-show", help="show one workflow contract")
    wf_show.add_argument("contract_id")
    wf_validate = subparsers.add_parser(
        "workflow-validate", help="validate workflow contracts and cross-reference stages"
    )

    # Capability registry subcommands
    cap_list = subparsers.add_parser("capabilities", help="list registered capabilities")
    cap_check = subparsers.add_parser(
        "capability-check", help="check workflow contract capabilities against the registry"
    )
    cap_check.add_argument("contract_id", nargs="?", help="workflow contract id (omit to check all)")
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

        if args.command == "validate":
            components = validate_catalog(args.catalog)
            print(f"validated {len(components)} FlowFoundry components")

            # Also validate workflow contracts if the directory exists
            from .workflow_contract import CONTRACTS_DIR as default_contracts

            contracts_dir = args.contracts or default_contracts
            if contracts_dir.is_dir() and list(contracts_dir.glob("*.contract.json")):
                contracts = load_workflow_contracts(contracts_dir)
                for wf in contracts:
                    issues = cross_reference_stages(wf)
                    if issues:
                        for issue in issues:
                            print(f"  {wf['id']}: {issue}", file=sys.stderr)
                        return 2
                print(f"validated {len(contracts)} workflow contracts")

            # Cross-reference capability registry with catalog
            from .capability_registry import CAPABILITY_REGISTRY_PATH

            if CAPABILITY_REGISTRY_PATH.is_file():
                issues = cross_reference_catalog()
                if issues:
                    for issue in issues:
                        print(f"  capability registry: {issue}", file=sys.stderr)
                    return 2
                registry = load_capability_registry()
                print(f"validated {len(registry['capabilities'])} registered capabilities")
            return 0

        # Workflow contract commands
        if args.command == "workflows":
            contracts = load_workflow_contracts(args.contracts)
            for wf in contracts:
                stage_count = len(wf["stages"])
                gate_count = len(wf["approval_gates"])
                print(
                    f"{wf['id']:<34} "
                    f"v{wf['version']:<12} "
                    f"{stage_count} stage{'s' if stage_count != 1 else ''}, "
                    f"{gate_count} approval gate{'s' if gate_count != 1 else ''}"
                )
            return 0

        if args.command == "workflow-show":
            contracts = load_workflow_contracts(args.contracts)
            for wf in contracts:
                if wf["id"] == args.contract_id:
                    print(json.dumps(wf, indent=2, ensure_ascii=False))
                    return 0
            raise CatalogError(f"unknown workflow contract: {args.contract_id}")

        if args.command == "workflow-validate":
            contracts = load_workflow_contracts(args.contracts)
            issues_found = 0
            for wf in contracts:
                issues = cross_reference_stages(wf)
                if issues:
                    for issue in issues:
                        print(f"  {wf['id']}: {issue}", file=sys.stderr)
                    issues_found += len(issues)
            if issues_found:
                print(
                    f"{issues_found} cross-reference issue{'s' if issues_found != 1 else ''} found",
                    file=sys.stderr,
                )
                return 2
            print(f"validated {len(contracts)} workflow contracts (no cross-reference issues)")
            return 0

        # Capability registry commands
        if args.command == "capabilities":
            registry = load_capability_registry()
            for cap in registry["capabilities"]:
                print(
                    f"{cap['id']:<40} "
                    f"{cap['maturity']:<12} "
                    f"provided by {cap['provided_by']:<30} "
                    f"[{cap['adapter']['type']}]"
                )
            return 0

        if args.command == "capability-check":
            contracts = load_workflow_contracts(args.contracts)
            registry = load_capability_registry()
            exit_code = 0
            targets = (
                [c for c in contracts if c["id"] == args.contract_id]
                if args.contract_id
                else contracts
            )
            if args.contract_id and not targets:
                raise CatalogError(f"unknown workflow contract: {args.contract_id}")
            for wf in targets:
                missing = check_workflow_capabilities(wf, registry)
                if missing:
                    print(
                        f"{wf['id']}: missing capabilities: {', '.join(missing)}",
                        file=sys.stderr,
                    )
                    exit_code = 2
                else:
                    required = wf.get("capabilities_required", [])
                    if required:
                        print(f"{wf['id']}: all {len(required)} capabilities satisfied")
                    else:
                        print(f"{wf['id']}: no capabilities required")
            return exit_code

        return 0
    except CatalogError as exc:
        print(f"flowfoundry: {exc}", file=sys.stderr)
        return 2

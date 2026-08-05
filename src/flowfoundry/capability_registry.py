"""Load and validate FlowFoundry capability registries.

A capability registry maps reviewed intent (capability IDs declared in component
manifests) to trusted implementations (concrete adapters with entry points).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import CatalogError, _require_text, load_catalog
from .resources import resource_path

CAPABILITY_REGISTRY_PATH = resource_path("catalog", "capability-registry.json")

ADAPTER_TYPES = {
    "claude-skill",
    "codex-skill",
    "deterministic-command",
    "python-module",
    "manual",
}
MATURITY_LEVELS = {"experimental", "alpha", "beta", "stable"}


def validate_capability_entry(entry: Any, index: int = 0) -> dict[str, Any]:
    """Validate a single capability registry entry."""
    if not isinstance(entry, dict):
        raise CatalogError(f"capabilities[{index}] must be an object")

    cap_id = _require_text(entry.get("id"), f"capabilities[{index}].id")
    if not cap_id or " " in cap_id:
        raise CatalogError(f"capabilities[{index}].id must be non-empty kebab-case")

    _require_text(entry.get("display_name"), f"capabilities[{index}].display_name")
    _require_text(entry.get("description"), f"capabilities[{index}].description")
    _require_text(entry.get("provided_by"), f"capabilities[{index}].provided_by")

    adapter = entry.get("adapter")
    if not isinstance(adapter, dict):
        raise CatalogError(f"capabilities[{index}].adapter must be an object")
    if adapter.get("type") not in ADAPTER_TYPES:
        raise CatalogError(
            f"capabilities[{index}].adapter.type must be one of {sorted(ADAPTER_TYPES)}"
        )
    _require_text(adapter.get("entry_point"), f"capabilities[{index}].adapter.entry_point")

    if entry.get("maturity") not in MATURITY_LEVELS:
        raise CatalogError(
            f"capabilities[{index}].maturity must be one of {sorted(MATURITY_LEVELS)}"
        )

    return entry


def load_capability_registry(
    path: Path | str | None = None,
) -> dict[str, Any]:
    """Load and validate the full capability registry."""
    registry_path = Path(path) if path is not None else CAPABILITY_REGISTRY_PATH
    if not registry_path.is_file():
        raise CatalogError(f"capability registry does not exist: {registry_path}")

    try:
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot read {registry_path.name}: {exc}") from exc

    if not isinstance(raw, dict):
        raise CatalogError("capability registry must be a JSON object")
    if raw.get("schema_version") != 1:
        raise CatalogError("capability registry schema_version must be 1")

    capabilities = raw.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise CatalogError("registry must contain a non-empty capabilities list")

    seen: set[str] = set()
    for i, entry in enumerate(capabilities):
        validate_capability_entry(entry, i)
        cap_id = entry["id"]
        if cap_id in seen:
            raise CatalogError(f"duplicate capability id: {cap_id}")
        seen.add(cap_id)

    return raw


def get_capability_ids(registry: dict[str, Any] | None = None) -> set[str]:
    """Return the set of all capability IDs in the registry."""
    if registry is None:
        registry = load_capability_registry()
    return {cap["id"] for cap in registry.get("capabilities", [])}


def check_workflow_capabilities(
    workflow_contract: dict[str, Any],
    registry: dict[str, Any] | None = None,
) -> list[str]:
    """Check that all capabilities required by a workflow contract exist in the registry.

    Returns a list of missing capability IDs (empty means all satisfied).
    """
    required = set(workflow_contract.get("capabilities_required", []))
    if not required:
        return []

    available = get_capability_ids(registry)
    missing = required - available
    return sorted(missing)


def cross_reference_catalog(
    registry: dict[str, Any] | None = None,
) -> list[str]:
    """Verify that every capability's provided_by field references an actual component in the catalog.

    Returns a list of issues (empty means valid).
    """
    if registry is None:
        registry = load_capability_registry()

    try:
        catalog = load_catalog()
    except CatalogError:
        return ["cannot load component catalog for cross-reference"]

    component_ids = {c["id"] for c in catalog}
    issues: list[str] = []

    for cap in registry.get("capabilities", []):
        provider = cap["provided_by"]
        if provider not in component_ids:
            issues.append(
                f"capability '{cap['id']}' references unknown component '{provider}'"
            )

    # Also check: does every component have at least one capability?
    providers_in_registry = {c["provided_by"] for c in registry.get("capabilities", [])}
    for cid in sorted(component_ids - providers_in_registry):
        issues.append(f"component '{cid}' has no registered capabilities")

    return issues

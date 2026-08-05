"""Load and validate FlowFoundry component declarations."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .resources import resource_path, resource_root

CATALOG_DIR = resource_path("catalog")
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KINDS = {"core-runtime", "workflow-pack", "reference-application", "reference-workflow"}
MATURITY = {"experimental", "alpha", "beta", "stable"}
INTEGRATION_MODES = {"bundled", "compatible-extension", "reference-application", "reference-workflow"}
SECRET_POLICIES = {"none", "environment", "local-user-config"}


class CatalogError(ValueError):
    """Raised when a component declaration violates the catalog contract."""


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{field} must be a non-empty string")
    return value


def _require_unique_text_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise CatalogError(f"{field} must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise CatalogError(f"{field} entries must be non-empty strings")
    if len(value) != len(set(value)):
        raise CatalogError(f"{field} entries must be unique")
    return value


def validate_component(component: Any) -> dict[str, Any]:
    if not isinstance(component, dict):
        raise CatalogError("component must be an object")
    if component.get("schema_version") != 1:
        raise CatalogError("schema_version must be 1")

    component_id = _require_text(component.get("id"), "id")
    if not ID_PATTERN.fullmatch(component_id):
        raise CatalogError("id must use lowercase kebab-case")
    aliases = component.get("aliases", [])
    if not isinstance(aliases, list):
        raise CatalogError("aliases must be a list")
    if len(aliases) != len(set(aliases)):
        raise CatalogError("aliases entries must be unique")
    for alias in aliases:
        if not isinstance(alias, str) or not ID_PATTERN.fullmatch(alias):
            raise CatalogError("aliases entries must use lowercase kebab-case")
        if alias == component_id:
            raise CatalogError("aliases must not repeat the canonical id")
    _require_text(component.get("display_name"), "display_name")
    _require_text(component.get("summary"), "summary")

    if component.get("kind") not in KINDS:
        raise CatalogError(f"kind must be one of {sorted(KINDS)}")
    if component.get("maturity") not in MATURITY:
        raise CatalogError(f"maturity must be one of {sorted(MATURITY)}")

    source = component.get("source")
    if not isinstance(source, dict):
        raise CatalogError("source must be an object")
    source_url = _require_text(source.get("url"), "source.url")
    if not source_url.startswith("https://github.com/"):
        raise CatalogError("source.url must be an HTTPS GitHub repository URL")
    _require_text(source.get("license"), "source.license")

    integration = component.get("integration")
    if not isinstance(integration, dict):
        raise CatalogError("integration must be an object")
    mode = integration.get("mode")
    if mode not in INTEGRATION_MODES:
        raise CatalogError(f"integration.mode must be one of {sorted(INTEGRATION_MODES)}")
    bundled_path = integration.get("bundled_path")
    if mode == "bundled":
        bundled_path = _require_text(bundled_path, "integration.bundled_path")
        candidate = Path(bundled_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise CatalogError("integration.bundled_path must stay inside the repository")
    elif bundled_path is not None:
        raise CatalogError("only bundled components may declare bundled_path")

    _require_unique_text_list(component.get("capabilities"), "capabilities")
    _require_unique_text_list(component.get("design_patterns"), "design_patterns")

    lifecycle = component.get("lifecycle")
    if not isinstance(lifecycle, dict):
        raise CatalogError("lifecycle must be an object")
    _require_unique_text_list(lifecycle.get("stages"), "lifecycle.stages")
    approvals = lifecycle.get("approvals")
    if not isinstance(approvals, list) or any(not isinstance(item, str) for item in approvals):
        raise CatalogError("lifecycle.approvals must be a list of strings")

    safety = component.get("safety")
    if not isinstance(safety, dict):
        raise CatalogError("safety must be an object")
    for field in ("local_first", "preserves_originals", "review_before_side_effects"):
        if not isinstance(safety.get(field), bool):
            raise CatalogError(f"safety.{field} must be a boolean")
    if safety.get("secrets") not in SECRET_POLICIES:
        raise CatalogError(f"safety.secrets must be one of {sorted(SECRET_POLICIES)}")
    _require_text(safety.get("network"), "safety.network")

    return component


def load_catalog(directory: Path | str | None = None) -> list[dict[str, Any]]:
    catalog_dir = Path(directory) if directory is not None else CATALOG_DIR
    if not catalog_dir.is_dir():
        raise CatalogError(f"catalog directory does not exist: {catalog_dir}")

    components: list[dict[str, Any]] = []
    seen: set[str] = set()
    for manifest_path in sorted(catalog_dir.glob("*.json")):
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CatalogError(f"cannot read {manifest_path.name}: {exc}") from exc
        # Skip non-component JSON files (e.g., capability-registry.json)
        if not isinstance(raw, dict) or "kind" not in raw:
            continue
        component = validate_component(raw)
        component_id = component["id"]
        identities = [component_id, *component.get("aliases", [])]
        collision = next((identity for identity in identities if identity in seen), None)
        if collision is not None:
            raise CatalogError(f"duplicate component id or alias: {collision}")
        seen.update(identities)
        components.append(component)

    if not components:
        raise CatalogError("catalog contains no component manifests")
    return components


def validate_catalog(directory: Path | str | None = None, repository_root: Path | None = None) -> list[dict[str, Any]]:
    components = load_catalog(directory)
    default_root, is_source_checkout = resource_root()
    root = repository_root or default_root
    verify_bundled_paths = repository_root is not None or is_source_checkout
    for component in components:
        bundled_path = component["integration"].get("bundled_path")
        if bundled_path and verify_bundled_paths and not (root / bundled_path).is_dir():
            raise CatalogError(
                f"bundled path for {component['id']} does not exist: {bundled_path}"
            )
    return components


def get_component(component_id: str, directory: Path | str | None = None) -> dict[str, Any]:
    for component in load_catalog(directory):
        if component["id"] == component_id or component_id in component.get("aliases", []):
            return component
    raise CatalogError(f"unknown component: {component_id}")

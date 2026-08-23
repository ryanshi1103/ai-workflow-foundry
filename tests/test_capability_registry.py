"""Tests for the capability registry validation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from flowfoundry.capability_registry import (
    check_workflow_capabilities,
    cross_reference_catalog,
    get_capability_ids,
    load_capability_registry,
    validate_capability_entry,
)
from flowfoundry.catalog import CatalogError

ROOT = Path(__file__).resolve().parents[1]


class CapabilityRegistryTests(unittest.TestCase):
    """Tests for the capability registry."""

    def test_registry_loads(self) -> None:
        registry = load_capability_registry()
        self.assertIn("capabilities", registry)
        self.assertEqual(len(registry["capabilities"]), 13)

    def test_all_capability_ids_are_unique(self) -> None:
        registry = load_capability_registry()
        ids = [c["id"] for c in registry["capabilities"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_get_capability_ids(self) -> None:
        ids = get_capability_ids()
        self.assertIn("validated-tabular-input", ids)
        self.assertIn("project-lifecycle", ids)

    def test_cross_reference_catalog_is_clean(self) -> None:
        issues = cross_reference_catalog()
        self.assertEqual(issues, [])

    def test_missing_provided_by_is_rejected(self) -> None:
        entry = {
            "id": "test-cap",
            "display_name": "Test",
            "description": "A test capability",
            "adapter": {"type": "python-module", "entry_point": "foo"},
            "maturity": "beta",
        }
        with self.assertRaisesRegex(CatalogError, "provided_by"):
            validate_capability_entry(entry, 0)

    def test_invalid_adapter_type_is_rejected(self) -> None:
        entry = {
            "id": "test-cap",
            "display_name": "Test",
            "description": "A test capability",
            "provided_by": "some-component",
            "adapter": {"type": "invalid", "entry_point": "foo"},
            "maturity": "beta",
        }
        with self.assertRaisesRegex(CatalogError, "adapter.type"):
            validate_capability_entry(entry, 0)

    def test_invalid_maturity_is_rejected(self) -> None:
        entry = {
            "id": "test-cap",
            "display_name": "Test",
            "description": "A test capability",
            "provided_by": "some-component",
            "adapter": {"type": "python-module", "entry_point": "foo"},
            "maturity": "production",
        }
        with self.assertRaisesRegex(CatalogError, "maturity"):
            validate_capability_entry(entry, 0)

    def test_duplicate_capability_id_is_rejected(self) -> None:
        registry = load_capability_registry()
        dup = dict(registry)
        dup["capabilities"] = registry["capabilities"] + [registry["capabilities"][0]]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "dup-registry.json"
            path.write_text(json.dumps(dup), encoding="utf-8")
            with self.assertRaisesRegex(CatalogError, "duplicate capability id"):
                load_capability_registry(path)


class CapabilityCheckTests(unittest.TestCase):
    """Tests for checking workflow capabilities against the registry."""

    def test_all_capabilities_satisfied(self) -> None:
        contract = {
            "capabilities_required": [
                "validated-tabular-input",
                "deterministic-document-geometry",
                "editable-vector-output",
                "safe-output-filename-generation",
            ]
        }
        missing = check_workflow_capabilities(contract)
        self.assertEqual(missing, [])

    def test_missing_capability_reported(self) -> None:
        contract = {"capabilities_required": ["nonexistent-capability"]}
        missing = check_workflow_capabilities(contract)
        self.assertIn("nonexistent-capability", missing)

    def test_no_requirements_is_ok(self) -> None:
        contract = {}
        missing = check_workflow_capabilities(contract)
        self.assertEqual(missing, [])

    def test_mixed_satisfied_and_missing(self) -> None:
        contract = {
            "capabilities_required": [
                "validated-tabular-input",
                "made-up-capability",
            ]
        }
        missing = check_workflow_capabilities(contract)
        self.assertEqual(missing, ["made-up-capability"])


if __name__ == "__main__":
    unittest.main()

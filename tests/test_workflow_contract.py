"""Tests for portable workflow contract validation."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from flowfoundry.catalog import CatalogError
from flowfoundry.workflow_contract import (
    cross_reference_stages,
    load_workflow_contracts,
    validate_workflow_contract,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_example_contract() -> dict:
    path = ROOT / "workflows" / "contracts" / "nameplate-generation.contract.json"
    return json.loads(path.read_text(encoding="utf-8"))


class WorkflowContractTests(unittest.TestCase):
    """Tests for individual workflow contract validation."""

    def test_example_contract_is_valid(self) -> None:
        contract = _load_example_contract()
        result = validate_workflow_contract(contract)
        self.assertEqual(result["id"], "nameplate-generation")
        self.assertEqual(result["version"], "1.0.0")

    def test_repository_contracts_load(self) -> None:
        contracts = load_workflow_contracts()
        self.assertGreaterEqual(len(contracts), 1)
        ids = [c["id"] for c in contracts]
        self.assertIn("nameplate-generation", ids)

    def test_cross_references_are_clean(self) -> None:
        contract = _load_example_contract()
        issues = cross_reference_stages(contract)
        self.assertEqual(issues, [])

    def test_missing_schema_version_is_rejected(self) -> None:
        contract = _load_example_contract()
        del contract["schema_version"]
        with self.assertRaisesRegex(CatalogError, "schema_version"):
            validate_workflow_contract(contract)

    def test_non_kebab_id_is_rejected(self) -> None:
        contract = _load_example_contract()
        contract["id"] = "Not Valid"
        with self.assertRaisesRegex(CatalogError, "kebab-case"):
            validate_workflow_contract(contract)

    def test_invalid_semver_is_rejected(self) -> None:
        contract = _load_example_contract()
        contract["version"] = "not-semver"
        with self.assertRaisesRegex(CatalogError, "SemVer"):
            validate_workflow_contract(contract)

    def test_empty_stages_is_rejected(self) -> None:
        contract = _load_example_contract()
        contract["stages"] = []
        with self.assertRaisesRegex(CatalogError, "non-empty"):
            validate_workflow_contract(contract)

    def test_duplicate_stage_id_is_rejected(self) -> None:
        contract = _load_example_contract()
        contract["stages"] = [contract["stages"][0], copy.deepcopy(contract["stages"][0])]
        with self.assertRaisesRegex(CatalogError, "duplicate stage id"):
            validate_workflow_contract(contract)

    def test_stage_without_produces_is_rejected(self) -> None:
        contract = _load_example_contract()
        del contract["stages"][0]["produces"]
        with self.assertRaisesRegex(CatalogError, "produces"):
            validate_workflow_contract(contract)

    def test_stage_without_artifacts_is_rejected(self) -> None:
        contract = _load_example_contract()
        contract["stages"][0]["produces"]["artifacts"] = []
        with self.assertRaisesRegex(CatalogError, "non-empty"):
            validate_workflow_contract(contract)

    def test_duplicate_artifact_id_is_rejected(self) -> None:
        contract = _load_example_contract()
        stage = contract["stages"][0]
        stage["produces"]["artifacts"] = [
            stage["produces"]["artifacts"][0],
            copy.deepcopy(stage["produces"]["artifacts"][0]),
        ]
        with self.assertRaisesRegex(CatalogError, "duplicate artifact id"):
            validate_workflow_contract(contract)

    def test_invalid_adapter_type_is_rejected(self) -> None:
        contract = _load_example_contract()
        contract["stages"][0]["adapter"]["type"] = "invalid-type"
        with self.assertRaisesRegex(CatalogError, "adapter.type"):
            validate_workflow_contract(contract)

    def test_adapter_without_entry_point_is_rejected(self) -> None:
        contract = _load_example_contract()
        del contract["stages"][0]["adapter"]["entry_point"]
        with self.assertRaisesRegex(CatalogError, "entry_point"):
            validate_workflow_contract(contract)

    def test_safety_without_local_first_is_rejected(self) -> None:
        contract = _load_example_contract()
        del contract["safety"]["local_first"]
        with self.assertRaisesRegex(CatalogError, "local_first"):
            validate_workflow_contract(contract)

    def test_invalid_side_effect_kind_is_rejected(self) -> None:
        contract = _load_example_contract()
        contract["safety"]["side_effects"][0]["kind"] = "nuclear_launch"
        with self.assertRaisesRegex(CatalogError, "kind"):
            validate_workflow_contract(contract)

    def test_duplicate_side_effect_is_rejected(self) -> None:
        contract = _load_example_contract()
        se = contract["safety"]["side_effects"][0]
        contract["safety"]["side_effects"] = [se, copy.deepcopy(se)]
        with self.assertRaisesRegex(CatalogError, "duplicate side effect"):
            validate_workflow_contract(contract)

    def test_invalid_approval_scope_is_rejected(self) -> None:
        contract = _load_example_contract()
        contract["approval_gates"][0]["scope"] = "maybe"
        with self.assertRaisesRegex(CatalogError, "scope"):
            validate_workflow_contract(contract)

    def test_invalid_auto_approve_policy_is_rejected(self) -> None:
        contract = _load_example_contract()
        contract["approval_gates"][0]["auto_approve_policy"] = "sometimes"
        with self.assertRaisesRegex(CatalogError, "auto_approve_policy"):
            validate_workflow_contract(contract)

    def test_invalid_idempotency_key_source_is_rejected(self) -> None:
        contract = _load_example_contract()
        contract["idempotency"]["key_source"] = "random"
        with self.assertRaisesRegex(CatalogError, "key_source"):
            validate_workflow_contract(contract)

    def test_duplicate_contract_ids_are_rejected(self) -> None:
        contract = _load_example_contract()
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            text = json.dumps(contract)
            (directory / "one.contract.json").write_text(text, encoding="utf-8")
            (directory / "two.contract.json").write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(CatalogError, "duplicate workflow contract id"):
                load_workflow_contracts(directory)

    def test_broken_json_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "broken.contract.json").write_text("{not json}", encoding="utf-8")
            with self.assertRaisesRegex(CatalogError, "cannot read"):
                load_workflow_contracts(directory)


class CrossReferenceTests(unittest.TestCase):
    """Tests for stage cross-referencing validation."""

    def test_depends_on_unknown_stage_is_reported(self) -> None:
        contract = _load_example_contract()
        contract["stages"][1]["depends_on"] = ["nonexistent-stage"]
        issues = cross_reference_stages(contract)
        self.assertTrue(any("depends_on unknown stage" in i for i in issues))

    def test_approval_gate_unknown_stage_is_reported(self) -> None:
        contract = _load_example_contract()
        contract["approval_gates"][0]["after_stage"] = "nonexistent-stage"
        issues = cross_reference_stages(contract)
        self.assertTrue(any("references unknown stage" in i for i in issues))

    def test_side_effect_unknown_stage_is_reported(self) -> None:
        contract = _load_example_contract()
        contract["safety"]["side_effects"][0]["stage_id"] = "nonexistent-stage"
        issues = cross_reference_stages(contract)
        self.assertTrue(any("references unknown stage" in i for i in issues))


if __name__ == "__main__":
    unittest.main()

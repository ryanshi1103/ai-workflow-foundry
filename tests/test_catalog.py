from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from flowfoundry.catalog import (
    CatalogError,
    get_component,
    load_catalog,
    validate_catalog,
    validate_component,
)

ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_repository_catalog_is_valid(self) -> None:
        components = validate_catalog(repository_root=ROOT)
        self.assertEqual(len(components), 4)

    def test_component_ids_are_unique(self) -> None:
        components = load_catalog()
        ids = [component["id"] for component in components]
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_cataloged_components_are_physically_bundled(self) -> None:
        components = load_catalog()
        bundled = {
            item["id"]: item["integration"].get("bundled_path")
            for item in components
            if item["integration"]["mode"] == "bundled"
        }
        self.assertEqual(
            bundled,
            {
                "ai-workspace-manager": "core/workspace-manager",
                "confera-media-skills": "components/confera-media-skills",
                "feedback-intelligence-system": "applications/feedback-intelligence-system",
                "print-ready-nameplate-generator": "workflows/print-ready-nameplate-generator",
            },
        )

    def test_get_known_component(self) -> None:
        component = get_component("feedback-intelligence-system")
        self.assertEqual(component["kind"], "reference-application")

    def test_legacy_component_alias_resolves_to_canonical_identity(self) -> None:
        component = get_component("feedback-analysis-system")
        self.assertEqual(component["id"], "feedback-intelligence-system")
        self.assertIn("social-negative-monitor", component["aliases"])

    def test_unknown_component_is_rejected(self) -> None:
        with self.assertRaisesRegex(CatalogError, "unknown component"):
            get_component("missing")

    def test_non_kebab_id_is_rejected(self) -> None:
        component = copy.deepcopy(load_catalog()[0])
        component["id"] = "Not Valid"
        with self.assertRaisesRegex(CatalogError, "kebab-case"):
            validate_component(component)

    def test_bundled_path_traversal_is_rejected(self) -> None:
        component = copy.deepcopy(get_component("ai-workspace-manager"))
        component["integration"]["bundled_path"] = "../outside"
        with self.assertRaisesRegex(CatalogError, "inside the repository"):
            validate_component(component)

    def test_external_component_cannot_claim_bundled_path(self) -> None:
        component = copy.deepcopy(get_component("confera-media-skills"))
        component["integration"]["mode"] = "compatible-extension"
        component["integration"]["bundled_path"] = "packs/media"
        with self.assertRaisesRegex(CatalogError, "only bundled"):
            validate_component(component)

    def test_missing_bundled_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(CatalogError, "does not exist"):
                validate_catalog(repository_root=Path(temp_dir))

    def test_duplicate_ids_across_files_are_rejected(self) -> None:
        manifest = get_component("confera-media-skills")
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            text = json.dumps(manifest)
            (directory / "one.json").write_text(text, encoding="utf-8")
            (directory / "two.json").write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(CatalogError, "duplicate component id"):
                load_catalog(directory)

    def test_alias_collision_is_rejected(self) -> None:
        first = copy.deepcopy(get_component("confera-media-skills"))
        second = copy.deepcopy(get_component("ai-workspace-manager"))
        first["aliases"] = ["legacy-component"]
        second["aliases"] = ["legacy-component"]
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "one.json").write_text(json.dumps(first), encoding="utf-8")
            (directory / "two.json").write_text(json.dumps(second), encoding="utf-8")
            with self.assertRaisesRegex(CatalogError, "id or alias"):
                load_catalog(directory)

    def test_schema_declares_same_required_top_level_fields(self) -> None:
        schema = json.loads((ROOT / "schemas/workflow-component.schema.json").read_text())
        component = load_catalog()[0]
        self.assertTrue(set(schema["required"]).issubset(component))
        self.assertTrue(set(component).issubset(schema["properties"]))


if __name__ == "__main__":
    unittest.main()

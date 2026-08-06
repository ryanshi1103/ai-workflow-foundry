from __future__ import annotations

import json
import unittest
from pathlib import Path, PurePosixPath

from flowfoundry.applications.mediaflow import (
    MediaFlowContractError,
    mediaflow_contract,
    validate_controlled_relative_path,
)
from flowfoundry.capability_registry import get_capability_ids
from flowfoundry.catalog import get_component

ROOT = Path(__file__).resolve().parents[1]


class MediaFlowApplicationTests(unittest.TestCase):
    def test_public_contract_has_private_source_boundary(self) -> None:
        contract = mediaflow_contract()
        self.assertEqual(contract["source_boundary"], "private-product")
        self.assertTrue(contract["policy"]["inputs_immutable"])
        self.assertTrue(contract["policy"]["outputs_no_overwrite"])
        self.assertIn("windows_desktop", contract["platforms"])
        self.assertIn("safe_paths", contract["shared_core"])

    def test_contract_calls_return_detached_values(self) -> None:
        first = mediaflow_contract()
        second = mediaflow_contract()
        first["platforms"].append("mutated")
        self.assertNotIn("mutated", second["platforms"])

    def test_controlled_paths_reject_escape_and_absolute_forms(self) -> None:
        invalid = (
            "",
            "../outside.mp4",
            "inputs/../outside.mp4",
            "/absolute/media.mp4",
            "C:/private/media.mp4",
            "inputs\\media.mp4",
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(MediaFlowContractError):
                validate_controlled_relative_path(value)

    def test_controlled_path_accepts_portable_relative_value(self) -> None:
        value = validate_controlled_relative_path("inputs/synthetic/photo-001.jpg")
        self.assertEqual(value, PurePosixPath("inputs/synthetic/photo-001.jpg"))

    def test_synthetic_fixture_contains_no_media_or_live_provider(self) -> None:
        path = ROOT / "applications/mediaflow/examples/synthetic-job.json"
        fixture = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(fixture["synthetic"])
        self.assertEqual(fixture["provider_mode"], "offline_fake")
        self.assertEqual(fixture["export_approval"], "pending")
        for value in fixture["inputs"] + fixture["requested_outputs"]:
            validate_controlled_relative_path(value)

    def test_legacy_product_names_resolve_to_mediaflow_catalog_entry(self) -> None:
        for identity in (
            "mediaflow",
            "huiying-media-workbench",
            "meeting-media-auto",
            "meeting-media-desktop",
        ):
            with self.subTest(identity=identity):
                self.assertEqual(get_component(identity)["id"], "mediaflow")

    def test_public_boundary_capability_is_registered(self) -> None:
        self.assertIn("controlled-media-path-validation", get_capability_ids())


if __name__ == "__main__":
    unittest.main()

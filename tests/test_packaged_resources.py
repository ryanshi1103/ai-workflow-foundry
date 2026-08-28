from __future__ import annotations

import unittest

from flowfoundry.resources import resource_path, resource_root


class PackagedResourceTests(unittest.TestCase):
    def test_source_resources_are_discoverable(self) -> None:
        root, is_source = resource_root()
        self.assertTrue(is_source)
        self.assertTrue((root / "catalog").is_dir())
        self.assertTrue(resource_path("workflows", "contracts").is_dir())


if __name__ == "__main__":
    unittest.main()

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_batch_nameplates.py"
SPEC = importlib.util.spec_from_file_location("nameplates", SCRIPT)
assert SPEC and SPEC.loader
nameplates = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nameplates)


class GeneratorHelpersTest(unittest.TestCase):
    def test_name_size(self):
        self.assertGreater(nameplates.name_size("林一"), nameplates.name_size("欧阳星河"))

    def test_safe_stem_blocks_path_characters(self):
        self.assertEqual(nameplates.safe_stem("../示例/班级"), "示例-班级")
        self.assertEqual(nameplates.safe_stem("  "), "nameplates")

    def test_read_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "names.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["姓名"])
                writer.writeheader()
                writer.writerows([{"姓名": "林一"}, {"姓名": ""}, {"姓名": "陈小满"}])
            self.assertEqual(nameplates.read_names(path), ["林一", "陈小满"])


if __name__ == "__main__":
    unittest.main()

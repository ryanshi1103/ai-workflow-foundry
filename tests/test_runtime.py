import os
import tempfile
import unittest
from pathlib import Path

from flowfoundry.runtime import resolve_project_execution_environment


class RuntimeTests(unittest.TestCase):
    def test_existing_venv_precedes_inherited_path_without_mutating_process(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            python = root / ".venv" / "bin" / "python"
            python.parent.mkdir(parents=True)
            python.write_text("", encoding="utf-8")
            python.chmod(0o755)
            before = os.environ.get("PATH")
            runtime = resolve_project_execution_environment(root)
            self.assertEqual(runtime["python"], str(python))
            self.assertTrue(runtime["env"]["PATH"].startswith(str(python.parent)))
            self.assertEqual(os.environ.get("PATH"), before)

    def test_missing_or_invalid_venv_falls_back_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = resolve_project_execution_environment(Path(directory))
            self.assertIsNone(runtime["python"])
            self.assertEqual(runtime["source"], "inherited environment")


if __name__ == "__main__":
    unittest.main()

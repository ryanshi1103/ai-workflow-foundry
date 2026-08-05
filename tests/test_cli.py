from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from flowfoundry.cli import main


class CliTests(unittest.TestCase):
    def test_validate_command(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            result = main(["validate"])
        self.assertEqual(result, 0)
        self.assertIn("validated 5", output.getvalue())

    def test_list_command(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            result = main(["list"])
        self.assertEqual(result, 0)
        self.assertIn("ai-workspace-manager", output.getvalue())
        self.assertIn("confera-media-skills", output.getvalue())

    def test_show_command_emits_json(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            result = main(["show", "print-ready-nameplate-generator"])
        self.assertEqual(result, 0)
        self.assertIn('"kind": "reference-workflow"', output.getvalue())

    def test_unknown_component_returns_diagnostic(self) -> None:
        error = io.StringIO()
        with redirect_stderr(error):
            result = main(["show", "missing"])
        self.assertEqual(result, 2)
        self.assertIn("unknown component", error.getvalue())


if __name__ == "__main__":
    unittest.main()

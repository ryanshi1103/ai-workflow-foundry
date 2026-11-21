import tempfile
import unittest
from pathlib import Path

from flowfoundry.core.context import build_goal_context
from flowfoundry.instructions import CORE_INSTRUCTION, relevant_skills


class InstructionTests(unittest.TestCase):
    def test_core_is_compact_and_outcome_first(self):
        self.assertLess(len(CORE_INSTRUCTION), 700)
        self.assertIn("DONE", CORE_INSTRUCTION)
        self.assertIn("EVIDENCE", CORE_INSTRUCTION)

    def test_skills_are_loaded_only_for_specific_media_goals(self):
        root = Path.cwd()
        self.assertEqual(relevant_skills(root, "check the README and tests"), ())
        selected = relevant_skills(root, "render this video with ffmpeg")
        self.assertEqual(len(selected), 1)
        self.assertIn("confera-ffmpeg-render", selected[0][0])

    def test_goal_context_records_skill_reason(self):
        root = Path.cwd()
        context = build_goal_context(root, "render this video with ffmpeg")
        self.assertEqual(len(context.skills), 1)
        self.assertIn("goal matched", context.skills[0][1])


if __name__ == "__main__":
    unittest.main()

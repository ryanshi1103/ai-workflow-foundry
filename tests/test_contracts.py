import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED = {
    "confera-audio-cleanup",
    "confera-caption-layout",
    "confera-chatcut-exchange",
    "confera-ffmpeg-render",
    "confera-media-inspector",
    "confera-narration-draft",
    "confera-photo-polish",
    "confera-quality-review",
    "confera-story-editor",
    "confera-timeline-review",
}


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise AssertionError(f"missing frontmatter: {path}")
    values = {}
    for line in match.group(1).splitlines():
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


class SkillContractsTest(unittest.TestCase):
    def test_skill_set_and_standard_frontmatter(self):
        folders = {path.name for path in SKILLS.iterdir() if path.is_dir()}
        self.assertEqual(folders, EXPECTED)
        for name in sorted(EXPECTED):
            metadata = frontmatter(SKILLS / name / "SKILL.md")
            self.assertEqual(set(metadata), {"name", "description"})
            self.assertEqual(metadata["name"], name)
            self.assertGreater(len(metadata["description"]), 40)

    def test_manifests_fail_closed(self):
        required_forbidden = {
            "Bash", "Shell", "Write", "Edit", "ArtifactFinalizer", "ExportApproval"
        }
        for name in sorted(EXPECTED):
            data = json.loads((SKILLS / name / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(data["name"], name)
            self.assertTrue(data["human_review_required"])
            self.assertTrue(data["input_schema"])
            self.assertTrue(data["output_schema"])
            self.assertTrue(data["network_policy"])
            self.assertTrue(data["privacy_policy"])
            self.assertTrue(required_forbidden.issubset(set(data["forbidden_tools"])))

    def test_readme_explains_every_skill(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for name in EXPECTED:
            self.assertIn(f"`{name}`", readme)


if __name__ == "__main__":
    unittest.main()

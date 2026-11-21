"""Compact task instruction and on-demand skill selection."""
from __future__ import annotations

from pathlib import Path

CORE_INSTRUCTION = """FlowFoundry authority boundary:
Act on the GOAL using the supplied CONTEXT.
CONSTRAINTS: stay inside the project; preserve user work; no external publication, paid action, credentials, or irreversible deletion.
AUTHORITY: perform local reversible actions autonomously; escalate only external/high-impact actions.
DONE: meet the stated acceptance criteria and run the smallest relevant deterministic checks.
EVIDENCE: report what changed, commands/checks run, and any uncertainty. A claim of done is not proof."""

_SKILLS = (
    ("confera-ffmpeg-render", ("video", "ffmpeg", "render")),
    ("confera-audio-cleanup", ("audio", "sound", "noise")),
    ("confera-photo-polish", ("photo", "image", "retouch")),
    ("confera-caption-layout", ("caption", "subtitle")),
)


def relevant_skills(root: Path, goal: str) -> tuple[tuple[str, str], ...]:
    text = goal.casefold()
    found = []
    for name, keywords in _SKILLS:
        if any(keyword in text for keyword in keywords):
            path = root / "components" / "confera-media-skills" / "skills" / name / "SKILL.md"
            if path.is_file():
                found.append((str(path.relative_to(root)), f"goal matched: {', '.join(keywords)}"))
    return tuple(found[:1])

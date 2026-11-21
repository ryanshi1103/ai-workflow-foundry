"""Build the smallest project context needed before execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .decisions import Decision, load_relevant_decisions
from ..project_context import ContextSnippet, retrieve_context
from ..instructions import relevant_skills


@dataclass(frozen=True)
class GoalContext:
    project_root: Path
    instruction_files: tuple[str, ...]
    decisions: tuple[Decision, ...]
    knowledge: tuple[ContextSnippet, ...] = ()
    skills: tuple[tuple[str, str], ...] = ()

    def prompt_section(self) -> str:
        lines = ["Relevant project context:"]
        if self.instruction_files:
            lines.append(
                "- Read and obey these project instruction/state files when relevant: "
                + ", ".join(self.instruction_files)
            )
        if self.decisions:
            lines.append("- Active decisions relevant to this goal:")
            lines.extend(f"  - {decision.to_context()}" for decision in self.decisions)
        else:
            lines.append("- No relevant binding project decision was selected.")
        if self.knowledge:
            lines.append("- Bounded project knowledge retrieved for this goal:")
            for snippet in self.knowledge[:4]:
                lines.append(f"  - [{snippet.kind}/{snippet.status}] {snippet.source}: {snippet.content[:450]}")
        if self.skills:
            lines.append("- Skills loaded (on demand):")
            for path, why in self.skills:
                lines.append(f"  - {path} ({why})")
                try:
                    skill_text = (self.project_root / path).read_text(encoding="utf-8")[:1800]
                except (OSError, UnicodeError):
                    skill_text = "(skill unavailable)"
                lines.append("    Guidance:\n" + skill_text)
        return "\n".join(lines)


def build_goal_context(root: Path, goal: str) -> GoalContext:
    instruction_files = tuple(
        str(path.relative_to(root))
        for path in (
            root / "AGENTS.md",
            root / "CLAUDE.md",
            root / ".ai" / "PROJECT_STATE.md",
        )
        if path.is_file()
    )
    # Goal execution needs only a small context slice; `flowfoundry ask` can
    # retrieve more when the user explicitly asks a project question.
    knowledge = retrieve_context(root, goal, limit=2, character_limit=1800).snippets
    return GoalContext(
        project_root=root,
        instruction_files=instruction_files,
        decisions=load_relevant_decisions(root, goal),
        knowledge=knowledge,
        skills=relevant_skills(root, goal),
    )

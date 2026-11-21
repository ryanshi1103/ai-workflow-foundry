"""Project question answering over bounded, canonical local context."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .goal_runner import project_root
from .project_context import RetrievalResult, _tokens, retrieve_context


# Ignore question scaffolding when selecting evidence, not when retrieving it.
_QUESTION_WORDS = set("a an the what which who how why when where did do does is are was were can could would should we our about of in to for and project please tell me".split())
_PROBLEM_MARKERS = (
    "问题", "严重", "风险", "阻塞", "限制", "problem", "issue", "risk",
    "blocker", "limitation", "weakness",
)


def _asks_about_problems(question: str) -> bool:
    lowered = question.casefold()
    return any(marker in lowered for marker in _PROBLEM_MARKERS)


def _answer_tokens(question: str) -> set[str]:
    """Add small bilingual intent aliases without inventing project facts."""
    tokens = _tokens(question) - _QUESTION_WORDS
    lowered = question.casefold()
    if _asks_about_problems(question):
        tokens.update(
            {
                "problem", "issue", "risk", "blocker", "limitation",
                "limitations", "failed", "failure", "missing", "unverified",
                "unknown", "unavailable", "depends", "block", "only", "proven",
            }
        )
    if any(marker in lowered for marker in ("当前", "现状", "现在", "current", "now")):
        tokens.update({"current", "state", "status", "known"})
    return tokens


def _condense(retrieval: RetrievalResult) -> str:
    """Select whole matching Markdown bullets/paragraphs without paraphrasing."""
    tokens = _answer_tokens(retrieval.question)
    problem_intent = _asks_about_problems(retrieval.question)
    matches = []
    for index, snippet in enumerate(retrieval.snippets, 1):
        units: list[str] = []
        lines: list[str] = []
        fenced = False
        for line in [*snippet.content.splitlines(), ""]:
            stripped = line.strip()
            boundary = not stripped or stripped.startswith(("#", "```")) or re.match(r"^(?:[-*+] |\d+[.)] )", stripped)
            if boundary and lines:
                units.append(" ".join(lines))
                lines = []
            if stripped.startswith("```"):
                fenced = not fenced
                continue
            if stripped and not fenced and not stripped.startswith("#"):
                lines.append(re.sub(r"^(?:[-*+] |\d+[.)] )", "", stripped))
        for unit_index, unit in enumerate(units):
            if len(snippet.content) >= 1600 and unit_index == len(units) - 1:
                unit += " … [excerpt may be truncated]"
            overlap = len(tokens & _tokens(unit.replace("/", " ")))
            if overlap:
                priority = 0 if snippet.status == "ACCEPTED" and snippet.kind in {"CURRENT_STATE", "DECISION"} else 1
                intent_priority = (
                    0
                    if problem_intent
                    and any(
                        marker in snippet.title.casefold()
                        for marker in ("known limitation", "known issue", "risk", "blocker")
                    )
                    else 1
                )
                matches.append(
                    (priority, intent_priority, -overlap, index, unit, snippet.status)
                )
    selected: list[str] = []
    seen: set[tuple[str, str]] = set()
    used = 0
    for _, _, _, index, unit, status in sorted(matches, key=lambda item: item[:4]):
        key = (status, unit.casefold())
        # Keep whole paragraphs and their qualifiers within the shared budget.
        if key in seen or len(selected) >= 6 or used + len(unit) > 1200:
            continue
        seen.add(key)
        used += len(unit)
        selected.append(f"- {unit} [{index}; {status}]")
    if not selected:
        return "No directly matching answer found in the bounded project excerpts. The retrieved sources may provide background; this does not establish that the project has no answer."
    return "Recorded context (selected excerpts):\n\n" + "\n".join(selected) + "\n\nThese excerpts may not fully answer the question; completeness and conflicts are not verified. CANDIDATE material is unaccepted."


def ask_project(root: Path, question: str, *, timeout_seconds: int = 300) -> dict[str, Any]:
    question = question.strip()
    if not question:
        raise ValueError("question must not be empty")
    root = project_root(root)
    retrieval = retrieve_context(root, question)
    # Deterministic excerpts are the default: this is immediate, auditable and
    # avoids spending a second model call when the answer is already recorded.
    answer = _condense(retrieval)
    executor = "local-retrieval"
    ai_calls = 0
    errors: list[str] = []
    status = "PARTIAL" if retrieval.snippets else "UNKNOWN"
    return {
        "question": question,
        "status": status,
        "answer": answer,
        "executor": executor,
        "ai_calls": ai_calls,
        "errors": errors,
        "sources": [snippet.to_dict() for snippet in retrieval.snippets],
        "retrieval": {
            "files": list(retrieval.searched_files),
            "snippets": len(retrieval.snippets),
            "characters": retrieval.characters,
            "approximate_tokens": retrieval.approximate_tokens,
            "why": list(retrieval.why),
        },
    }

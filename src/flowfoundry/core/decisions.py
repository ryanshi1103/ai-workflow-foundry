"""Load a bounded set of relevant, authoritative project decisions.

The product does not require a user to operate a ledger.  It can consume a small
JSONL ledger when one exists and can read the repository's existing active
decision bullets.  Only binding/adopted decisions enter model context.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


_AUTHORITY = {"binding", "adopted"}
_TOKEN = re.compile(r"[a-z0-9_/-]{3,}|[\u3400-\u9fff]{2,}", re.IGNORECASE)


@dataclass(frozen=True)
class Decision:
    id: str
    text: str
    status: str
    scope: tuple[str, ...] = ("project",)
    slot: str | None = None
    value: str | None = None
    supersedes: tuple[str, ...] = ()
    provenance: str = "unknown"

    def to_context(self) -> str:
        return f"[{self.id}] {self.text} (source: {self.provenance})"


def _tokens(value: str) -> set[str]:
    return {token.casefold() for token in _TOKEN.findall(value)}


def _jsonl_decisions(path: Path) -> list[Decision]:
    if not path.is_file():
        return []
    decisions: list[Decision] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(value, dict):
            continue
        decision_id = str(value.get("id", "")).strip()
        text = str(value.get("text", "")).strip()
        status = str(value.get("status", "")).strip().casefold()
        if not decision_id or not text or status not in _AUTHORITY:
            continue
        scope_value = value.get("scope", ["project"])
        scope = (
            tuple(str(item) for item in scope_value)
            if isinstance(scope_value, list)
            else (str(scope_value),)
        )
        supersedes_value = value.get("supersedes", [])
        supersedes = (
            tuple(str(item) for item in supersedes_value)
            if isinstance(supersedes_value, list)
            else ()
        )
        decisions.append(
            Decision(
                id=decision_id,
                text=text,
                status=status,
                scope=scope,
                slot=str(value["slot"]) if value.get("slot") else None,
                value=str(value["value"]) if value.get("value") else None,
                supersedes=supersedes,
                provenance=f"{path.relative_to(path.parent.parent)}:{line_number}",
            )
        )
    return decisions


def _markdown_decisions(path: Path) -> list[Decision]:
    if not path.is_file():
        return []
    decisions: list[Decision] = []
    active = False
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith("## "):
            active = stripped in {"## 当前有效决定", "## Active decisions"}
            continue
        if not active or not stripped.startswith("- "):
            continue
        text = stripped[2:].strip()
        # Ignore obvious generated-report fragments in the historical file.
        if len(text) < 24 or "|" in text or text.startswith("Remote mutations"):
            continue
        decisions.append(
            Decision(
                id=f"markdown-{line_number}",
                text=text,
                status="binding",
                provenance=f"docs/decisions.md:{line_number}",
            )
        )
    return decisions


def _active(decisions: Iterable[Decision]) -> list[Decision]:
    values = list(decisions)
    superseded = {item for decision in values for item in decision.supersedes}
    # A newer authoritative value for the same semantic slot replaces the older one.
    latest_by_slot: dict[str, Decision] = {}
    for decision in values:
        if decision.slot:
            latest_by_slot[decision.slot] = decision
    return [
        decision
        for decision in values
        if decision.id not in superseded
        and (not decision.slot or latest_by_slot[decision.slot].id == decision.id)
    ]


def load_relevant_decisions(
    root: Path,
    goal: str,
    *,
    limit: int = 5,
    character_limit: int = 4000,
) -> tuple[Decision, ...]:
    """Return only authoritative decisions sharing terms or scope with the goal."""

    candidates = _active(
        [
            *_jsonl_decisions(root / ".flowfoundry" / "decisions.jsonl"),
            *_markdown_decisions(root / "docs" / "decisions.md"),
        ]
    )
    goal_tokens = _tokens(goal)
    scored: list[tuple[int, Decision]] = []
    for decision in candidates:
        decision_tokens = _tokens(" ".join((*decision.scope, decision.text)))
        score = len(goal_tokens & decision_tokens)
        if score:
            scored.append((score, decision))
    selected: list[Decision] = []
    used = 0
    for _, decision in sorted(scored, key=lambda item: (-item[0], item[1].id)):
        size = len(decision.to_context())
        if len(selected) >= limit or used + size > character_limit:
            break
        selected.append(decision)
        used += size
    return tuple(selected)


def decision_conflicts(
    decisions: Iterable[Decision], proposals: Mapping[str, str]
) -> tuple[Decision, ...]:
    """Find proposals that contradict an occupied binding semantic slot."""

    return tuple(
        decision
        for decision in decisions
        if decision.slot
        and decision.value is not None
        and decision.slot in proposals
        and proposals[decision.slot] != decision.value
    )

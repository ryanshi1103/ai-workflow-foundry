"""Deterministic, bounded retrieval over canonical project knowledge.

This module is deliberately a file reader and scorer, not a memory platform:
there are no embeddings, vector stores, background indexing jobs, or automatic
promotion of imported material to project truth.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from secrets import token_hex
from typing import Any, Iterable

from .core.decisions import load_relevant_decisions


class KnowledgeType(StrEnum):
    CURRENT_STATE = "CURRENT_STATE"
    DECISION = "DECISION"
    FACT = "FACT"
    RESULT = "RESULT"
    EVIDENCE = "EVIDENCE"
    OPEN_LOOP = "OPEN_LOOP"


@dataclass(frozen=True)
class ContextSnippet:
    kind: str
    source: str
    title: str
    content: str
    status: str = "ACCEPTED"
    date: str | None = None
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source,
            "title": self.title,
            "content": self.content,
            "status": self.status,
            "date": self.date,
            "score": round(self.score, 3),
        }


@dataclass(frozen=True)
class RetrievalResult:
    question: str
    snippets: tuple[ContextSnippet, ...]
    searched_files: tuple[str, ...]
    characters: int
    why: tuple[str, ...]

    @property
    def approximate_tokens(self) -> int:
        return max(1, self.characters // 4)

    def prompt_text(self) -> str:
        if not self.snippets:
            return "No accepted project context matched this question."
        blocks = []
        for index, snippet in enumerate(self.snippets, 1):
            blocks.append(
                f"[{index}] {snippet.kind} / {snippet.status} / {snippet.source}"
                f"\n{snippet.title}\n{snippet.content}"
            )
        return "\n\n".join(blocks)


_TOKEN = re.compile(r"[a-z0-9_/-]{2,}|[\u3400-\u9fff]{2,}", re.IGNORECASE)
_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")


def _tokens(value: str) -> set[str]:
    return {token.casefold() for token in _TOKEN.findall(value)}


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _read_chunks(
    root: Path,
    path: Path,
    *,
    kind: KnowledgeType,
    status: str = "ACCEPTED",
    date: str | None = None,
    max_chars: int = 80_000,
) -> tuple[ContextSnippet, ...]:
    try:
        text = path.read_text(encoding="utf-8")[:max_chars]
    except (OSError, UnicodeError):
        return ()
    source = _relative(root, path)
    chunks: list[ContextSnippet] = []
    heading = source
    lines: list[str] = []

    def flush() -> None:
        nonlocal lines, heading
        content = "\n".join(lines).strip()
        if content:
            chunks.append(
                ContextSnippet(
                    kind=kind.value,
                    source=source,
                    title=heading,
                    content=content[:1600],
                    status=status,
                    date=date,
                )
            )
        lines = []

    for line in text.splitlines():
        match = _HEADING.match(line.strip())
        if match:
            flush()
            heading = match.group(1)
            lines = [line]
        else:
            lines.append(line)
        if sum(len(item) for item in lines) > 1800:
            flush()
    flush()
    return tuple(chunks)


def _report_status(path: Path) -> tuple[str, str | None]:
    try:
        lines = path.read_text(encoding="utf-8")[:6000].splitlines()
    except (OSError, UnicodeError):
        return "CANDIDATE", None
    status = "CANDIDATE"
    date = None
    for line in lines:
        if line.startswith("STATUS:"):
            value = line.split(":", 1)[1].strip().upper()
            status = "ACCEPTED" if value in {"PASS", "COMPLETE", "COMPLETED", "PARTIAL"} else "CANDIDATE"
        if line.startswith("DATE:"):
            date = line.split(":", 1)[1].strip()
    return status, date


def _canonical_snippets(root: Path) -> tuple[list[ContextSnippet], list[str]]:
    snippets: list[ContextSnippet] = []
    searched: list[str] = []
    state = root / ".ai" / "PROJECT_STATE.md"
    latest = root / ".ai" / "LATEST.md"
    if state.is_file():
        searched.append(_relative(root, state))
        snippets.extend(_read_chunks(root, state, kind=KnowledgeType.CURRENT_STATE))
    if latest.is_file():
        searched.append(_relative(root, latest))
        snippets.extend(_read_chunks(root, latest, kind=KnowledgeType.RESULT))
    reports = root / ".ai" / "reports"
    if reports.is_dir():
        for path in sorted(reports.glob("*.md"), reverse=True):
            searched.append(_relative(root, path))
            status, date = _report_status(path)
            snippets.extend(
                _read_chunks(root, path, kind=KnowledgeType.RESULT, status=status, date=date)
            )
    # Only active decisions are admitted. Superseded/advisory records never
    # become ordinary project context through this path.
    decision_path = root / "docs" / "decisions.md"
    if decision_path.is_file():
        searched.append(_relative(root, decision_path))
    for path in (root / ".ai" / "DECISIONS.md",):
        if path.is_file():
            searched.append(_relative(root, path))
    return snippets, searched


def _imported_snippets(root: Path) -> tuple[list[ContextSnippet], list[str]]:
    metadata_path = root / ".ai" / "context" / "imports.jsonl"
    snippets: list[ContextSnippet] = []
    searched: list[str] = []
    if not metadata_path.is_file():
        return snippets, searched
    for line in metadata_path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        stored = root / str(value.get("stored_path", ""))
        if not stored.is_file():
            continue
        source = _relative(root, stored)
        searched.append(source)
        snippets.extend(
            _read_chunks(
                root,
                stored,
                kind=KnowledgeType.FACT,
                status=str(value.get("status", "CANDIDATE")),
                date=str(value.get("date")) if value.get("date") else None,
            )
        )
    return snippets, searched


def _task_snippets(root: Path) -> tuple[list[ContextSnippet], list[str]]:
    task_root = root / ".flowfoundry" / "coordinator" / "tasks"
    snippets: list[ContextSnippet] = []
    searched: list[str] = []
    if not task_root.is_dir():
        return snippets, searched
    for path in sorted(task_root.glob("task-*.json"), reverse=True):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        status = str(value.get("status", ""))
        kind = KnowledgeType.OPEN_LOOP if status not in {"COMPLETED", "PARTIAL", "CANCELLED"} else KnowledgeType.RESULT
        source = _relative(root, path)
        searched.append(source)
        snippets.append(
            ContextSnippet(
                kind=kind.value,
                source=source,
                title=str(value.get("parent_goal", value.get("task_id", "task"))),
                content=(
                    f"status={status}; capability={value.get('worker_capability')}; "
                    f"priority={value.get('priority')}; error={value.get('error') or 'none'}"
                ),
                status="ACCEPTED",
                date=str(value.get("updated_at")) if value.get("updated_at") else None,
            )
        )
    return snippets, searched


def retrieve_context(
    root: Path,
    question: str,
    *,
    limit: int = 8,
    character_limit: int = 7000,
) -> RetrievalResult:
    """Retrieve the smallest scored set of canonical/candidate snippets."""
    root = root.resolve()
    canonical, searched = _canonical_snippets(root)
    imported, imported_files = _imported_snippets(root)
    tasks, task_files = _task_snippets(root)
    searched.extend(imported_files)
    searched.extend(task_files)
    candidates = [*canonical, *imported, *tasks]
    query_tokens = _tokens(question)

    # Active decisions are separately parsed to preserve supersession semantics
    # and to avoid treating historical report prose as a binding decision.
    decisions = load_relevant_decisions(root, question, limit=8, character_limit=5000)
    for decision in decisions:
        candidates.append(
            ContextSnippet(
                kind=KnowledgeType.DECISION.value,
                source=decision.provenance,
                title=decision.id,
                content=decision.text,
                status="ACCEPTED",
            )
        )

    scored: list[ContextSnippet] = []
    for snippet in candidates:
        overlap = len(query_tokens & _tokens(f"{snippet.title} {snippet.content}"))
        phrase_bonus = 1.5 if question.casefold() in snippet.content.casefold() else 0.0
        kind_bonus = {
            KnowledgeType.CURRENT_STATE.value: 1.8,
            KnowledgeType.DECISION.value: 1.5,
            KnowledgeType.OPEN_LOOP.value: 1.2,
            KnowledgeType.RESULT.value: 1.0,
            KnowledgeType.EVIDENCE.value: 0.8,
            KnowledgeType.FACT.value: 0.6,
        }.get(snippet.kind, 0.0)
        status_bonus = 0.0 if snippet.status == "ACCEPTED" else -0.8
        score = overlap + phrase_bonus + kind_bonus + status_bonus
        if score > 0:
            scored.append(ContextSnippet(**{**snippet.__dict__, "score": score}))
    if not scored:
        # A question with no lexical match still receives a bounded current-state
        # slice, never the entire archive.
        scored = [
            ContextSnippet(**{**snippet.__dict__, "score": 0.1})
            for snippet in candidates
            if snippet.kind == KnowledgeType.CURRENT_STATE.value
        ][:2]
    scored.sort(key=lambda snippet: (-snippet.score, snippet.status != "ACCEPTED", snippet.source, snippet.title))
    selected: list[ContextSnippet] = []
    used = 0
    for snippet in scored:
        if len(selected) >= limit or used + len(snippet.content) > character_limit:
            continue
        selected.append(snippet)
        used += len(snippet.content)
    why = (
        "lexical overlap over canonical project files and active decisions",
        "candidate imports are labeled and ranked below accepted truth",
        "historical docs/archive and raw conversations are excluded",
    )
    return RetrievalResult(
        question=question,
        snippets=tuple(selected),
        searched_files=tuple(dict.fromkeys(searched)),
        characters=used,
        why=why,
    )


def import_context(root: Path, source: Path, *, title: str | None = None) -> dict[str, Any]:
    """Copy an explicit handoff into the local candidate context area."""
    source = source.expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"context file does not exist: {source}")
    try:
        content = source.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise ValueError("context import must be UTF-8 text") from exc
    if not content.strip():
        raise ValueError("context file is empty")
    context_root = root / ".ai" / "context" / "imports"
    context_root.mkdir(parents=True, exist_ok=True)
    identifier = f"import-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{token_hex(3)}"
    stored = context_root / f"{identifier}.md"
    stored.write_text(content, encoding="utf-8")
    metadata = {
        "id": identifier,
        "source": str(source),
        "stored_path": _relative(root, stored),
        "title": title or source.stem,
        "date": datetime.now(timezone.utc).isoformat(),
        "status": "CANDIDATE",
    }
    metadata_path = root / ".ai" / "context" / "imports.jsonl"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(metadata, ensure_ascii=False) + "\n")
    return metadata

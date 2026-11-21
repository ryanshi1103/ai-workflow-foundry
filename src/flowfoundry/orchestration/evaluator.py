"""Stable reviewer protocol validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import ProviderResult, ReviewDecision


@dataclass(frozen=True)
class ReviewRecord:
    decision: ReviewDecision
    commit: str
    task_id: str
    tests: tuple[str, ...]
    blocking_findings: tuple[str, ...]
    suggested_fixes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "decision": self.decision.value,
            "commit": self.commit,
            "task_id": self.task_id,
            "tests": list(self.tests),
            "blocking_findings": list(self.blocking_findings),
            "suggested_fixes": list(self.suggested_fixes),
        }


def evaluate_review(task_id: str, result: ProviderResult) -> ReviewRecord:
    decision = result.review or ReviewDecision.REVIEW_PENDING
    outputs = result.outputs
    return ReviewRecord(
        decision=decision,
        commit=str(outputs.get("commit", "UNCOMMITTED")),
        task_id=task_id,
        tests=tuple(str(item) for item in outputs.get("tests", ())),
        blocking_findings=(result.findings if decision == ReviewDecision.BLOCKED else ()),
        suggested_fixes=tuple(str(item) for item in outputs.get("suggested_fixes", ())),
    )

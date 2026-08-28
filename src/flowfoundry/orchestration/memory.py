"""Small project-local performance memory for explainable routing feedback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AgentSpec, ProviderResult, TaskSpec
from .workspace import atomic_write_json, secure_file_lock, utc_now


class AgentPerformanceMemory:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).resolve()

    def record(
        self,
        agent: AgentSpec,
        task: TaskSpec,
        result: ProviderResult,
        usage: dict[str, Any],
        category: str,
        *,
        execution_kind: str = "unknown",
    ) -> None:
        with secure_file_lock(self.path.with_suffix(".lock")):
            data = self._read()
            agents = data.setdefault("agents", {})
            stats = agents.setdefault(
                agent.id,
                {
                    "provider": agent.provider,
                    "model": agent.model,
                    "executions": 0,
                    "successes": 0,
                    "failures": 0,
                    "provider_calls": 0,
                    "latency_ms": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "estimated_cost_usd": 0.0,
                    "review_decisions": {},
                    "categories": {},
                },
            )
            stats["executions"] += 1
            stats["successes" if result.success else "failures"] += 1
            stats["provider_calls"] += int(usage.get("provider_calls") or 0)
            for field in ("latency_ms", "input_tokens", "output_tokens"):
                stats[field] += int(usage.get(field) or 0)
            stats["estimated_cost_usd"] += float(usage.get("estimated_cost_usd") or 0.0)
            decision = result.review.value if result.review is not None else None
            if decision:
                decisions = stats["review_decisions"]
                decisions[decision] = int(decisions.get(decision, 0)) + 1
            category_stats = stats["categories"].setdefault(
                category,
                {"executions": 0, "successes": 0, "failures": 0},
            )
            category_stats["executions"] += 1
            category_stats["successes" if result.success else "failures"] += 1
            kind_stats = stats.setdefault("execution_kinds", {}).setdefault(
                execution_kind,
                {"executions": 0, "successes": 0, "failures": 0},
            )
            kind_stats["executions"] += 1
            kind_stats["successes" if result.success else "failures"] += 1
            stats["last_task_role"] = task.role
            stats["updated_at"] = utc_now()
            data["updated_at"] = utc_now()
            atomic_write_json(self.path, data)

    def routing_scores(
        self,
        *,
        minimum_samples: int = 3,
        execution_kind: str | None = None,
    ) -> dict[str, float]:
        scores: dict[str, float] = {}
        for agent_id, stats in self._read().get("agents", {}).items():
            selected = stats
            if execution_kind is not None:
                selected = stats.get("execution_kinds", {}).get(execution_kind, {})
            executions = int(selected.get("executions", 0))
            if executions >= minimum_samples:
                scores[str(agent_id)] = int(selected.get("successes", 0)) / executions
        return scores

    def record_meeting_contribution(
        self,
        agent_id: str,
        run_id: str,
        *,
        disagreed: bool,
        cross_reviewed: bool,
        accepted: bool,
    ) -> None:
        """Record only small meeting usefulness counters, idempotently per run."""

        with secure_file_lock(self.path.with_suffix(".lock")):
            data = self._read()
            stats = data.setdefault("agents", {}).setdefault(agent_id, {})
            meeting_runs = stats.setdefault("meeting_run_ids", [])
            if run_id in meeting_runs:
                return
            meeting_runs.append(run_id)
            stats["meeting_contributions"] = int(stats.get("meeting_contributions", 0)) + 1
            stats["meeting_disagreements"] = int(stats.get("meeting_disagreements", 0)) + int(
                disagreed
            )
            stats["meeting_cross_reviews"] = int(stats.get("meeting_cross_reviews", 0)) + int(
                cross_reviewed
            )
            stats["meeting_contributions_accepted"] = int(
                stats.get("meeting_contributions_accepted", 0)
            ) + int(accepted)
            stats["updated_at"] = utc_now()
            data["updated_at"] = utc_now()
            atomic_write_json(self.path, data)

    def _read(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {"schema_version": 1, "agents": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"schema_version": 1, "agents": {}}
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            return {"schema_version": 1, "agents": {}}
        return data


class MeetingExperienceLedger:
    """Project-local, idempotent record used for future strategy learning."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).resolve()

    def record(self, experience: dict[str, Any]) -> None:
        run_id = str(experience["run_id"])
        record_id = str(experience.get("experience_id", run_id))
        with secure_file_lock(self.path.with_suffix(".lock")):
            data = self._read()
            records = data.setdefault("records", {})
            if record_id in records:
                return
            records[record_id] = experience
            data["updated_at"] = utc_now()
            atomic_write_json(self.path, data)

    def _read(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {"schema_version": 1, "records": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"schema_version": 1, "records": {}}
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            return {"schema_version": 1, "records": {}}
        return data

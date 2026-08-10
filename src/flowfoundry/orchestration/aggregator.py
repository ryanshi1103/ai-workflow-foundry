"""Deterministic aggregation of persisted run state."""

from __future__ import annotations

from typing import Any

from .isolation import WorktreeError, WorktreeManager
from .models import TaskStatus
from .workspace import RunWorkspace, atomic_write_json, atomic_write_text, utc_now


class ResultAggregator:
    def aggregate(self, workspace: RunWorkspace) -> dict[str, Any]:
        manifest = workspace.manifest()
        completed: list[str] = []
        unfinished: list[str] = []
        tests: list[str] = []
        commits: list[str] = []
        generated_files: list[str] = []
        risks: list[str] = []
        task_usage: list[dict[str, Any]] = []
        for task in workspace.plan().tasks:
            state = manifest["tasks"][task.id]
            if isinstance(state.get("usage"), dict):
                task_usage.append(state["usage"])
            if state["status"] == TaskStatus.COMPLETED.value:
                completed.append(task.id)
            else:
                unfinished.append(task.id)
                if state.get("error"):
                    risks.append(f"{task.id}: {state['error']}")
            tests.extend(task.validation_commands)
            result_path = workspace.task_dir(task.id) / "result.json"
            if result_path.exists():
                generated_files.append(str(result_path.relative_to(workspace.path)))
                result = workspace.read_json(str(result_path.relative_to(workspace.path)))
                commit = result.get("outputs", {}).get("commit")
                if commit:
                    commits.append(str(commit))
        human_path = workspace.contained("HUMAN_ACTIONS_REQUIRED.md")
        meeting = manifest.get("meeting")
        meeting_usage = meeting.get("usage") if isinstance(meeting, dict) else None
        if isinstance(meeting_usage, dict):
            usage = {
                key: meeting_usage.get(key)
                for key in (
                    "provider_calls",
                    "input_tokens",
                    "output_tokens",
                    "latency_ms",
                    "estimated_cost_usd",
                    "token_status",
                    "cost_status",
                )
            }
        else:
            usage = self._aggregate_usage(task_usage)
        isolation: list[dict[str, Any]] = []
        if any(workspace.contained("worktrees").glob("wt-*.json")):
            try:
                isolation = WorktreeManager(workspace).status_records()
            except WorktreeError:
                isolation = []
        report = {
            "schema_version": 1,
            "run_id": workspace.run_id,
            "status": manifest["status"],
            "completed_tasks": completed,
            "unfinished_tasks": unfinished,
            "tests": sorted(set(tests)),
            "risks": risks,
            "human_actions_required": human_path.exists(),
            "generated_files": generated_files,
            "commits": sorted(set(commits)),
            "usage": usage,
            "meeting": self._meeting_summary(meeting) if isinstance(meeting, dict) else None,
            "workspace_isolation": isolation,
            "next_step": "inspect unfinished tasks" if unfinished else "review final artifacts",
            "created_at": utc_now(),
        }
        atomic_write_json(workspace.contained("final", "report.json"), report)
        lines = [
            f"# Run {workspace.run_id}",
            "",
            f"- Status: {report['status']}",
            f"- Completed: {', '.join(completed) or 'none'}",
            f"- Unfinished: {', '.join(unfinished) or 'none'}",
            f"- Human actions required: {report['human_actions_required']}",
            "",
        ]
        atomic_write_text(workspace.contained("final", "report.md"), "\n".join(lines))
        return report

    @staticmethod
    def _meeting_summary(meeting: dict[str, Any]) -> dict[str, Any]:
        cancellation = meeting.get("cancellation")
        cancellation = cancellation if isinstance(cancellation, dict) else {}
        return {
            "state": meeting["state"],
            "rounds_executed": list(meeting.get("rounds_executed", ())),
            "conflicts_detected": len(meeting.get("conflicts", ())),
            "early_stopped": bool(meeting.get("early_stopped", False)),
            "dissent_count": len(meeting.get("dissent", ())),
            "budget_status": meeting.get("budget_status", "unknown"),
            "result_ref": meeting.get("result_ref"),
            "experience_ref": meeting.get("experience_ref"),
            "cancel_requested": bool(meeting.get("cancel_requested", False)),
            "termination_status": cancellation.get("termination_status"),
            "active_provider": next(
                (
                    execution.get("provider")
                    for execution in cancellation.get("executions", ())
                    if isinstance(execution, dict)
                ),
                None,
            ),
            "forced_termination": bool(cancellation.get("forced_termination", False)),
            "partial_result": bool(cancellation.get("partial_result", False)),
        }

    @staticmethod
    def _aggregate_usage(task_usage: list[dict[str, Any]]) -> dict[str, Any]:
        def total(field: str) -> int | float | None:
            values = [usage[field] for usage in task_usage if usage.get(field) is not None]
            return sum(values) if values else None

        token_statuses = {usage.get("token_status", "unavailable") for usage in task_usage}
        cost_statuses = {usage.get("cost_status", "unavailable") for usage in task_usage}
        return {
            "provider_calls": int(total("provider_calls") or 0),
            "input_tokens": total("input_tokens"),
            "output_tokens": total("output_tokens"),
            "latency_ms": total("latency_ms"),
            "estimated_cost_usd": total("estimated_cost_usd"),
            "token_status": next(iter(token_statuses)) if len(token_statuses) == 1 else "unavailable",
            "cost_status": next(iter(cost_statuses)) if len(cost_statuses) == 1 else "unavailable",
        }

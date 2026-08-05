"""Deterministic aggregation of persisted run state."""

from __future__ import annotations

from typing import Any

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
        for task in workspace.plan().tasks:
            state = manifest["tasks"][task.id]
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

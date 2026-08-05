"""Recovery and explicit retry operations for persisted runs."""

from __future__ import annotations

from typing import Any

from .models import TaskPlan, TaskStatus
from .workspace import RunWorkspace, stable_hash, utc_now


class RecoveryManager:
    def recover_interrupted(self, workspace: RunWorkspace) -> dict[str, Any]:
        def recover(manifest: dict[str, Any]) -> dict[str, Any]:
            recovered: list[str] = []
            for task_id, state in manifest["tasks"].items():
                if state["status"] == TaskStatus.RUNNING.value:
                    state["status"] = TaskStatus.PENDING.value
                    state["recovered_at"] = utc_now()
                    recovered.append(task_id)
            manifest["recovered_tasks"] = sorted(recovered)
            manifest["status"] = "running"
            return manifest

        return workspace.update_manifest(recover)

    def retry_failed_task(self, workspace: RunWorkspace, task_id: str) -> dict[str, Any]:
        current = workspace.manifest()["tasks"][task_id]["status"]
        if current not in {
            TaskStatus.FAILED.value,
            TaskStatus.BLOCKED.value,
            TaskStatus.SKIPPED.value,
        }:
            raise ValueError(f"task is not retryable from status: {current}")
        return workspace.update_task(task_id, status=TaskStatus.PENDING.value, error=None)

    def reconcile_plan(self, workspace: RunWorkspace, plan: TaskPlan) -> dict[str, Any]:
        """Preserve unchanged completed tasks and reset changed inputs plus dependents."""

        incoming = {task.id: task for task in plan.tasks}

        def reconcile(manifest: dict[str, Any]) -> dict[str, Any]:
            previous = manifest["tasks"]
            changed: set[str] = set()
            new_states: dict[str, Any] = {}
            for task in plan.tasks:
                input_hash = stable_hash(task.to_dict())
                prior = previous.get(task.id)
                dependencies_changed = bool(set(task.dependencies).intersection(changed))
                if prior and prior.get("input_hash") == input_hash and not dependencies_changed:
                    new_states[task.id] = prior
                else:
                    changed.add(task.id)
                    new_states[task.id] = {
                        "status": TaskStatus.PENDING.value,
                        "attempts": 0,
                        "agent_id": None,
                        "input_hash": input_hash,
                    }
            manifest["plan"] = plan.to_dict()
            manifest["goal"] = plan.goal
            manifest["input_hash"] = stable_hash(plan.to_dict())
            manifest["tasks"] = new_states
            manifest["status"] = "running"
            manifest["changed_tasks"] = sorted(changed)
            return manifest

        if set(incoming) != {task.id for task in plan.tasks}:
            raise ValueError("duplicate task ids")
        return workspace.update_manifest(reconcile)

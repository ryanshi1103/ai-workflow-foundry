"""Recovery and explicit retry operations for persisted runs."""

from __future__ import annotations

from typing import Any

from .models import TaskPlan, TaskStatus
from .workspace import RunWorkspace, stable_hash, utc_now


class RecoveryManager:
    def recover_interrupted(self, workspace: RunWorkspace) -> dict[str, Any]:
        def recover(manifest: dict[str, Any]) -> dict[str, Any]:
            meeting = manifest.get("meeting")
            if isinstance(meeting, dict) and meeting.get("state") in {
                "completed",
                "blocked",
                "failed",
                "cancelled",
                "budget_exhausted",
            }:
                manifest["recovered_tasks"] = []
                return manifest
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
        manifest = workspace.manifest()
        current = manifest["tasks"][task_id]["status"]
        if current not in {
            TaskStatus.FAILED.value,
            TaskStatus.BLOCKED.value,
            TaskStatus.SKIPPED.value,
            TaskStatus.SKIPPED_PENDING_HUMAN.value,
        }:
            raise ValueError(f"task is not retryable from status: {current}")

        plan = workspace.plan()

        def reset_retry_chain(run_manifest: dict[str, Any]) -> dict[str, Any]:
            run_manifest["tasks"][task_id].update(
                {"status": TaskStatus.PENDING.value, "error": None}
            )
            revived = {task_id}
            for task in plan.tasks:
                state = run_manifest["tasks"][task.id]
                if (
                    state["status"] == TaskStatus.SKIPPED.value
                    and set(task.dependencies).intersection(revived)
                ):
                    state.update(
                        {
                            "status": TaskStatus.PENDING.value,
                            "error": None,
                            "attempts": 0,
                            "agent_id": None,
                        }
                    )
                    revived.add(task.id)
            run_manifest["status"] = "running"
            run_manifest["revived_tasks"] = sorted(revived)
            return run_manifest

        return workspace.update_manifest(reset_retry_chain)

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

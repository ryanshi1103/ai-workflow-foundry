"""Recovery and explicit retry operations for persisted runs."""

from __future__ import annotations

from typing import Any

from .execution import ProviderExecutionHandle
from .isolation import WorktreeError, WorktreeManager
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
                "cancel_unverified",
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

        recovered_manifest = workspace.update_manifest(recover)
        if any(workspace.contained("worktrees").glob("wt-*.json")):
            try:
                manager = WorktreeManager(workspace)
                records = manager.reconcile(
                    active_executions=ProviderExecutionHandle.recovery_status_for_run(
                        workspace.path
                    )
                )

                def record_worktrees(manifest: dict[str, Any]) -> dict[str, Any]:
                    manifest["worktree_recovery"] = [
                        {
                            "worktree_id": record["worktree_id"],
                            "status": record["status"],
                            "retained_after_run": bool(
                                record.get("retained_after_run", False)
                            ),
                        }
                        for record in records
                    ]
                    return manifest

                recovered_manifest = workspace.update_manifest(record_worktrees)
            except WorktreeError as exc:
                def warning(manifest: dict[str, Any]) -> dict[str, Any]:
                    manifest["worktree_recovery_warning"] = f"{exc.code}: {exc}"
                    return manifest

                recovered_manifest = workspace.update_manifest(warning)
        return recovered_manifest

    def retry_failed_task(self, workspace: RunWorkspace, task_id: str) -> dict[str, Any]:
        active = [
            record
            for record in ProviderExecutionHandle.status_for_run(workspace.path)
            if record.get("task_id") == task_id
            and record.get("state")
            in {"running", "cancel_requested", "terminating", "killing"}
        ]
        if active:
            raise ValueError("task still has an active native provider execution")
        manifest = workspace.manifest()
        current = manifest["tasks"][task_id]["status"]
        if current not in {
            TaskStatus.FAILED.value,
            TaskStatus.BLOCKED.value,
            TaskStatus.SKIPPED.value,
            TaskStatus.SKIPPED_PENDING_HUMAN.value,
            TaskStatus.CANCELLED.value,
        }:
            raise ValueError(f"task is not retryable from status: {current}")

        plan = workspace.plan()

        def reset_retry_chain(run_manifest: dict[str, Any]) -> dict[str, Any]:
            current_attempts = int(run_manifest["tasks"][task_id].get("attempts", 0))
            run_manifest["tasks"][task_id].update(
                {
                    "status": TaskStatus.PENDING.value,
                    "error": None,
                    "manual_attempt_limit": current_attempts + 1,
                    "retry_requested_at": utc_now(),
                }
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
            run_manifest["cancel_requested"] = False
            meeting = run_manifest.get("meeting")
            if isinstance(meeting, dict) and meeting.get("state") in {
                "cancelled",
                "cancel_unverified",
            }:
                meeting["attempt"] = int(meeting.get("attempt", 1)) + 1
                meeting["cancel_requested"] = False
                meeting["cancel_requested_at"] = None
                meeting["cancellation"] = None
                meeting["experience_ref"] = None
                meeting.pop("usage", None)
                meeting.pop("finished_at", None)
                meeting.pop("terminal_reason", None)
                meeting["started_at"] = utc_now()
                if task_id in meeting.get("participants", {}):
                    meeting["state"] = "round1_running"
                    meeting["participants"][task_id].update(
                        {
                            "status": TaskStatus.PENDING.value,
                            "finished_at": None,
                            "partial_result": False,
                        }
                    )
                elif task_id in meeting.get("validation", {}):
                    meeting["state"] = "validating"
                    meeting["validation"][task_id] = {
                        "status": TaskStatus.PENDING.value
                    }
                else:
                    meeting["state"] = "planned"
                meeting["state_updated_at"] = utc_now()
                run_manifest.pop("finished_at", None)
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

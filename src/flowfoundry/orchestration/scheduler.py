"""Dependency-aware, retry-bounded scheduler for offline or explicit providers."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
from typing import Any

from .approvals import ApprovalGate
from .evaluator import evaluate_review
from .mailbox import Mailbox
from .meeting import MeetingRuntime
from .memory import AgentPerformanceMemory
from .models import ProviderResult, ReviewDecision, TaskSpec, TaskStatus
from .providers import Provider
from .provider_setup import ProviderSetupFlow
from .router import TaskRouter
from .workspace import RunWorkspace, atomic_write_json, utc_now

_DEPENDENCY_FAILURE = {
    TaskStatus.BLOCKED.value,
    TaskStatus.FAILED.value,
    TaskStatus.SKIPPED.value,
    TaskStatus.SKIPPED_PENDING_HUMAN.value,
}


class RunScheduler:
    def __init__(
        self,
        router: TaskRouter,
        provider: Provider,
        *,
        max_workers: int = 4,
        approval_gate: ApprovalGate | None = None,
    ) -> None:
        self.router = router
        self.provider = provider
        self.max_workers = max(1, max_workers)
        self.approval_gate = approval_gate or ApprovalGate()
        self._agent_slots = {
            agent.id: Semaphore(agent.concurrency_limit)
            for agent in self.router.registry.list()
        }

    def run(self, workspace: RunWorkspace) -> dict[str, Any]:
        plan = workspace.plan()
        if plan.meeting_plan is not None:
            return MeetingRuntime(
                self.router,
                self.provider,
                approval_gate=self.approval_gate,
            ).run(workspace)
        performance = AgentPerformanceMemory(workspace.performance_memory_path)
        self.router.history_scores = performance.routing_scores()
        tasks = {task.id: task for task in plan.tasks}
        while True:
            manifest = workspace.manifest()
            states = manifest["tasks"]
            pending = [task for task in plan.tasks if states[task.id]["status"] == TaskStatus.PENDING.value]
            if not pending:
                break

            progress = self._skip_failed_dependents(workspace, pending, states)
            manifest = workspace.manifest()
            states = manifest["tasks"]
            ready = [
                task
                for task in pending
                if states[task.id]["status"] == TaskStatus.PENDING.value
                and self._dependencies_satisfied(task, states, tasks)
            ]
            if not ready:
                if not progress:
                    break
                continue

            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(ready))) as pool:
                futures = {pool.submit(self._execute_task, workspace, task): task.id for task in ready}
                for future in as_completed(futures):
                    task_id = futures[future]
                    try:
                        future.result()
                    except Exception as exc:  # provider boundary: persist, never lose scheduler state
                        workspace.update_task(
                            task_id,
                            status=TaskStatus.FAILED.value,
                            error=f"{type(exc).__name__}: {exc}",
                            finished_at=utc_now(),
                        )

        return self._finalize_run_status(workspace)

    @staticmethod
    def _dependencies_satisfied(
        task: TaskSpec,
        states: dict[str, Any],
        tasks: dict[str, TaskSpec],
    ) -> bool:
        for dependency in task.dependencies:
            status = states[dependency]["status"]
            if status == TaskStatus.COMPLETED.value:
                continue
            if status == TaskStatus.REVIEW_REQUIRED.value and tasks[dependency].role != "reviewer":
                continue
            return False
        return True

    def _skip_failed_dependents(
        self,
        workspace: RunWorkspace,
        pending: list[TaskSpec],
        states: dict[str, Any],
    ) -> bool:
        changed = False
        for task in pending:
            failed = [dep for dep in task.dependencies if states[dep]["status"] in _DEPENDENCY_FAILURE]
            if failed:
                workspace.update_task(
                    task.id,
                    status=TaskStatus.SKIPPED.value,
                    error=f"dependency did not complete: {', '.join(failed)}",
                    finished_at=utc_now(),
                )
                changed = True
        return changed

    def _execute_task(self, workspace: RunWorkspace, task: TaskSpec) -> None:
        decision = self.approval_gate.evaluate(workspace, task)
        if not decision.allowed:
            workspace.update_task(
                task.id,
                status=TaskStatus.SKIPPED_PENDING_HUMAN.value,
                error=decision.reason,
                finished_at=utc_now(),
            )
            return

        try:
            agent = self.router.route(task)
        except LookupError as exc:
            ProviderSetupFlow(self.router.registry).record(workspace, task, str(exc))
            workspace.update_task(
                task.id,
                status=TaskStatus.BLOCKED.value,
                error=str(exc),
                finished_at=utc_now(),
            )
            return
        current_attempts = int(workspace.manifest()["tasks"][task.id].get("attempts", 0))
        final_result: ProviderResult | None = None
        attempt_usage: list[dict[str, Any]] = []
        with self._agent_slots[agent.id]:
            for attempt in range(current_attempts + 1, task.retry_limit + 2):
                workspace.update_task(
                    task.id,
                    status=TaskStatus.RUNNING.value,
                    attempts=attempt,
                    agent_id=agent.id,
                    started_at=utc_now(),
                )
                final_result = self.provider.execute(
                    task,
                    agent,
                    workspace.task_dir(task.id),
                    workspace.project_root,
                )
                attempt_usage.append(final_result.usage.to_dict())
                if final_result.success:
                    break
        assert final_result is not None
        workspace.write_task_result(task.id, final_result.to_dict())
        usage = self._aggregate_usage(attempt_usage)
        workspace.update_task(task.id, usage=usage)
        profile = workspace.plan().task_profile
        category = profile.task_type if profile is not None else task.role
        memory = AgentPerformanceMemory(workspace.performance_memory_path)
        try:
            memory.record(agent, task, final_result, usage, category)
            self.router.history_scores = memory.routing_scores()
        except (OSError, TypeError, ValueError) as exc:
            workspace.update_task(
                task.id,
                memory_warning=f"performance memory unavailable: {type(exc).__name__}",
            )
        Mailbox(workspace).send(
            sender=agent.id,
            recipient="aggregator",
            task_id=task.id,
            kind="task_result",
            payload=final_result.to_dict(),
        )
        if not final_result.success:
            workspace.update_task(
                task.id,
                status=TaskStatus.FAILED.value,
                error=final_result.summary,
                finished_at=utc_now(),
            )
            return

        if task.role == "reviewer":
            self._persist_review(workspace, task, final_result)
            return

        status = TaskStatus.REVIEW_REQUIRED if task.review_required else TaskStatus.COMPLETED
        workspace.update_task(task.id, status=status.value, finished_at=utc_now(), error=None)

    @staticmethod
    def _aggregate_usage(attempts: list[dict[str, Any]]) -> dict[str, Any]:
        def total(field: str) -> int | float | None:
            values = [attempt[field] for attempt in attempts if attempt.get(field) is not None]
            return sum(values) if values else None

        token_statuses = {attempt.get("token_status", "unavailable") for attempt in attempts}
        cost_statuses = {attempt.get("cost_status", "unavailable") for attempt in attempts}
        return {
            "provider_calls": len(attempts),
            "input_tokens": total("input_tokens"),
            "output_tokens": total("output_tokens"),
            "latency_ms": total("latency_ms"),
            "estimated_cost_usd": total("estimated_cost_usd"),
            "token_status": next(iter(token_statuses)) if len(token_statuses) == 1 else "unavailable",
            "cost_status": next(iter(cost_statuses)) if len(cost_statuses) == 1 else "unavailable",
        }

    def _persist_review(
        self,
        workspace: RunWorkspace,
        task: TaskSpec,
        result: ProviderResult,
    ) -> None:
        record = evaluate_review(task.id, result)
        atomic_write_json(workspace.contained("reviews", f"{task.id}.json"), record.to_dict())
        source_task = task.inputs.get("source_task")
        if record.decision in {ReviewDecision.APPROVED, ReviewDecision.APPROVED_WITH_NOTES}:
            status = TaskStatus.COMPLETED
            if isinstance(source_task, str):
                workspace.update_task(source_task, status=TaskStatus.COMPLETED.value, reviewed_at=utc_now())
        elif record.decision == ReviewDecision.BLOCKED:
            status = TaskStatus.BLOCKED
            if isinstance(source_task, str):
                workspace.update_task(source_task, status=TaskStatus.BLOCKED.value, reviewed_at=utc_now())
        else:
            status = TaskStatus.REVIEW_REQUIRED
        workspace.update_task(task.id, status=status.value, finished_at=utc_now(), error=None)

    def _finalize_run_status(
        self,
        workspace: RunWorkspace,
    ) -> dict[str, Any]:
        def finalize(manifest: dict[str, Any]) -> dict[str, Any]:
            statuses = {state["status"] for state in manifest["tasks"].values()}
            if statuses <= {TaskStatus.COMPLETED.value}:
                manifest["status"] = "completed"
            elif TaskStatus.REVIEW_REQUIRED.value in statuses or TaskStatus.PENDING.value in statuses:
                manifest["status"] = "review_pending"
            elif statuses.intersection(_DEPENDENCY_FAILURE):
                manifest["status"] = "completed_with_blockers"
            else:
                manifest["status"] = "running"
            manifest["finished_at"] = utc_now()
            return manifest

        return workspace.update_manifest(finalize)

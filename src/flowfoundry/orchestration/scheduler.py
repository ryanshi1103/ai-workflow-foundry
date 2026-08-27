"""Dependency-aware, retry-bounded scheduler for offline or explicit providers."""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path
from threading import Semaphore
from typing import Any

from .approvals import ApprovalGate
from .decisions import DecisionContextService
from .evaluator import evaluate_review
from .isolation import WorktreeError, WorktreeManager
from .mailbox import Mailbox
from .meeting import MeetingRuntime
from .memory import AgentPerformanceMemory
from .models import (
    AgentSpec,
    IsolationMode,
    ProviderResult,
    ReviewDecision,
    TaskSpec,
    TaskStatus,
)
from .provider_setup import ProviderSetupFlow
from .providers import Provider
from .router import TaskRouter
from .workspace import RunWorkspace, atomic_write_json, utc_now
from .workspace_preflight import WorkspaceCompatibilityPreflight

_DEPENDENCY_FAILURE = {
    TaskStatus.BLOCKED.value,
    TaskStatus.FAILED.value,
    TaskStatus.SKIPPED.value,
    TaskStatus.SKIPPED_PENDING_HUMAN.value,
    TaskStatus.CANCELLED.value,
}


class RunScheduler:
    def __init__(
        self,
        router: TaskRouter,
        provider: Provider,
        *,
        max_workers: int = 4,
        approval_gate: ApprovalGate | None = None,
        workspace_preflight: WorkspaceCompatibilityPreflight | None = None,
    ) -> None:
        self.router = router
        self.provider = provider
        self.max_workers = max(1, max_workers)
        self.approval_gate = approval_gate or ApprovalGate()
        self.workspace_preflight = workspace_preflight or WorkspaceCompatibilityPreflight()
        self._agent_slots = {
            agent.id: Semaphore(agent.concurrency_limit)
            for agent in self.router.registry.list()
        }
        self._shared_writer_slot = Semaphore(1)

    def run(self, workspace: RunWorkspace) -> dict[str, Any]:
        plan = workspace.plan()
        context_limit = 10_000
        if plan.meeting_plan is not None:
            context_limit = max(
                2_000,
                min(9_000, plan.meeting_plan.context_char_limit * 3 // 4),
            )
        DecisionContextService().prepare(workspace, max_chars=context_limit)
        if plan.meeting_plan is not None:
            return MeetingRuntime(
                self.router,
                self.provider,
                approval_gate=self.approval_gate,
            ).run(workspace)
        self._reset_workspace_preflight_blockers(workspace)
        performance = AgentPerformanceMemory(workspace.performance_memory_path)
        self.router.history_scores = performance.routing_scores(
            execution_kind=self._execution_kind()
        )
        tasks = {task.id: task for task in plan.tasks}
        while True:
            manifest = workspace.manifest()
            states = manifest["tasks"]
            if manifest.get("cancel_requested"):
                for task in plan.tasks:
                    if states[task.id]["status"] == TaskStatus.PENDING.value:
                        workspace.update_task(
                            task.id,
                            status=TaskStatus.CANCELLED.value,
                            error="operator cancellation",
                            finished_at=utc_now(),
                        )
                break
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
        task = DecisionContextService.inject_task(workspace, task)
        if workspace.manifest().get("cancel_requested"):
            workspace.update_task(
                task.id,
                status=TaskStatus.CANCELLED.value,
                error="operator cancellation",
                finished_at=utc_now(),
            )
            return
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
        project_workspace = workspace.project_root_path
        if self._execution_kind() != "mock" and not self._workspace_preflight_allows(
            workspace,
            task,
            agent,
            project_workspace,
            current_attempts=current_attempts,
        ):
            return
        execution_workspace = project_workspace
        manager: WorktreeManager | None = None
        worktree: dict[str, Any] | None = None
        source_task = task.inputs.get("source_task")
        source_state = (
            workspace.manifest()["tasks"].get(source_task, {})
            if isinstance(source_task, str)
            else {}
        )
        source_worktree_id = source_state.get("worktree_id")
        provider_requires = bool(
            getattr(self.provider, "requires_managed_worktree", False)
        )
        mode = WorktreeManager.isolation_mode(
            required_permissions=task.required_permissions,
            agent_permissions=agent.permission_profile,
            provider_requires_isolation=provider_requires,
        )
        if source_worktree_id or mode == IsolationMode.MANAGED_WORKTREE:
            try:
                manager = WorktreeManager(workspace)
                if source_worktree_id:
                    worktree = manager.record(str(source_worktree_id))
                else:
                    worktree = manager.allocate(
                        task_id=task.id,
                        participant_id=agent.id,
                        attempt_id=current_attempts + 1,
                        base_commit=str(task.inputs.get("base_commit", "HEAD")),
                        dirty_base_required=bool(
                            task.inputs.get("requires_uncommitted_state", False)
                        ),
                    )
                execution_workspace = manager._validated_path(worktree)
                workspace.update_task(
                    task.id,
                    isolation_mode=(
                        IsolationMode.MANAGED_WORKTREE.value
                        if mode == IsolationMode.MANAGED_WORKTREE
                        else IsolationMode.READ_ONLY.value
                    ),
                    worktree_id=worktree["worktree_id"],
                    base_commit=worktree["base_commit"],
                    candidate_branch=worktree["branch"],
                )
            except WorktreeError as exc:
                if exc.code == "WORKTREE_UNAVAILABLE" and not task.inputs.get(
                    "parallel_write_required", False
                ):
                    manager = None
                    worktree = None
                    execution_workspace = workspace.project_root
                    mode = IsolationMode.NONE
                    workspace.update_task(
                        task.id,
                        isolation_mode=IsolationMode.NONE.value,
                        isolation_limitation="non_git_serial_execution",
                    )
                else:
                    workspace.update_task(
                        task.id,
                        status=TaskStatus.BLOCKED.value,
                        isolation_mode=mode.value,
                        error=f"{exc.code}: {exc}",
                        finished_at=utc_now(),
                    )
                    return
        else:
            workspace.update_task(task.id, isolation_mode=mode.value)

        if (
            self._execution_kind() != "mock"
            and execution_workspace != project_workspace
            and not self._workspace_preflight_allows(
                workspace,
                task,
                agent,
                execution_workspace,
                current_attempts=current_attempts,
            )
        ):
            return

        is_validation = bool(
            worktree
            and source_worktree_id
            and (
                "testing" in task.required_capabilities
                or bool(task.validation_commands)
                or bool(task.inputs.get("validation", False))
            )
        )
        serial_slot = (
            self._shared_writer_slot
            if mode == IsolationMode.NONE
            and "write_workspace" in task.required_permissions
            and provider_requires
            else _NullSemaphore()
        )
        if manager and worktree and is_validation:
            try:
                manager.begin_validation(str(worktree["worktree_id"]))
            except WorktreeError as exc:
                workspace.update_task(
                    task.id,
                    status=TaskStatus.BLOCKED.value,
                    error=f"{exc.code}: {exc}",
                    finished_at=utc_now(),
                )
                return

        with self._agent_slots[agent.id], serial_slot:
            state = workspace.manifest()["tasks"][task.id]
            max_attempt = max(
                task.retry_limit + 1,
                int(state.get("manual_attempt_limit", 0)),
            )
            for attempt in range(current_attempts + 1, max_attempt + 1):
                if workspace.manifest().get("cancel_requested"):
                    if manager and worktree:
                        try:
                            manager.retain(
                                str(worktree["worktree_id"]),
                                reason="operator cancellation before provider execution",
                            )
                        except WorktreeError:
                            pass
                    workspace.update_task(
                        task.id,
                        status=TaskStatus.CANCELLED.value,
                        error="operator cancellation",
                        finished_at=utc_now(),
                    )
                    return
                workspace.update_task(
                    task.id,
                    status=TaskStatus.RUNNING.value,
                    attempts=attempt,
                    agent_id=agent.id,
                    started_at=utc_now(),
                )
                writer_acquired = False
                if manager and worktree and mode == IsolationMode.MANAGED_WORKTREE and not is_validation:
                    try:
                        manager.acquire_writer(
                            str(worktree["worktree_id"]),
                            participant_id=agent.id,
                            attempt_id=attempt,
                        )
                        writer_acquired = True
                    except WorktreeError as exc:
                        final_result = ProviderResult(False, f"{exc.code}: {exc}")
                        break
                try:
                    try:
                        final_result = self.provider.execute(
                            task,
                            agent,
                            workspace.task_dir(task.id),
                            execution_workspace,
                        )
                    except Exception as exc:
                        final_result = ProviderResult(
                            False,
                            f"{type(exc).__name__}: {exc}",
                        )
                finally:
                    if writer_acquired and manager and worktree:
                        if final_result is None:
                            outcome = "failed"
                        elif final_result.cancelled:
                            outcome = "cancelled"
                        elif final_result.success:
                            outcome = "success"
                        elif attempt < max_attempt:
                            outcome = "retry"
                        else:
                            outcome = "failed"
                        manager.release_writer(
                            str(worktree["worktree_id"]),
                            participant_id=agent.id,
                            attempt_id=attempt,
                            outcome=outcome,
                        )
                attempt_usage.append(final_result.usage.to_dict())
                if final_result.success:
                    break
        assert final_result is not None
        provider_result = final_result
        validation: dict[str, Any] = {}
        if (
            final_result.success
            and manager
            and worktree
            and mode == IsolationMode.MANAGED_WORKTREE
            and not is_validation
            and task.validation_commands
        ):
            try:
                manager.begin_validation(str(worktree["worktree_id"]))
                validation = self._run_validation_commands(
                    task.validation_commands,
                    execution_workspace,
                    timeout_seconds=task.timeout_seconds,
                )
                manager.finish_validation(str(worktree["worktree_id"]), validation)
            except WorktreeError as exc:
                validation = {
                    "success": False,
                    "error": f"{exc.code}: {exc}",
                    "commands": [],
                }
            if not validation.get("success"):
                failed_command = next(
                    (
                        str(item.get("command"))
                        for item in validation.get("commands", ())
                        if isinstance(item, dict) and not item.get("success")
                    ),
                    "candidate validation",
                )
                final_result = replace(
                    final_result,
                    success=False,
                    summary=f"validation failed: {failed_command}",
                    outputs={**final_result.outputs, "validation": validation},
                )
        workspace.write_task_result(task.id, final_result.to_dict())
        usage = self._aggregate_usage(attempt_usage)
        workspace.update_task(task.id, usage=usage)
        if manager and worktree and (
            mode == IsolationMode.MANAGED_WORKTREE or is_validation
        ):
            validation = (
                {
                    "success": final_result.success,
                    "task_id": task.id,
                    "provider_summary": final_result.summary,
                }
                if is_validation
                else validation or dict(manager.record(str(worktree["worktree_id"])).get("validation", {}))
            )
            if is_validation:
                manager.finish_validation(str(worktree["worktree_id"]), validation)
            candidate = manager.candidate_result(
                str(worktree["worktree_id"]),
                provider_result={
                    "success": provider_result.success,
                    "cancelled": provider_result.cancelled,
                    "summary": provider_result.summary,
                },
                validation=validation,
            )
            candidate_ref = workspace.contained(
                "artifacts", "candidates", f"{worktree['worktree_id']}.json"
            )
            candidate_payload = candidate.to_dict()
            existing_candidate: dict[str, Any] = {}
            if is_validation and candidate_ref.is_file():
                existing_candidate = workspace.read_json(
                    str(candidate_ref.relative_to(workspace.path))
                )
                existing_provider = existing_candidate.get("provider_result")
                if isinstance(existing_provider, dict):
                    candidate_payload["provider_result"] = existing_provider
            writer_task_id = (
                str(source_task)
                if is_validation and isinstance(source_task, str)
                else task.id
            )
            candidate_payload["experience"] = {
                "experience_id": f"{workspace.run_id}:candidate:{worktree['worktree_id']}",
                "execution_kind": self._execution_kind(),
                "provider": agent.provider,
                "strategy": (
                    workspace.plan().routing_decision.mode.value
                    if workspace.plan().routing_decision is not None
                    else "unspecified"
                ),
                "isolation_mode": IsolationMode.MANAGED_WORKTREE.value,
                "worktree_id": worktree["worktree_id"],
                "base_commit": worktree["base_commit"],
                "writer_attempts": int(
                    workspace.manifest()["tasks"][writer_task_id].get("attempts", 0)
                ),
                "changed_files_count": len(candidate.changed_files),
                "validation": validation,
                "retained_after_run": manager.is_dirty(
                    manager.record(str(worktree["worktree_id"]))
                ),
            }
            atomic_write_json(candidate_ref, candidate_payload)
            workspace.update_task(
                task.id,
                candidate_result_ref=str(candidate_ref.relative_to(workspace.path)),
                changed_files_count=len(candidate.changed_files),
                retained_after_run=manager.is_dirty(manager.record(str(worktree["worktree_id"]))),
                validation=validation,
            )
        profile = workspace.plan().task_profile
        category = profile.task_type if profile is not None else task.role
        memory = AgentPerformanceMemory(workspace.performance_memory_path)
        try:
            memory.record(
                agent,
                task,
                final_result,
                usage,
                category,
                execution_kind=self._execution_kind(),
            )
            self.router.history_scores = memory.routing_scores(
                execution_kind=self._execution_kind()
            )
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
        if final_result.cancelled or final_result.termination.get("status") == "cancel_unverified":
            workspace.update_task(
                task.id,
                status=TaskStatus.CANCELLED.value,
                error=final_result.summary,
                finished_at=utc_now(),
                partial_result=final_result.partial_result,
            )
            return
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

    def _execution_kind(self) -> str:
        return str(getattr(self.provider, "execution_kind", "unknown"))

    def _workspace_preflight_allows(
        self,
        workspace: RunWorkspace,
        task: TaskSpec,
        agent: AgentSpec,
        execution_workspace: Path,
        *,
        current_attempts: int,
    ) -> bool:
        previous_code = workspace.manifest()["tasks"][task.id].get(
            "precondition_code"
        )
        preflight = self.workspace_preflight.check(
            agent, workspace, execution_workspace
        )
        preflight_ref = self.workspace_preflight.persist(workspace, task.id, preflight)
        workspace.update_task(
            task.id,
            agent_id=agent.id,
            workspace_compatible=preflight.compatible,
            workspace_preflight_ref=preflight_ref,
        )
        if preflight.provider_attempt_allowed:
            return True
        workspace.update_task(
            task.id,
            status=TaskStatus.BLOCKED.value,
            attempts=current_attempts,
            usage=self._aggregate_usage([]),
            precondition_code=preflight.error_code,
            error=f"{preflight.error_code}: {preflight.reason}",
            finished_at=utc_now(),
        )
        if (
            preflight.remediation == "user_action_required"
            and previous_code != preflight.error_code
        ):
            workspace.append_human_action(
                task.id,
                preflight.reason
                or "Codex workspace compatibility requires user action",
            )
        return False

    @staticmethod
    def _reset_workspace_preflight_blockers(workspace: RunWorkspace) -> None:
        def reset(manifest: dict[str, Any]) -> dict[str, Any]:
            reset_any = False
            for state in manifest["tasks"].values():
                if (
                    state.get("status") == TaskStatus.BLOCKED.value
                    and state.get("precondition_code")
                    and state.get("workspace_preflight_ref")
                ):
                    state.update(
                        {
                            "status": TaskStatus.PENDING.value,
                            "error": None,
                            "finished_at": None,
                            "workspace_compatible": None,
                            "preflight_rechecked_at": utc_now(),
                        }
                    )
                    reset_any = True
            if reset_any:
                manifest["status"] = "running"
                manifest.pop("finished_at", None)
            return manifest

        workspace.update_manifest(reset)

    @staticmethod
    def _run_validation_commands(
        commands: tuple[str, ...],
        project_root: Any,
        *,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        for command in commands:
            started = time.monotonic()
            try:
                argv = shlex.split(command)
                if not argv:
                    raise ValueError("validation command is empty")
                completed = subprocess.run(
                    argv,
                    cwd=project_root,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
                result = {
                    "command": command,
                    "success": completed.returncode == 0,
                    "exit_code": completed.returncode,
                    "stdout": completed.stdout[-40_000:],
                    "stderr": completed.stderr[-40_000:],
                    "latency_ms": round((time.monotonic() - started) * 1000),
                    "timed_out": False,
                }
            except subprocess.TimeoutExpired as exc:
                result = {
                    "command": command,
                    "success": False,
                    "exit_code": None,
                    "stdout": (exc.stdout or "")[-40_000:],
                    "stderr": (exc.stderr or "")[-40_000:],
                    "latency_ms": round((time.monotonic() - started) * 1000),
                    "timed_out": True,
                }
            except (OSError, ValueError) as exc:
                result = {
                    "command": command,
                    "success": False,
                    "exit_code": None,
                    "stdout": "",
                    "stderr": f"{type(exc).__name__}: {exc}",
                    "latency_ms": round((time.monotonic() - started) * 1000),
                    "timed_out": False,
                }
            results.append(result)
            if not result["success"]:
                break
        return {
            "success": len(results) == len(commands) and all(item["success"] for item in results),
            "commands": results,
        }

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
            if manifest.get("cancel_requested") or TaskStatus.CANCELLED.value in statuses:
                manifest["status"] = "cancelled"
            elif statuses <= {TaskStatus.COMPLETED.value}:
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


class _NullSemaphore:
    def __enter__(self) -> _NullSemaphore:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

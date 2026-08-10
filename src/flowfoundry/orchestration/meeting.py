"""Bounded, conflict-driven, durable AI meeting runtime."""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .approvals import ApprovalGate
from .evaluator import evaluate_review
from .execution import ProviderExecutionHandle
from .isolation import WorktreeError, WorktreeManager
from .mailbox import Mailbox
from .memory import AgentPerformanceMemory, MeetingExperienceLedger
from .models import (
    MeetingContribution,
    MeetingPlan,
    MeetingState,
    ProviderResult,
    ReviewDecision,
    TaskSpec,
    TaskStatus,
)
from .provider_setup import ProviderSetupFlow
from .providers import Provider
from .router import TaskRouter
from .workspace import RunWorkspace, atomic_write_json, stable_hash, utc_now


_TERMINAL_STATES = {
    MeetingState.COMPLETED,
    MeetingState.BLOCKED,
    MeetingState.FAILED,
    MeetingState.CANCELLED,
    MeetingState.CANCEL_UNVERIFIED,
    MeetingState.BUDGET_EXHAUSTED,
}

_TRANSITIONS: dict[MeetingState, set[MeetingState]] = {
    MeetingState.PLANNED: {MeetingState.CONTEXT_READY},
    MeetingState.CONTEXT_READY: {MeetingState.ROUND1_RUNNING},
    MeetingState.ROUND1_RUNNING: {MeetingState.ROUND1_COMPLETE},
    MeetingState.ROUND1_COMPLETE: {MeetingState.CONFLICT_CHECKED},
    MeetingState.CONFLICT_CHECKED: {MeetingState.ROUND2_RUNNING, MeetingState.CONVERGING},
    MeetingState.ROUND2_RUNNING: {MeetingState.ROUND2_COMPLETE},
    MeetingState.ROUND2_COMPLETE: {MeetingState.CONVERGING},
    MeetingState.CONVERGING: {MeetingState.VALIDATING, MeetingState.COMPLETED},
    MeetingState.VALIDATING: {MeetingState.COMPLETED, MeetingState.BLOCKED, MeetingState.FAILED},
}
for _state in tuple(_TRANSITIONS):
    _TRANSITIONS[_state].update(
        {
            MeetingState.BLOCKED,
            MeetingState.FAILED,
            MeetingState.CANCELLED,
            MeetingState.CANCEL_UNVERIFIED,
            MeetingState.BUDGET_EXHAUSTED,
        }
    )


class MeetingRuntime:
    """Run at most independent views, one targeted cross-review, and convergence."""

    def __init__(
        self,
        router: TaskRouter,
        provider: Provider,
        *,
        approval_gate: ApprovalGate | None = None,
    ) -> None:
        self.router = router
        self.provider = provider
        self.approval_gate = approval_gate or ApprovalGate()

    def run(self, workspace: RunWorkspace) -> dict[str, Any]:
        plan = workspace.plan()
        meeting_plan = plan.meeting_plan
        if meeting_plan is None:
            raise ValueError("task plan does not contain a meeting plan")

        performance = AgentPerformanceMemory(workspace.performance_memory_path)
        self.router.history_scores = performance.routing_scores(
            execution_kind=self._execution_kind()
        )
        tasks = {task.id: task for task in plan.tasks}

        while True:
            manifest = workspace.manifest()
            meeting = manifest["meeting"]
            state = MeetingState(meeting["state"])
            if state in _TERMINAL_STATES:
                return self._finalize(workspace)
            if meeting.get("cancel_requested") or manifest.get("cancel_requested"):
                self.transition(workspace, MeetingState.CANCELLED, reason="operator cancellation")
                continue
            reason = self._budget_reason(meeting_plan, meeting, before_agent_call=False)
            if reason:
                self._exhaust(workspace, reason)
                continue

            if state == MeetingState.PLANNED:
                self._prepare_context(workspace, meeting_plan)
            elif state == MeetingState.CONTEXT_READY:
                self.transition(workspace, MeetingState.ROUND1_RUNNING)
            elif state == MeetingState.ROUND1_RUNNING:
                self._run_round1(workspace, meeting_plan, tasks)
            elif state == MeetingState.ROUND1_COMPLETE:
                self._detect_conflicts(workspace, meeting_plan)
            elif state == MeetingState.CONFLICT_CHECKED:
                if workspace.manifest()["meeting"]["conflicts"]:
                    if not self._round_capacity(workspace, meeting_plan, "targeted_cross_review"):
                        continue
                    self.transition(workspace, MeetingState.ROUND2_RUNNING)
                else:
                    if not self._round_capacity(workspace, meeting_plan, "convergence"):
                        continue
                    self._mark_early_stop(workspace)
                    self.transition(workspace, MeetingState.CONVERGING)
            elif state == MeetingState.ROUND2_RUNNING:
                self._run_round2(workspace, meeting_plan, tasks)
            elif state == MeetingState.ROUND2_COMPLETE:
                if not self._round_capacity(workspace, meeting_plan, "convergence"):
                    continue
                self.transition(workspace, MeetingState.CONVERGING)
            elif state == MeetingState.CONVERGING:
                self._converge(workspace, meeting_plan, tasks)
            elif state == MeetingState.VALIDATING:
                self._validate(workspace, meeting_plan, tasks)

    def cancel(
        self,
        workspace: RunWorkspace,
        *,
        grace_period_seconds: float = 2.0,
    ) -> dict[str, Any]:
        current = workspace.manifest()
        meeting = current.get("meeting")
        if not isinstance(meeting, dict):
            return self._cancel_task_run(
                workspace,
                grace_period_seconds=grace_period_seconds,
            )
        state = MeetingState(meeting["state"])
        if state in _TERMINAL_STATES:
            return self._finalize(workspace)
        active = ProviderExecutionHandle.active_for_run(workspace.path)
        provider_starting = any(
            task.get("status") == TaskStatus.RUNNING.value
            for task in current["tasks"].values()
        )
        requested_at = utc_now()

        def request(manifest: dict[str, Any]) -> dict[str, Any]:
            meeting = manifest.get("meeting")
            if not isinstance(meeting, dict):
                raise ValueError("run does not contain a meeting")
            state = MeetingState(meeting["state"])
            if state in _TERMINAL_STATES:
                return manifest
            manifest["cancel_requested"] = True
            meeting["cancel_requested"] = True
            meeting["cancel_requested_at"] = meeting.get("cancel_requested_at") or requested_at
            meeting["cancellation"] = {
                "requested_at": meeting["cancel_requested_at"],
                "provider_running_at_cancel": bool(active) or provider_starting,
                "termination_status": "requested",
                "graceful_termination": False,
                "forced_termination": False,
                "partial_result": False,
                "executions": [],
            }
            return manifest

        workspace.update_manifest(request)
        if provider_starting and not active:
            startup_deadline = time.monotonic() + 0.5
            while time.monotonic() < startup_deadline and not active:
                active = ProviderExecutionHandle.active_for_run(workspace.path)
                if not active:
                    time.sleep(0.01)
        outcomes = ProviderExecutionHandle.cancel_active(
            workspace.path,
            grace_seconds=grace_period_seconds,
        )

        def record_outcomes(manifest: dict[str, Any]) -> dict[str, Any]:
            cancellation = manifest["meeting"].setdefault("cancellation", {})
            records = [outcome.to_dict() for outcome in outcomes]
            cancellation["executions"] = records
            cancellation["graceful_termination"] = any(
                outcome.graceful is True and not outcome.forced for outcome in outcomes
            )
            cancellation["forced_termination"] = any(outcome.forced for outcome in outcomes)
            cancellation["partial_result"] = any(outcome.partial_result for outcome in outcomes)
            if any(outcome.state == "cancel_unverified" for outcome in outcomes):
                cancellation["termination_status"] = "cancel_unverified"
            elif any(outcome.forced for outcome in outcomes):
                cancellation["termination_status"] = "forced"
            elif outcomes and all(outcome.action == "already_exited" for outcome in outcomes):
                cancellation["termination_status"] = "completion_race"
            elif outcomes:
                cancellation["termination_status"] = "graceful"
            else:
                cancellation["termination_status"] = "no_active_process"
            return manifest

        workspace.update_manifest(record_outcomes)
        if any(outcome.state == "cancel_unverified" for outcome in outcomes):
            self.transition(
                workspace,
                MeetingState.CANCEL_UNVERIFIED,
                reason="provider process identity could not be verified",
            )
            return self._finalize(workspace)
        if not active:
            self._mark_pending_tasks_cancelled(workspace)
            self.transition(workspace, MeetingState.CANCELLED, reason="operator cancellation")
            return self._finalize(workspace)

        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            manifest = workspace.manifest()
            if MeetingState(manifest["meeting"]["state"]) in _TERMINAL_STATES:
                return self._finalize(workspace)
            time.sleep(0.05)
        manifest = workspace.manifest()
        if MeetingState(manifest["meeting"]["state"]) not in _TERMINAL_STATES:
            self.transition(workspace, MeetingState.CANCELLED, reason="operator cancellation")
        return self._finalize(workspace)

    @staticmethod
    def _cancel_task_run(
        workspace: RunWorkspace,
        *,
        grace_period_seconds: float,
    ) -> dict[str, Any]:
        """Cancel an explicit DAG run and retain any managed candidate."""

        current = workspace.manifest()
        if current.get("status") == "cancelled" and current.get("cancel_requested"):
            return current
        active = ProviderExecutionHandle.active_for_run(workspace.path)
        provider_starting = any(
            task.get("status") == TaskStatus.RUNNING.value
            for task in current["tasks"].values()
        )
        requested_at = utc_now()

        def request(manifest: dict[str, Any]) -> dict[str, Any]:
            manifest["cancel_requested"] = True
            manifest["cancel_requested_at"] = manifest.get("cancel_requested_at") or requested_at
            manifest["cancellation"] = manifest.get("cancellation") or {
                "requested_at": manifest["cancel_requested_at"],
                "provider_running_at_cancel": bool(active) or provider_starting,
                "termination_status": "requested",
                "executions": [],
            }
            return manifest

        workspace.update_manifest(request)
        if provider_starting and not active:
            deadline = time.monotonic() + 0.5
            while time.monotonic() < deadline and not active:
                active = ProviderExecutionHandle.active_for_run(workspace.path)
                if not active:
                    time.sleep(0.01)
        outcomes = ProviderExecutionHandle.cancel_active(
            workspace.path,
            grace_seconds=grace_period_seconds,
        )
        retained: list[str] = []
        if any(workspace.contained("worktrees").glob("wt-*.json")):
            try:
                retained = [
                    str(record["worktree_id"])
                    for record in WorktreeManager(workspace).release_cancelled_leases()
                ]
            except WorktreeError:
                retained = []

        def finish(manifest: dict[str, Any]) -> dict[str, Any]:
            records = [outcome.to_dict() for outcome in outcomes]
            cancellation = manifest.setdefault("cancellation", {})
            cancellation["executions"] = records
            cancellation["graceful_termination"] = any(
                outcome.graceful is True and not outcome.forced for outcome in outcomes
            )
            cancellation["forced_termination"] = any(outcome.forced for outcome in outcomes)
            cancellation["partial_result"] = any(outcome.partial_result for outcome in outcomes)
            cancellation["retained_worktrees"] = sorted(set(retained))
            if any(outcome.state == "cancel_unverified" for outcome in outcomes):
                cancellation["termination_status"] = "cancel_unverified"
            elif any(outcome.forced for outcome in outcomes):
                cancellation["termination_status"] = "forced"
            elif outcomes:
                cancellation["termination_status"] = "graceful"
            else:
                cancellation["termination_status"] = "no_active_process"
            for task in manifest["tasks"].values():
                if task["status"] in {TaskStatus.PENDING.value, TaskStatus.RUNNING.value}:
                    task["status"] = TaskStatus.CANCELLED.value
                    task["error"] = "operator cancellation"
                    task["finished_at"] = utc_now()
            manifest["status"] = "cancelled"
            manifest["finished_at"] = utc_now()
            return manifest

        return workspace.update_manifest(finish)

    @staticmethod
    def _mark_pending_tasks_cancelled(workspace: RunWorkspace) -> None:
        def mark(manifest: dict[str, Any]) -> dict[str, Any]:
            finished_at = utc_now()
            for task_id, task in manifest["tasks"].items():
                if task["status"] == TaskStatus.PENDING.value:
                    task.update(
                        {
                            "status": TaskStatus.CANCELLED.value,
                            "error": "operator cancellation before provider start",
                            "finished_at": finished_at,
                        }
                    )
                    participant = manifest["meeting"].get("participants", {}).get(task_id)
                    if isinstance(participant, dict):
                        participant.update(
                            {
                                "status": TaskStatus.CANCELLED.value,
                                "finished_at": finished_at,
                            }
                        )
            return manifest

        workspace.update_manifest(mark)

    def transition(
        self,
        workspace: RunWorkspace,
        target: MeetingState,
        *,
        reason: str | None = None,
    ) -> dict[str, Any]:
        def apply(manifest: dict[str, Any]) -> dict[str, Any]:
            meeting = manifest["meeting"]
            current = MeetingState(meeting["state"])
            if target not in _TRANSITIONS.get(current, set()):
                raise ValueError(f"illegal meeting transition: {current.value} -> {target.value}")
            meeting["state"] = target.value
            meeting["state_updated_at"] = utc_now()
            if reason:
                meeting["terminal_reason"] = reason
            manifest["status"] = self._run_status_for(target)
            return manifest

        return workspace.update_manifest(apply)

    @staticmethod
    def _run_status_for(state: MeetingState) -> str:
        if state == MeetingState.COMPLETED:
            return "completed"
        if state == MeetingState.BLOCKED:
            return "completed_with_blockers"
        if state == MeetingState.FAILED:
            return "failed"
        if state == MeetingState.CANCELLED:
            return "cancelled"
        if state == MeetingState.CANCEL_UNVERIFIED:
            return "cancel_unverified"
        if state == MeetingState.BUDGET_EXHAUSTED:
            return "budget_exhausted"
        return "running"

    def _prepare_context(self, workspace: RunWorkspace, meeting_plan: MeetingPlan) -> None:
        manifest = workspace.manifest()
        existing = manifest["meeting"].get("context_pack_ref")
        if isinstance(existing, str) and workspace.contained(existing).is_file():
            self.transition(workspace, MeetingState.CONTEXT_READY)
            return

        plan = workspace.plan()
        relevant_files: list[str] = []
        constraints: list[str] = []
        previous_decisions: list[str] = []
        acceptance: list[str] = []
        for task in plan.tasks:
            for key, target in (
                ("relevant_files", relevant_files),
                ("artifact_refs", relevant_files),
                ("constraints", constraints),
                ("previous_decisions", previous_decisions),
            ):
                value = task.inputs.get(key)
                if isinstance(value, (list, tuple)):
                    target.extend(str(item) for item in value)
                elif isinstance(value, str):
                    target.append(value)
            acceptance.extend(str(item) for item in task.expected_outputs)
            acceptance.extend(str(item) for item in task.validation_commands)
        goal_limit = max(256, min(4_000, meeting_plan.context_char_limit // 3))
        context = {
            "schema_version": 1,
            "task_goal": self._bounded_text(plan.goal, goal_limit),
            "constraints": self._bounded_items(constraints, 40, 500),
            "workspace_ref": str(workspace.project_root),
            "relevant_artifact_refs": self._bounded_items(relevant_files, 60, 500),
            "previous_decisions": self._bounded_items(previous_decisions, 20, 500),
            "acceptance_criteria": self._bounded_items(acceptance, 80, 300),
            "requested_output_schema": {
                "position": "non-empty recommendation",
                "confidence": "0..1",
                "key_reasons": "list[str]",
                "risks": "list[str]",
                "assumptions": "list[str]",
                "blocking_concerns": "list[str]",
                "evidence_refs": "list[str]",
                "acceptance_constraints_met": "bool",
                "dissent": "bool",
            },
            "bounded": True,
            "char_limit": meeting_plan.context_char_limit,
        }
        serialized_limit = meeting_plan.context_char_limit - 200
        list_fields = (
            "relevant_artifact_refs",
            "constraints",
            "acceptance_criteria",
            "previous_decisions",
        )
        removed = False
        while len(json.dumps(context, ensure_ascii=False, indent=2)) > serialized_limit:
            populated = [field for field in list_fields if context[field]]
            if populated:
                largest = max(populated, key=lambda field: len(json.dumps(context[field])))
                context[largest].pop()
                removed = True
                continue
            goal = str(context["task_goal"])
            if len(goal) <= 256:
                break
            excess = len(json.dumps(context, ensure_ascii=False, indent=2)) - serialized_limit
            context["task_goal"] = self._bounded_text(goal, max(256, len(goal) - excess - 32))
            removed = True
        context["content_truncated"] = removed or "[truncated]" in str(context)
        context["context_hash"] = stable_hash(context)
        relative = "artifacts/meeting/context-pack.json"
        atomic_write_json(workspace.contained(relative), context)

        def persist(run_manifest: dict[str, Any]) -> dict[str, Any]:
            run_manifest["meeting"]["context_pack_ref"] = relative
            run_manifest["meeting"]["context_pack_hash"] = context["context_hash"]
            return run_manifest

        workspace.update_manifest(persist)
        self.transition(workspace, MeetingState.CONTEXT_READY)

    @staticmethod
    def _bounded_text(value: str, limit: int) -> str:
        return value if len(value) <= limit else value[:limit] + "...[truncated]"

    @classmethod
    def _bounded_items(cls, values: list[str], count: int, chars: int) -> list[str]:
        return [cls._bounded_text(value, chars) for value in values[:count]]

    def _run_round1(
        self,
        workspace: RunWorkspace,
        meeting_plan: MeetingPlan,
        tasks: dict[str, TaskSpec],
    ) -> None:
        for task_id in meeting_plan.participant_task_ids:
            meeting = workspace.manifest()["meeting"]
            if meeting["participants"][task_id]["status"] == TaskStatus.COMPLETED.value:
                continue
            if self._budget_reason(meeting_plan, meeting, before_agent_call=True):
                self._exhaust(
                    workspace,
                    self._budget_reason(meeting_plan, meeting, before_agent_call=True) or "budget",
                )
                return
            context_ref = str(meeting["context_pack_ref"])
            bounded_task = replace(
                tasks[task_id],
                dependencies=(),
                inputs={
                    **tasks[task_id].inputs,
                    "meeting_round": 1,
                    "context_pack_ref": str(workspace.contained(context_ref)),
                    "independent_view": True,
                },
                expected_outputs=("meeting_contribution",),
                required_permissions=("read_workspace",),
                validation_commands=(),
                review_required=False,
            )
            self._execute_round1_participant(workspace, bounded_task)
            state = MeetingState(workspace.manifest()["meeting"]["state"])
            if state in _TERMINAL_STATES:
                return

        meeting = workspace.manifest()["meeting"]
        completed = sum(
            participant["status"] == TaskStatus.COMPLETED.value
            for participant in meeting["participants"].values()
        )
        if completed < meeting_plan.minimum_participants:
            self.transition(
                workspace,
                MeetingState.BLOCKED,
                reason=(
                    f"only {completed} meeting participants completed; "
                    f"minimum is {meeting_plan.minimum_participants}"
                ),
            )
            return
        self._append_round(workspace, "independent_views")
        self.transition(workspace, MeetingState.ROUND1_COMPLETE)

    def _execute_round1_participant(self, workspace: RunWorkspace, task: TaskSpec) -> None:
        meeting_record = workspace.manifest()["meeting"]["participants"][task.id]
        attempted = set(str(item) for item in meeting_record.get("attempted_agents", ()))
        task_record = workspace.manifest()["tasks"][task.id]
        max_attempts = max(
            task.retry_limit + 2,
            int(task_record.get("manual_attempt_limit", 0)),
        )
        final_result: ProviderResult | None = None
        final_agent_id: str | None = None
        while int(workspace.manifest()["tasks"][task.id].get("attempts", 0)) < max_attempts:
            task_state = workspace.manifest()["tasks"][task.id]
            attempt = int(task_state.get("attempts", 0)) + 1
            exclusions = attempted if attempt > task.retry_limit + 1 else set()
            try:
                agent = self.router.route(task, excluded_agent_ids=exclusions)
            except LookupError as exc:
                ProviderSetupFlow(self.router.registry).record(workspace, task, str(exc))
                self._mark_participant_failure(workspace, task.id, str(exc), unavailable=True)
                return
            attempted.add(agent.id)
            call_id = f"round1-{task.id}-attempt-{attempt}"
            result = self._provider_call(
                workspace,
                task,
                agent.id,
                call_id,
                workspace.task_dir(task.id),
                phase="round1",
            )
            if result is None:
                return
            final_result = result
            final_agent_id = agent.id
            if result.success:
                break
        if final_result is None or final_agent_id is None:
            self._mark_participant_failure(workspace, task.id, "participant produced no result")
            return
        if not final_result.success:
            self._finish_task_failure(workspace, task.id, final_result.summary)
            self._mark_participant_failure(workspace, task.id, final_result.summary)
            return

        contribution = final_result.contribution or MeetingContribution(
            position=f"undetermined:{task.id}",
            confidence=0.0,
            blocking_concerns=("structured contribution unavailable",),
            acceptance_constraints_met=False,
            dissent=True,
        )
        workspace.write_task_result(task.id, final_result.to_dict())
        usage = self._task_usage(workspace, f"round1-{task.id}-")
        workspace.update_task(task.id, usage=usage, agent_id=final_agent_id)
        self._record_performance(workspace, task, final_agent_id, final_result, usage)
        Mailbox(workspace).send(
            sender=final_agent_id,
            recipient="aggregator",
            task_id=task.id,
            kind="meeting_round1_contribution",
            payload=final_result.to_dict(),
        )

        def complete(manifest: dict[str, Any]) -> dict[str, Any]:
            participant = manifest["meeting"]["participants"][task.id]
            participant.update(
                {
                    "status": TaskStatus.COMPLETED.value,
                    "agent_id": final_agent_id,
                    "contribution": contribution.to_dict(),
                    "finished_at": utc_now(),
                }
            )
            return manifest

        workspace.update_manifest(complete)
        self._apply_task_result_status(workspace, task, final_result)

    def _provider_call(
        self,
        workspace: RunWorkspace,
        task: TaskSpec,
        agent_id: str,
        call_id: str,
        task_dir: Path,
        *,
        phase: str,
    ) -> ProviderResult | None:
        receipt_ref = f"artifacts/meeting/calls/{call_id}.json"
        receipt_path = workspace.contained(receipt_ref)
        manifest = workspace.manifest()
        if (
            not receipt_path.is_file()
            and (manifest.get("cancel_requested") or manifest["meeting"].get("cancel_requested"))
        ):
            state = MeetingState(manifest["meeting"]["state"])
            if state not in _TERMINAL_STATES:
                self.transition(
                    workspace,
                    MeetingState.CANCELLED,
                    reason="operator cancellation",
                )
            self._finalize(workspace)
            return None
        attempt = int(call_id.rsplit("-", 1)[-1])
        if phase in {"round1", "validation"}:
            workspace.update_task(
                task.id,
                status=TaskStatus.RUNNING.value,
                attempts=attempt,
                agent_id=agent_id,
                started_at=utc_now(),
            )
        if receipt_path.is_file():
            result = ProviderResult.from_dict(workspace.read_json(receipt_ref)["result"])
        else:
            meeting_plan = workspace.plan().meeting_plan
            assert meeting_plan is not None
            reason = self._budget_reason(
                meeting_plan,
                workspace.manifest()["meeting"],
                before_agent_call=True,
            )
            if reason:
                self._exhaust(workspace, reason)
                return None
            agent = self.router.registry.get(agent_id)
            active_plan = workspace.plan().meeting_plan
            assert active_plan is not None
            remaining_seconds = self._remaining_wall_seconds(
                active_plan,
                workspace.manifest()["meeting"],
            )
            task = replace(task, timeout_seconds=max(1, min(task.timeout_seconds, int(remaining_seconds))))
            try:
                result = self.provider.execute(task, agent, task_dir, workspace.project_root)
            except Exception as exc:  # provider boundary; KeyboardInterrupt still enables crash tests
                result = ProviderResult(False, f"{type(exc).__name__}: {exc}")
            atomic_write_json(
                receipt_path,
                {
                    "schema_version": 1,
                    "call_id": call_id,
                    "phase": phase,
                    "task_id": task.id,
                    "agent_id": agent_id,
                    "result": result.to_dict(),
                    "created_at": utc_now(),
                },
            )
        self._account_call(workspace, call_id, task.id, agent_id, phase, result)
        termination_status = result.termination.get("status")
        if result.cancelled or termination_status == "cancel_unverified":
            target = (
                MeetingState.CANCEL_UNVERIFIED
                if termination_status == "cancel_unverified"
                else MeetingState.CANCELLED
            )
            self._record_cancelled_call(
                workspace,
                task,
                agent_id,
                result,
                target=target,
            )
            return None
        active_plan = workspace.plan().meeting_plan
        assert active_plan is not None
        reason = self._budget_reason(
            active_plan,
            workspace.manifest()["meeting"],
            before_agent_call=False,
        )
        if reason:
            self._exhaust(workspace, reason)
        return result

    def _record_cancelled_call(
        self,
        workspace: RunWorkspace,
        task: TaskSpec,
        agent_id: str,
        result: ProviderResult,
        *,
        target: MeetingState,
    ) -> None:
        workspace.write_task_result(task.id, result.to_dict())
        workspace.update_task(
            task.id,
            status=TaskStatus.CANCELLED.value,
            agent_id=agent_id,
            usage={"provider_calls": 1, **result.usage.to_dict()},
            error=result.summary,
            finished_at=utc_now(),
            partial_result=result.partial_result,
        )

        def record(manifest: dict[str, Any]) -> dict[str, Any]:
            meeting = manifest["meeting"]
            participant = meeting.get("participants", {}).get(task.id)
            if isinstance(participant, dict):
                participant.update(
                    {
                        "status": TaskStatus.CANCELLED.value,
                        "agent_id": agent_id,
                        "finished_at": utc_now(),
                        "partial_result": result.partial_result,
                    }
                )
            cancellation = meeting.setdefault(
                "cancellation",
                {
                    "requested_at": meeting.get("cancel_requested_at"),
                    "provider_running_at_cancel": True,
                    "executions": [],
                },
            )
            termination = result.termination
            cancellation["partial_result"] = bool(result.partial_result)
            cancellation["graceful_termination"] = bool(termination.get("graceful", False))
            cancellation["forced_termination"] = bool(termination.get("forced", False))
            if target == MeetingState.CANCEL_UNVERIFIED:
                cancellation["termination_status"] = "cancel_unverified"
            elif termination.get("forced"):
                cancellation["termination_status"] = "forced"
            elif termination.get("graceful"):
                cancellation["termination_status"] = "graceful"
            else:
                cancellation["termination_status"] = str(
                    termination.get("status", target.value)
                )
            return manifest

        workspace.update_manifest(record)
        state = MeetingState(workspace.manifest()["meeting"]["state"])
        if state not in _TERMINAL_STATES:
            self.transition(workspace, target, reason="operator cancellation")
        self._finalize(workspace)

    def _account_call(
        self,
        workspace: RunWorkspace,
        call_id: str,
        task_id: str,
        agent_id: str,
        phase: str,
        result: ProviderResult,
    ) -> None:
        usage = result.usage

        def account(manifest: dict[str, Any]) -> dict[str, Any]:
            meeting = manifest["meeting"]
            consumed = meeting["budget_consumed"]
            if call_id in consumed["accounted_call_ids"]:
                return manifest
            consumed["accounted_call_ids"].append(call_id)
            consumed["agent_calls"] += 1
            if usage.input_tokens is None or usage.output_tokens is None:
                consumed["token_measurement_complete"] = False
            else:
                consumed["known_input_tokens"] += usage.input_tokens
                consumed["known_output_tokens"] += usage.output_tokens
                consumed["known_total_tokens"] += usage.input_tokens + usage.output_tokens
            if usage.estimated_cost_usd is None:
                consumed["cost_measurement_complete"] = False
            else:
                consumed["known_cost_usd"] += usage.estimated_cost_usd
            if usage.latency_ms is None:
                consumed["latency_measurement_complete"] = False
            else:
                consumed["known_latency_ms"] += usage.latency_ms
            if phase == "round1":
                participant = meeting["participants"][task_id]
                participant["call_ids"].append(call_id)
                if agent_id not in participant["attempted_agents"]:
                    participant["attempted_agents"].append(agent_id)
            meeting["last_call_at"] = utc_now()
            return manifest

        workspace.update_manifest(account)

    def _task_usage(self, workspace: RunWorkspace, call_prefix: str) -> dict[str, Any]:
        usages: list[dict[str, Any]] = []
        for path in sorted(workspace.contained("artifacts", "meeting", "calls").glob(f"{call_prefix}*.json")):
            record = workspace.read_json(str(path.relative_to(workspace.path)))
            result = record.get("result")
            if isinstance(result, dict) and isinstance(result.get("usage"), dict):
                usages.append(result["usage"])
        return self._aggregate_usage(usages)

    @staticmethod
    def _aggregate_usage(usages: list[dict[str, Any]]) -> dict[str, Any]:
        def total(field: str) -> int | float | None:
            values = [usage[field] for usage in usages if usage.get(field) is not None]
            return sum(values) if len(values) == len(usages) and values else None

        token_complete = bool(usages) and all(
            usage.get("input_tokens") is not None and usage.get("output_tokens") is not None
            for usage in usages
        )
        cost_complete = bool(usages) and all(usage.get("estimated_cost_usd") is not None for usage in usages)
        return {
            "provider_calls": len(usages),
            "input_tokens": total("input_tokens"),
            "output_tokens": total("output_tokens"),
            "latency_ms": total("latency_ms"),
            "estimated_cost_usd": total("estimated_cost_usd"),
            "token_status": "measured" if token_complete else "unavailable",
            "cost_status": "measured" if cost_complete else "unavailable",
        }

    def _record_performance(
        self,
        workspace: RunWorkspace,
        task: TaskSpec,
        agent_id: str,
        result: ProviderResult,
        usage: dict[str, Any],
    ) -> None:
        memory = AgentPerformanceMemory(workspace.performance_memory_path)
        profile = workspace.plan().task_profile
        category = profile.task_type if profile is not None else task.role
        try:
            memory.record(
                self.router.registry.get(agent_id),
                task,
                result,
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

    def _apply_task_result_status(
        self,
        workspace: RunWorkspace,
        task: TaskSpec,
        result: ProviderResult,
    ) -> None:
        if task.role != "reviewer":
            workspace.update_task(
                task.id,
                status=TaskStatus.COMPLETED.value,
                finished_at=utc_now(),
                error=None,
            )
            return
        record = evaluate_review(task.id, result)
        atomic_write_json(workspace.contained("reviews", f"{task.id}.json"), record.to_dict())
        source_task = task.inputs.get("source_task")
        if record.decision in {ReviewDecision.APPROVED, ReviewDecision.APPROVED_WITH_NOTES}:
            status = TaskStatus.COMPLETED
        elif record.decision == ReviewDecision.BLOCKED:
            status = TaskStatus.BLOCKED
            if isinstance(source_task, str):
                workspace.update_task(source_task, status=TaskStatus.BLOCKED.value, reviewed_at=utc_now())
        else:
            status = TaskStatus.REVIEW_REQUIRED
            if isinstance(source_task, str):
                workspace.update_task(
                    source_task,
                    status=TaskStatus.REVIEW_REQUIRED.value,
                    reviewed_at=utc_now(),
                )
        workspace.update_task(task.id, status=status.value, finished_at=utc_now(), error=None)

    def _mark_participant_failure(
        self,
        workspace: RunWorkspace,
        task_id: str,
        reason: str,
        *,
        unavailable: bool = False,
    ) -> None:
        def apply(manifest: dict[str, Any]) -> dict[str, Any]:
            participant = manifest["meeting"]["participants"][task_id]
            participant.update(
                {
                    "status": TaskStatus.BLOCKED.value if unavailable else TaskStatus.FAILED.value,
                    "error": reason,
                    "finished_at": utc_now(),
                }
            )
            manifest["tasks"][task_id].update(
                {
                    "status": TaskStatus.BLOCKED.value if unavailable else TaskStatus.FAILED.value,
                    "error": reason,
                    "finished_at": utc_now(),
                }
            )
            return manifest

        workspace.update_manifest(apply)

    @staticmethod
    def _finish_task_failure(workspace: RunWorkspace, task_id: str, reason: str) -> None:
        workspace.update_task(
            task_id,
            status=TaskStatus.FAILED.value,
            error=reason,
            finished_at=utc_now(),
        )

    def _detect_conflicts(self, workspace: RunWorkspace, meeting_plan: MeetingPlan) -> None:
        participants = workspace.manifest()["meeting"]["participants"]
        completed = {
            task_id: MeetingContribution.from_dict(record["contribution"])
            for task_id, record in participants.items()
            if record["status"] == TaskStatus.COMPLETED.value
            and isinstance(record.get("contribution"), dict)
        }
        positions = {task_id: self._normalize(view.position) for task_id, view in completed.items()}
        reasons: list[str] = []
        if len(set(positions.values())) > 1:
            reasons.append("incompatible_positions")
        if any(view.blocking_concerns for view in completed.values()):
            reasons.append("blocking_objection")
        if any(view.dissent or view.remaining_dissent for view in completed.values()):
            reasons.append("explicit_dissent")
        if any(not view.acceptance_constraints_met for view in completed.values()):
            reasons.append("acceptance_constraint_gap")
        low_confidence = [
            task_id
            for task_id, view in completed.items()
            if view.confidence < meeting_plan.confidence_threshold
        ]
        if low_confidence:
            reasons.append("confidence_below_threshold")

        conflicts: list[dict[str, Any]] = []
        if reasons:
            targeted: list[str] = []
            if len(set(positions.values())) > 1:
                for position in dict.fromkeys(positions.values()):
                    candidates = [
                        task_id for task_id, normalized in positions.items() if normalized == position
                    ]
                    representative = max(candidates, key=lambda task_id: completed[task_id].confidence)
                    targeted.append(representative)
            for task_id, view in completed.items():
                if (
                    view.blocking_concerns
                    or view.dissent
                    or view.remaining_dissent
                    or not view.acceptance_constraints_met
                    or view.confidence < meeting_plan.confidence_threshold
                ) and task_id not in targeted:
                    targeted.append(task_id)
            if len(targeted) == 1 and len(completed) > 1:
                counterpart = max(
                    (task_id for task_id in completed if task_id not in targeted),
                    key=lambda task_id: completed[task_id].confidence,
                )
                targeted.append(counterpart)
            conflict = {
                "conflict_id": "conflict-001",
                "disputed_decision": workspace.plan().goal,
                "reasons": sorted(set(reasons)),
                "participant_positions": {
                    task_id: {
                        "position": self._bounded_text(view.position, 1_000),
                        "confidence": view.confidence,
                        "blocking_concerns": self._bounded_items(
                            list(view.blocking_concerns), 5, 300
                        ),
                        "evidence_refs": self._bounded_items(list(view.evidence_refs), 10, 300),
                    }
                    for task_id, view in completed.items()
                },
                "target_participants": targeted,
                "required_resolution": "defend, revise, reject, or combine the disputed decision",
                "resolved": False,
            }
            conflicts.append(conflict)

        def persist(manifest: dict[str, Any]) -> dict[str, Any]:
            manifest["meeting"]["conflicts"] = conflicts
            manifest["meeting"]["conflicts_detected"] = len(conflicts)
            return manifest

        workspace.update_manifest(persist)
        self.transition(workspace, MeetingState.CONFLICT_CHECKED)

    def _run_round2(
        self,
        workspace: RunWorkspace,
        meeting_plan: MeetingPlan,
        tasks: dict[str, TaskSpec],
    ) -> None:
        meeting = workspace.manifest()["meeting"]
        for conflict in meeting["conflicts"]:
            conflict_id = str(conflict["conflict_id"])
            pack_ref = self._write_conflict_pack(workspace, conflict)
            for task_id in conflict["target_participants"]:
                key = f"{conflict_id}:{task_id}"
                current = workspace.manifest()["meeting"]["cross_reviews"].get(key, {})
                if current.get("status") == TaskStatus.COMPLETED.value:
                    continue
                task = replace(
                    tasks[task_id],
                    id=f"cross-{conflict_id}-{task_id}",
                    title=f"Resolve {conflict_id}",
                    dependencies=(),
                    inputs={
                        "meeting_round": 2,
                        "source_participant": task_id,
                        "conflict_id": conflict_id,
                        "conflict_pack_ref": str(workspace.contained(pack_ref)),
                    },
                    expected_outputs=("cross_review_contribution",),
                    required_permissions=("read_workspace",),
                    validation_commands=(),
                    retry_limit=0,
                    review_required=False,
                )
                self._execute_cross_review(workspace, task, key, task_id)
                if MeetingState(workspace.manifest()["meeting"]["state"]) in _TERMINAL_STATES:
                    return
            self._resolve_conflict(workspace, conflict_id)
        self._append_round(workspace, "targeted_cross_review")
        self.transition(workspace, MeetingState.ROUND2_COMPLETE)

    def _write_conflict_pack(self, workspace: RunWorkspace, conflict: dict[str, Any]) -> str:
        conflict_id = str(conflict["conflict_id"])
        relative = f"artifacts/meeting/conflicts/{conflict_id}.json"
        path = workspace.contained(relative)
        if not path.is_file():
            atomic_write_json(
                path,
                {
                    "schema_version": 1,
                    "conflict_id": conflict_id,
                    "disputed_decision": conflict["disputed_decision"],
                    "positions": conflict["participant_positions"],
                    "relevant_evidence_refs": sorted(
                        {
                            ref
                            for position in conflict["participant_positions"].values()
                            for ref in position.get("evidence_refs", ())
                        }
                    ),
                    "required_resolution": conflict["required_resolution"],
                    "bounded": True,
                },
            )
        return relative

    def _execute_cross_review(
        self,
        workspace: RunWorkspace,
        task: TaskSpec,
        key: str,
        source_task_id: str,
    ) -> None:
        attempted: set[str] = set()
        final_result: ProviderResult | None = None
        final_agent_id: str | None = None
        for attempt in (1, 2):
            try:
                agent = self.router.route(task, excluded_agent_ids=attempted)
            except LookupError:
                break
            attempted.add(agent.id)
            call_id = f"round2-{task.id}-attempt-{attempt}"
            task_dir = workspace.contained("artifacts", "meeting", "round2", task.id)
            task_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            result = self._provider_call(
                workspace,
                task,
                agent.id,
                call_id,
                task_dir,
                phase="round2",
            )
            if result is None:
                return
            final_result = result
            final_agent_id = agent.id
            if result.success:
                break
        contribution = final_result.contribution if final_result and final_result.success else None

        def persist(manifest: dict[str, Any]) -> dict[str, Any]:
            manifest["meeting"]["cross_reviews"][key] = {
                "status": (
                    TaskStatus.COMPLETED.value if contribution is not None else TaskStatus.FAILED.value
                ),
                "source_participant": source_task_id,
                "agent_id": final_agent_id,
                "contribution": contribution.to_dict() if contribution else None,
                "error": None if contribution else (final_result.summary if final_result else "no fallback"),
                "finished_at": utc_now(),
            }
            return manifest

        workspace.update_manifest(persist)

    def _resolve_conflict(self, workspace: RunWorkspace, conflict_id: str) -> None:
        meeting = workspace.manifest()["meeting"]
        conflict = next(item for item in meeting["conflicts"] if item["conflict_id"] == conflict_id)
        final_positions: dict[str, str] = {}
        blockers = False
        for task_id in conflict["participant_positions"]:
            key = f"{conflict_id}:{task_id}"
            review = meeting["cross_reviews"].get(key, {})
            raw = review.get("contribution")
            if isinstance(raw, dict):
                view = MeetingContribution.from_dict(raw)
            else:
                original = meeting["participants"][task_id]["contribution"]
                view = MeetingContribution.from_dict(original)
            final_positions[task_id] = view.position
            blockers = blockers or bool(view.blocking_concerns) or view.remaining_dissent
        resolved = len({self._normalize(value) for value in final_positions.values()}) == 1 and not blockers

        def persist(manifest: dict[str, Any]) -> dict[str, Any]:
            active = next(
                item for item in manifest["meeting"]["conflicts"] if item["conflict_id"] == conflict_id
            )
            active["resolved"] = resolved
            active["final_positions"] = final_positions
            return manifest

        workspace.update_manifest(persist)

    def _converge(
        self,
        workspace: RunWorkspace,
        meeting_plan: MeetingPlan,
        tasks: dict[str, TaskSpec],
    ) -> None:
        meeting = workspace.manifest()["meeting"]
        views: dict[str, MeetingContribution] = {}
        for task_id, participant in meeting["participants"].items():
            raw = participant.get("contribution")
            if isinstance(raw, dict):
                views[task_id] = MeetingContribution.from_dict(raw)
        for key, review in meeting["cross_reviews"].items():
            raw = review.get("contribution")
            source = review.get("source_participant")
            if isinstance(raw, dict) and isinstance(source, str):
                views[source] = MeetingContribution.from_dict(raw)
        if not views:
            self.transition(workspace, MeetingState.BLOCKED, reason="no usable meeting contributions")
            return

        normalized = {task_id: self._normalize(view.position) for task_id, view in views.items()}
        counts = Counter(normalized.values())
        confidence = {
            position: sum(view.confidence for task_id, view in views.items() if normalized[task_id] == position)
            for position in counts
        }
        winning = max(counts, key=lambda position: (counts[position], confidence[position], position))
        winner_ids = [task_id for task_id in meeting_plan.participant_task_ids if normalized.get(task_id) == winning]
        decision = views[winner_ids[0]].position if winner_ids else winning
        dissent: list[dict[str, Any]] = []
        for task_id, view in views.items():
            if normalized[task_id] != winning or view.blocking_concerns or view.remaining_dissent:
                dissent.append(
                    {
                        "participant": task_id,
                        "position": view.position,
                        "confidence": view.confidence,
                        "blocking_concerns": list(view.blocking_concerns),
                        "reasons": list(view.key_reasons),
                    }
                )
        for task_id, participant in meeting["participants"].items():
            if participant["status"] != TaskStatus.COMPLETED.value:
                dissent.append(
                    {
                        "participant": task_id,
                        "position": "unavailable",
                        "confidence": 0.0,
                        "blocking_concerns": [participant.get("error", "participant unavailable")],
                        "reasons": [],
                    }
                )
        rationale = list(
            dict.fromkeys(reason for task_id in winner_ids for reason in views[task_id].key_reasons)
        )
        evidence = sorted(
            {ref for task_id in winner_ids for ref in views[task_id].evidence_refs}
        )
        requirements = sorted(
            {
                item
                for task_id in meeting_plan.validation_task_ids
                for item in (*tasks[task_id].validation_commands, *tasks[task_id].expected_outputs)
            }
        )
        result = {
            "schema_version": 1,
            "decision": decision,
            "rationale": rationale,
            "evidence_refs": evidence,
            "unresolved_dissent": dissent,
            "confidence": round(
                sum(views[task_id].confidence for task_id in winner_ids) / max(1, len(winner_ids)),
                3,
            ),
            "recommended_next_action": "execute the decision within the declared constraints",
            "validation_requirements": requirements,
            "validation": "pending" if meeting_plan.validation_task_ids else "not_required",
            "degraded": bool(dissent),
            "created_at": utc_now(),
        }
        relative = "final/meeting-result.json"
        atomic_write_json(workspace.contained(relative), result)

        def persist(manifest: dict[str, Any]) -> dict[str, Any]:
            manifest["meeting"]["result_ref"] = relative
            manifest["meeting"]["dissent"] = dissent
            return manifest

        workspace.update_manifest(persist)
        self._append_round(workspace, "convergence")
        if meeting_plan.validation_task_ids:
            self.transition(workspace, MeetingState.VALIDATING)
        else:
            self.transition(workspace, MeetingState.COMPLETED)

    def _validate(
        self,
        workspace: RunWorkspace,
        meeting_plan: MeetingPlan,
        tasks: dict[str, TaskSpec],
    ) -> None:
        blocked = False
        failed = False
        for task_id in meeting_plan.validation_task_ids:
            state = workspace.manifest()["tasks"][task_id]
            if state["status"] == TaskStatus.COMPLETED.value:
                continue
            task = tasks[task_id]
            dependency_states = workspace.manifest()["tasks"]
            failed_dependencies = [
                dependency
                for dependency in task.dependencies
                if dependency_states[dependency]["status"]
                in {
                    TaskStatus.BLOCKED.value,
                    TaskStatus.FAILED.value,
                    TaskStatus.SKIPPED.value,
                    TaskStatus.SKIPPED_PENDING_HUMAN.value,
                }
            ]
            pending_dependencies = [
                dependency
                for dependency in task.dependencies
                if dependency_states[dependency]["status"]
                in {TaskStatus.PENDING.value, TaskStatus.REVIEW_REQUIRED.value}
            ]
            if failed_dependencies:
                workspace.update_task(
                    task_id,
                    status=TaskStatus.SKIPPED.value,
                    error=f"dependency did not complete: {', '.join(failed_dependencies)}",
                    finished_at=utc_now(),
                )
                blocked = True
                continue
            if pending_dependencies:
                blocked = True
                continue
            bounded_task = replace(
                task,
                dependencies=(),
                inputs={
                    "meeting_result_ref": str(workspace.contained("final", "meeting-result.json")),
                    "context_pack_ref": str(
                        workspace.contained(workspace.manifest()["meeting"]["context_pack_ref"])
                    ),
                },
            )
            result = self._execute_validation_task(workspace, bounded_task)
            if result is None:
                return
            failed = failed or not result.success

        result_path = workspace.contained("final", "meeting-result.json")
        result_record = workspace.read_json("final/meeting-result.json")
        result_record["validation"] = "failed" if failed else ("blocked" if blocked else "passed")
        atomic_write_json(result_path, result_record)
        if failed:
            self.transition(workspace, MeetingState.FAILED, reason="meeting validation failed")
        elif blocked:
            self.transition(workspace, MeetingState.BLOCKED, reason="meeting validation was blocked")
        else:
            self.transition(workspace, MeetingState.COMPLETED)

    def _execute_validation_task(
        self,
        workspace: RunWorkspace,
        task: TaskSpec,
    ) -> ProviderResult | None:
        attempted: set[str] = set()
        final_result: ProviderResult | None = None
        final_agent_id: str | None = None
        task_record = workspace.manifest()["tasks"][task.id]
        max_attempts = max(
            task.retry_limit + 2,
            int(task_record.get("manual_attempt_limit", 0)),
        )
        while int(workspace.manifest()["tasks"][task.id].get("attempts", 0)) < max_attempts:
            attempt = int(workspace.manifest()["tasks"][task.id].get("attempts", 0)) + 1
            exclusions = attempted if attempt > task.retry_limit + 1 else set()
            try:
                agent = self.router.route(task, excluded_agent_ids=exclusions)
            except LookupError as exc:
                ProviderSetupFlow(self.router.registry).record(workspace, task, str(exc))
                self._finish_task_failure(workspace, task.id, str(exc))
                return ProviderResult(False, str(exc))
            attempted.add(agent.id)
            result = self._provider_call(
                workspace,
                task,
                agent.id,
                f"validation-{task.id}-attempt-{attempt}",
                workspace.task_dir(task.id),
                phase="validation",
            )
            if result is None:
                return None
            final_result = result
            final_agent_id = agent.id
            if result.success:
                break
        assert final_result is not None and final_agent_id is not None
        workspace.write_task_result(task.id, final_result.to_dict())
        usage = self._task_usage(workspace, f"validation-{task.id}-")
        workspace.update_task(task.id, usage=usage, agent_id=final_agent_id)
        self._record_performance(workspace, task, final_agent_id, final_result, usage)
        Mailbox(workspace).send(
            sender=final_agent_id,
            recipient="aggregator",
            task_id=task.id,
            kind="meeting_validation_result",
            payload=final_result.to_dict(),
        )
        if final_result.success:
            workspace.update_task(
                task.id,
                status=TaskStatus.COMPLETED.value,
                finished_at=utc_now(),
                error=None,
            )
        else:
            self._finish_task_failure(workspace, task.id, final_result.summary)
        return final_result

    def _budget_reason(
        self,
        meeting_plan: MeetingPlan,
        meeting: dict[str, Any],
        *,
        before_agent_call: bool,
    ) -> str | None:
        budget = meeting_plan.budget
        consumed = meeting["budget_consumed"]
        if before_agent_call and consumed["agent_calls"] >= budget.max_agent_calls:
            return "agent_call_budget"
        if (
            budget.max_total_tokens is not None
            and consumed["known_total_tokens"] >= budget.max_total_tokens
        ):
            return "token_budget"
        if (
            budget.max_cost_usd is not None
            and consumed["known_cost_usd"] >= budget.max_cost_usd
        ):
            return "cost_budget"
        started = datetime.fromisoformat(str(meeting["started_at"]))
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        if elapsed >= budget.max_wall_time_seconds:
            return "wall_time_budget"
        return None

    @staticmethod
    def _remaining_wall_seconds(meeting_plan: MeetingPlan, meeting: dict[str, Any]) -> float:
        started = datetime.fromisoformat(str(meeting["started_at"]))
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        return max(0.0, meeting_plan.budget.max_wall_time_seconds - elapsed)

    def _round_capacity(
        self,
        workspace: RunWorkspace,
        meeting_plan: MeetingPlan,
        next_round: str,
    ) -> bool:
        rounds = workspace.manifest()["meeting"]["rounds_executed"]
        if len(rounds) >= meeting_plan.budget.max_rounds:
            self._exhaust(workspace, f"round_budget_before_{next_round}")
            return False
        return True

    def _exhaust(self, workspace: RunWorkspace, reason: str) -> None:
        state = MeetingState(workspace.manifest()["meeting"]["state"])
        if state in _TERMINAL_STATES:
            return

        def persist(manifest: dict[str, Any]) -> dict[str, Any]:
            manifest["meeting"]["budget_status"] = "exhausted"
            manifest["meeting"]["budget_exhaustion_reason"] = reason
            return manifest

        workspace.update_manifest(persist)
        self.transition(workspace, MeetingState.BUDGET_EXHAUSTED, reason=reason)

    @staticmethod
    def _append_round(workspace: RunWorkspace, name: str) -> None:
        def append(manifest: dict[str, Any]) -> dict[str, Any]:
            rounds = manifest["meeting"]["rounds_executed"]
            if name not in rounds:
                rounds.append(name)
            return manifest

        workspace.update_manifest(append)

    @staticmethod
    def _mark_early_stop(workspace: RunWorkspace) -> None:
        def mark(manifest: dict[str, Any]) -> dict[str, Any]:
            meeting = manifest["meeting"]
            meeting["early_stopped"] = True
            meeting["early_stop_reason"] = (
                "round 1 positions agree, no blocking conflict exists, confidence and acceptance thresholds passed"
            )
            return manifest

        workspace.update_manifest(mark)

    @staticmethod
    def _normalize(position: str) -> str:
        return " ".join(position.casefold().split())

    def _finalize(self, workspace: RunWorkspace) -> dict[str, Any]:
        manifest = workspace.manifest()
        meeting = manifest["meeting"]
        experience_ref = meeting.get("experience_ref")
        if (
            isinstance(experience_ref, str)
            and isinstance(meeting.get("usage"), dict)
            and workspace.contained(experience_ref).is_file()
        ):
            return manifest
        state = MeetingState(meeting["state"])
        task_statuses = {item["status"] for item in manifest["tasks"].values()}
        if state == MeetingState.COMPLETED:
            if task_statuses <= {TaskStatus.COMPLETED.value}:
                run_status = "completed"
            elif TaskStatus.REVIEW_REQUIRED.value in task_statuses or TaskStatus.PENDING.value in task_statuses:
                run_status = "review_pending"
            else:
                run_status = "completed_with_blockers"
        elif state == MeetingState.BLOCKED and (
            TaskStatus.REVIEW_REQUIRED.value in task_statuses
            and TaskStatus.FAILED.value not in task_statuses
        ):
            run_status = "review_pending"
        else:
            run_status = self._run_status_for(state)

        consumed = meeting["budget_consumed"]
        budget_status = meeting["budget_status"]
        if budget_status == "active":
            budget_status = (
                "within_budget"
                if consumed["token_measurement_complete"] and consumed["cost_measurement_complete"]
                else "within_budget_with_unavailable_usage"
            )
        usage = {
            "provider_calls": consumed["agent_calls"],
            "input_tokens": (
                consumed["known_input_tokens"] if consumed["token_measurement_complete"] else None
            ),
            "output_tokens": (
                consumed["known_output_tokens"] if consumed["token_measurement_complete"] else None
            ),
            "total_tokens": (
                consumed["known_total_tokens"] if consumed["token_measurement_complete"] else None
            ),
            "latency_ms": (
                consumed["known_latency_ms"] if consumed["latency_measurement_complete"] else None
            ),
            "estimated_cost_usd": (
                consumed["known_cost_usd"] if consumed["cost_measurement_complete"] else None
            ),
            "token_status": "measured" if consumed["token_measurement_complete"] else "unavailable",
            "cost_status": "measured" if consumed["cost_measurement_complete"] else "unavailable",
        }
        meeting_attempt = int(meeting.get("attempt", 1))
        finished_at = utc_now()
        cancellation = meeting.get("cancellation")
        cancellation = cancellation if isinstance(cancellation, dict) else {}
        experience = {
            "schema_version": 1,
            "experience_id": f"{workspace.run_id}:meeting:{meeting_attempt}",
            "execution_kind": self._execution_kind(),
            "run_id": workspace.run_id,
            "meeting_attempt": meeting_attempt,
            "task_class": (
                workspace.plan().task_profile.task_type
                if workspace.plan().task_profile is not None
                else "general"
            ),
            "strategy": "multi_agent",
            "meeting_started": meeting["started_at"],
            "participants": [
                {
                    "task_id": task_id,
                    "agent_id": participant.get("agent_id"),
                    "status": participant["status"],
                }
                for task_id, participant in meeting["participants"].items()
            ],
            "rounds_executed": list(meeting["rounds_executed"]),
            "agent_calls": consumed["agent_calls"],
            "conflicts_detected": len(meeting["conflicts"]),
            "cross_reviews": len(meeting["cross_reviews"]),
            "round1_consensus": not bool(meeting["conflicts"]),
            "cross_review": bool(meeting["cross_reviews"]),
            "early_stopped": bool(meeting["early_stopped"]),
            "dissent_count": len(meeting["dissent"]),
            "tokens": usage["total_tokens"],
            "token_status": usage["token_status"],
            "cost": usage["estimated_cost_usd"],
            "cost_status": usage["cost_status"],
            "latency_ms": usage["latency_ms"],
            "elapsed_time": self._elapsed_seconds(meeting["started_at"], finished_at),
            "budget_status": budget_status,
            "budget_exhaustion_reason": meeting.get("budget_exhaustion_reason"),
            "final_success": state == MeetingState.COMPLETED and run_status == "completed",
            "meeting_state": state.value,
            "cancellation_requested": bool(meeting.get("cancel_requested")),
            "cancellation_time": meeting.get("cancel_requested_at"),
            "provider_running_at_cancel": bool(
                cancellation.get("provider_running_at_cancel", False)
            ),
            "graceful_termination": bool(cancellation.get("graceful_termination", False)),
            "forced_termination": bool(cancellation.get("forced_termination", False)),
            "partial_result": bool(cancellation.get("partial_result", False)),
            "termination_status": cancellation.get("termination_status"),
            "final_state": state.value,
            "validation": self._validation_status(workspace),
            "created_at": finished_at,
        }
        experience_ref = (
            "final/meeting-experience.json"
            if meeting_attempt == 1
            else f"final/meeting-experience-attempt-{meeting_attempt}.json"
        )
        atomic_write_json(workspace.contained(experience_ref), experience)
        MeetingExperienceLedger(workspace.meeting_experience_path).record(experience)
        self._record_meeting_memory(workspace)

        def finish(run_manifest: dict[str, Any]) -> dict[str, Any]:
            run_manifest["status"] = run_status
            run_manifest["meeting"]["usage"] = usage
            run_manifest["meeting"]["budget_status"] = budget_status
            run_manifest["meeting"]["experience_ref"] = experience_ref
            run_manifest["meeting"]["finished_at"] = finished_at
            run_manifest["finished_at"] = run_manifest["meeting"]["finished_at"]
            return run_manifest

        return workspace.update_manifest(finish)

    def _execution_kind(self) -> str:
        return str(getattr(self.provider, "execution_kind", "unknown"))

    @staticmethod
    def _elapsed_seconds(started_at: str, finished_at: str) -> float | None:
        try:
            start = datetime.fromisoformat(started_at)
            finish = datetime.fromisoformat(finished_at)
        except (TypeError, ValueError):
            return None
        return max(0.0, round((finish - start).total_seconds(), 3))

    @staticmethod
    def _validation_status(workspace: RunWorkspace) -> str:
        result = workspace.contained("final", "meeting-result.json")
        if not result.is_file():
            return "not_reached"
        return str(workspace.read_json("final/meeting-result.json").get("validation", "unknown"))

    @staticmethod
    def _record_meeting_memory(workspace: RunWorkspace) -> None:
        meeting = workspace.manifest()["meeting"]
        result_path = workspace.contained("final", "meeting-result.json")
        decision = None
        if result_path.is_file():
            decision = workspace.read_json("final/meeting-result.json").get("decision")
        memory = AgentPerformanceMemory(workspace.performance_memory_path)
        for task_id, participant in meeting["participants"].items():
            agent_id = participant.get("agent_id")
            raw = participant.get("contribution")
            if not isinstance(agent_id, str) or not isinstance(raw, dict):
                continue
            contribution = MeetingContribution.from_dict(raw)
            try:
                memory.record_meeting_contribution(
                    agent_id,
                    workspace.run_id,
                    disagreed=(
                        isinstance(decision, str)
                        and MeetingRuntime._normalize(contribution.position)
                        != MeetingRuntime._normalize(decision)
                    ),
                    cross_reviewed=any(
                        review.get("source_participant") == task_id
                        for review in meeting["cross_reviews"].values()
                    ),
                    accepted=(
                        isinstance(decision, str)
                        and MeetingRuntime._normalize(contribution.position)
                        == MeetingRuntime._normalize(decision)
                    ),
                )
            except (OSError, TypeError, ValueError, KeyError):
                continue

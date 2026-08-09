"""Provider adapters. Real command execution is disabled unless explicitly enabled."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Protocol

from ..workspace.providers.config import prepare_claude_environment
from .execution import ManagedProcessResult, ProviderExecutionHandle
from .models import (
    AgentSpec,
    MeetingContribution,
    ProviderResult,
    ReviewDecision,
    TaskSpec,
    UsageMetrics,
)
from .workspace import atomic_write_json

_NATIVE_PROVIDERS = frozenset({"codex", "claude", "deepseek"})
_DEPENDENCY_CONTEXT_LIMIT = 12_000
_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean"},
        "summary": {"type": "string"},
        "outputs": {"type": "object"},
        "review": {
            "anyOf": [
                {
                    "type": "string",
                    "enum": [
                        "APPROVED",
                        "APPROVED_WITH_NOTES",
                        "BLOCKED",
                        "REVIEW_PENDING",
                    ],
                },
                {"type": "null"},
            ]
        },
        "findings": {"type": "array", "items": {"type": "string"}},
        "contribution": {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "position": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "key_reasons": {"type": "array", "items": {"type": "string"}},
                        "risks": {"type": "array", "items": {"type": "string"}},
                        "assumptions": {"type": "array", "items": {"type": "string"}},
                        "blocking_concerns": {"type": "array", "items": {"type": "string"}},
                        "evidence_refs": {"type": "array", "items": {"type": "string"}},
                        "acceptance_constraints_met": {"type": "boolean"},
                        "dissent": {"type": "boolean"},
                        "action": {
                            "anyOf": [
                                {"type": "string", "enum": ["defend", "revise", "reject", "combine"]},
                                {"type": "null"},
                            ]
                        },
                        "position_changed": {"type": "boolean"},
                        "resolved": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
                        "remaining_dissent": {"type": "boolean"},
                        "new_evidence": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["position", "confidence"],
                    "additionalProperties": False,
                },
                {"type": "null"},
            ]
        },
    },
    "required": ["success", "summary", "outputs", "review", "findings"],
    "additionalProperties": False,
}


class Provider(Protocol):
    def execute(
        self,
        task: TaskSpec,
        agent: AgentSpec,
        task_dir: Path,
        project_root: Path,
    ) -> ProviderResult: ...


@dataclass
class FakeProvider:
    """Deterministic provider used by tests and the public example."""

    failures_before_success: dict[str, int] = field(default_factory=dict)
    reviews: dict[str, ReviewDecision] = field(default_factory=dict)
    meeting_positions: dict[str, str] = field(default_factory=dict)
    round2_positions: dict[str, str] = field(default_factory=dict)
    meeting_confidence: dict[str, float] = field(default_factory=dict)
    failures_by_agent: dict[str, int] = field(default_factory=dict)
    calls: dict[str, int] = field(default_factory=dict)

    def execute(
        self,
        task: TaskSpec,
        agent: AgentSpec,
        task_dir: Path,
        project_root: Path,
    ) -> ProviderResult:
        count = self.calls.get(task.id, 0) + 1
        self.calls[task.id] = count
        if count <= self.failures_before_success.get(task.id, 0):
            return ProviderResult(False, f"synthetic failure {count}")
        if self.failures_by_agent.get(agent.id, 0) > 0:
            self.failures_by_agent[agent.id] -= 1
            return ProviderResult(False, f"synthetic agent failure: {agent.id}")
        review = self.reviews.get(task.id)
        source_participant = str(task.inputs.get("source_participant", task.id))
        if task.inputs.get("meeting_round") == 2:
            review = self.reviews.get(source_participant, review)
        if task.role == "reviewer" and review is None:
            review = ReviewDecision.APPROVED
        contribution = None
        meeting_round = task.inputs.get("meeting_round")
        if meeting_round in {1, 2}:
            initial_position = self.meeting_positions.get(source_participant, "proceed")
            position = (
                self.round2_positions.get(source_participant, initial_position)
                if meeting_round == 2
                else initial_position
            )
            blockers: tuple[str, ...] = ()
            if review == ReviewDecision.BLOCKED:
                position = self.meeting_positions.get(source_participant, "block")
                blockers = ("synthetic blocking review",)
            elif review == ReviewDecision.REVIEW_PENDING:
                position = self.meeting_positions.get(source_participant, "pending")
                blockers = ("review remains pending",)
            changed = meeting_round == 2 and position != initial_position
            resolution_supplied = (
                meeting_round == 2 and source_participant in self.round2_positions
            )
            contribution = MeetingContribution(
                position=position,
                confidence=self.meeting_confidence.get(source_participant, 0.9),
                key_reasons=(f"synthetic view from {source_participant}",),
                blocking_concerns=blockers,
                acceptance_constraints_met=review != ReviewDecision.REVIEW_PENDING,
                action="revise" if changed else ("defend" if meeting_round == 2 else None),
                position_changed=changed,
                resolved=resolution_supplied if meeting_round == 2 else None,
                remaining_dissent=meeting_round == 2 and not resolution_supplied,
            )
        return ProviderResult(
            True,
            f"synthetic {agent.role} completed {task.id}",
            outputs={"task_id": task.id, "agent_id": agent.id, "synthetic": True},
            review=review,
            contribution=contribution,
            usage=UsageMetrics(
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
                estimated_cost_usd=0.0,
                token_status="measured",
                cost_status="measured",
            ),
        )


class DryRunProvider(FakeProvider):
    """Alias with explicit intent for CLI dry-run execution."""


class LocalCommandProvider:
    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled

    def execute(
        self,
        task: TaskSpec,
        agent: AgentSpec,
        task_dir: Path,
        project_root: Path,
    ) -> ProviderResult:
        if not self.enabled:
            return ProviderResult(False, "real provider execution is disabled")
        if agent.provider in _NATIVE_PROVIDERS:
            return self._execute_native(task, agent, task_dir, project_root)
        command = [
            part.replace("{task_file}", str(task_dir / "task.json"))
            for part in agent.command_template
        ]
        started = time.monotonic()
        completed = self._execute_managed(
            command,
            task=task,
            agent=agent,
            task_dir=task_dir,
            project_root=project_root,
        )
        latency_ms = round((time.monotonic() - started) * 1000)
        if completed.cancelled or completed.state == "cancel_unverified":
            return ProviderResult(
                False,
                (
                    "local command cancellation could not verify process identity"
                    if completed.state == "cancel_unverified"
                    else "local command cancelled"
                ),
                outputs={
                    "stdout": completed.stdout[-40_000:],
                    "stderr": completed.stderr[-40_000:],
                    "execution_ref": completed.execution_ref,
                },
                usage=UsageMetrics(latency_ms=latency_ms),
                cancelled=completed.cancelled,
                partial_result=completed.partial_result,
                termination=completed.termination,
            )
        if completed.timed_out:
            return ProviderResult(
                False,
                f"local command timed out after {task.timeout_seconds} seconds",
                outputs={
                    "stdout": completed.stdout[-40_000:],
                    "stderr": completed.stderr[-40_000:],
                    "execution_ref": completed.execution_ref,
                },
                usage=UsageMetrics(latency_ms=latency_ms),
                partial_result=completed.partial_result,
                termination=completed.termination,
            )
        return ProviderResult(
            completed.returncode == 0,
            f"local command exited {completed.returncode}",
            outputs={
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "execution_ref": completed.execution_ref,
            },
            usage=UsageMetrics(latency_ms=latency_ms),
            termination=completed.termination,
        )

    def _execute_native(
        self,
        task: TaskSpec,
        agent: AgentSpec,
        task_dir: Path,
        project_root: Path,
    ) -> ProviderResult:
        schema_path = task_dir / "provider-result.schema.json"
        result_path = task_dir / "provider-output.json"
        atomic_write_json(schema_path, _RESULT_SCHEMA)
        result_path.unlink(missing_ok=True)
        prompt = self._task_prompt(task, task_dir)
        command = self._native_command(agent, task, schema_path, result_path)
        child_env = os.environ.copy()
        if agent.provider in {"claude", "deepseek"}:
            prepare_claude_environment(agent.provider, child_env)

        started = time.monotonic()
        completed = self._execute_managed(
            command,
            task=task,
            agent=agent,
            task_dir=task_dir,
            project_root=project_root,
            env=child_env,
            input_text=prompt,
        )
        latency_ms = round((time.monotonic() - started) * 1000)
        if completed.cancelled or completed.state == "cancel_unverified":
            partial = self._native_result(completed.stdout, result_path, latency_ms)
            return replace(
                partial,
                success=False,
                summary=(
                    f"{agent.provider} cancellation could not verify process identity"
                    if completed.state == "cancel_unverified"
                    else f"{agent.provider} command cancelled"
                ),
                outputs={
                    **partial.outputs,
                    "stdout": completed.stdout[-40_000:],
                    "stderr": completed.stderr[-40_000:],
                    "execution_ref": completed.execution_ref,
                },
                cancelled=completed.cancelled,
                partial_result=completed.partial_result or result_path.is_file(),
                termination=completed.termination,
            )
        if completed.timed_out:
            return ProviderResult(
                False,
                f"{agent.provider} timed out after {task.timeout_seconds} seconds",
                outputs={
                    "stdout": completed.stdout[-40_000:],
                    "stderr": completed.stderr[-40_000:],
                    "execution_ref": completed.execution_ref,
                },
                usage=UsageMetrics(latency_ms=latency_ms),
                partial_result=completed.partial_result or result_path.is_file(),
                termination=completed.termination,
            )
        if completed.returncode != 0:
            return ProviderResult(
                False,
                f"{agent.provider} command exited {completed.returncode}",
                outputs={
                    "stdout": completed.stdout[-40_000:],
                    "stderr": completed.stderr[-40_000:],
                    "execution_ref": completed.execution_ref,
                },
                usage=UsageMetrics(latency_ms=latency_ms),
                termination=completed.termination,
            )
        result = self._native_result(completed.stdout, result_path, latency_ms)
        return replace(
            result,
            outputs={**result.outputs, "execution_ref": completed.execution_ref},
            termination=completed.termination,
        )

    @staticmethod
    def _execute_managed(
        command: list[str],
        *,
        task: TaskSpec,
        agent: AgentSpec,
        task_dir: Path,
        project_root: Path,
        env: dict[str, str] | None = None,
        input_text: str | None = None,
    ) -> ManagedProcessResult:
        handle = ProviderExecutionHandle.start(
            command,
            provider=agent.provider,
            task_id=task.id,
            participant_id=agent.id,
            task_dir=task_dir,
            project_root=project_root,
            env=env,
        )
        return handle.communicate(input_text, timeout_seconds=task.timeout_seconds)

    @staticmethod
    def _native_command(
        agent: AgentSpec,
        task: TaskSpec,
        schema_path: Path,
        result_path: Path,
    ) -> list[str]:
        if agent.provider == "codex":
            sandbox = (
                "read-only"
                if task.role in {"architect", "reviewer"} or task.inputs.get("meeting_round")
                else "workspace-write"
            )
            return [
                agent.command_template[0],
                "exec",
                "--ephemeral",
                "--color",
                "never",
                "--sandbox",
                sandbox,
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(result_path),
                "-",
            ]
        permission = (
            "plan"
            if task.role in {"architect", "reviewer"} or task.inputs.get("meeting_round")
            else "acceptEdits"
        )
        return [
            agent.command_template[0],
            "--print",
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(_RESULT_SCHEMA, separators=(",", ":")),
            "--no-session-persistence",
            "--permission-mode",
            permission,
        ]

    @staticmethod
    def _task_prompt(task: TaskSpec, task_dir: Path) -> str:
        dependency_artifacts: dict[str, object] = {}
        run_root = task_dir.parent.parent
        for dependency in task.dependencies:
            result_path = run_root / "tasks" / dependency / "result.json"
            if result_path.is_file():
                try:
                    with result_path.open(encoding="utf-8") as handle:
                        content = handle.read(_DEPENDENCY_CONTEXT_LIMIT + 1)
                    if len(content) > _DEPENDENCY_CONTEXT_LIMIT:
                        dependency_artifacts[dependency] = {
                            "artifact_ref": str(result_path),
                            "artifact_truncated": True,
                            "preview": content[:_DEPENDENCY_CONTEXT_LIMIT],
                        }
                    else:
                        dependency_artifacts[dependency] = json.loads(content)
                except (OSError, json.JSONDecodeError):
                    dependency_artifacts[dependency] = {"status": "artifact_unreadable"}
        context = {
            "task": task.to_dict(),
            "dependency_artifacts": dependency_artifacts,
        }
        meeting_instruction = ""
        if task.inputs.get("meeting_round") == 1:
            meeting_instruction = (
                " This is an independent Round 1 view: read the shared context_pack_ref, do not "
                "seek other participants' output, and populate contribution with position, confidence, "
                "reasons, risks, assumptions, blockers, and evidence references."
            )
        elif task.inputs.get("meeting_round") == 2:
            meeting_instruction = (
                " This is a targeted cross-review: read only conflict_pack_ref and relevant evidence, "
                "then defend, revise, reject, or combine; populate all cross-review contribution fields."
            )
        return (
            "Execute this bounded FlowFoundry task in the current project workspace. "
            "Inspect only the context needed, respect the declared permissions, and do not "
            "expose credentials. Return only a JSON object matching the requested schema. "
            "For reviewer tasks, set review to one of APPROVED, APPROVED_WITH_NOTES, BLOCKED, "
            "or REVIEW_PENDING."
            + meeting_instruction
            + " Context:\n"
            + json.dumps(context, indent=2, ensure_ascii=False)
        )

    @staticmethod
    def _native_result(stdout: str, result_path: Path, latency_ms: int) -> ProviderResult:
        wrapper: dict[str, object] = {}
        envelope: object = None
        if result_path.is_file():
            try:
                envelope = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                envelope = None
        if envelope is None:
            try:
                parsed = json.loads(stdout)
                if isinstance(parsed, dict):
                    wrapper = parsed
                    envelope = parsed.get("structured_output", parsed.get("result", parsed))
            except json.JSONDecodeError:
                envelope = None
        if isinstance(envelope, str):
            try:
                envelope = json.loads(envelope)
            except json.JSONDecodeError:
                envelope = None
        if not isinstance(envelope, dict):
            return ProviderResult(
                False,
                "provider did not return the required structured result",
                outputs={"stdout": stdout[-40_000:]},
                usage=UsageMetrics(latency_ms=latency_ms),
            )

        review_value = envelope.get("review")
        try:
            review = ReviewDecision(str(review_value)) if review_value is not None else None
        except ValueError:
            review = ReviewDecision.REVIEW_PENDING
        outputs = envelope.get("outputs")
        findings = envelope.get("findings")
        contribution_data = envelope.get("contribution")
        usage = wrapper.get("usage") if isinstance(wrapper.get("usage"), dict) else {}
        input_tokens = _nonnegative_int(usage.get("input_tokens"))
        output_tokens = _nonnegative_int(usage.get("output_tokens"))
        cost = _nonnegative_float(wrapper.get("total_cost_usd"))
        return ProviderResult(
            success=bool(envelope.get("success", False)),
            summary=str(envelope.get("summary", "provider returned no summary")),
            outputs=outputs if isinstance(outputs, dict) else {},
            review=review,
            findings=tuple(str(item) for item in findings) if isinstance(findings, list) else (),
            contribution=(
                MeetingContribution.from_dict(contribution_data)
                if isinstance(contribution_data, dict)
                else None
            ),
            usage=UsageMetrics(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                estimated_cost_usd=cost,
                token_status=(
                    "measured"
                    if input_tokens is not None and output_tokens is not None
                    else "unavailable"
                ),
                cost_status="measured" if cost is not None else "unavailable",
            ),
        )


def _nonnegative_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _nonnegative_float(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return float(value)
    return None

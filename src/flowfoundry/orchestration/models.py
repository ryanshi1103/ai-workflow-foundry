"""Serializable models shared by the orchestration runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    REVIEW_REQUIRED = "review_required"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    SKIPPED_PENDING_HUMAN = "skipped_pending_human"
    CANCELLED = "cancelled"


class ReviewDecision(StrEnum):
    APPROVED = "APPROVED"
    APPROVED_WITH_NOTES = "APPROVED_WITH_NOTES"
    BLOCKED = "BLOCKED"
    REVIEW_PENDING = "REVIEW_PENDING"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionMode(StrEnum):
    SINGLE_AGENT = "single_agent"
    SINGLE_AGENT_REVIEWER = "single_agent_reviewer"
    MULTI_AGENT = "multi_agent"


class IsolationMode(StrEnum):
    """Filesystem isolation required by one concrete execution."""

    NONE = "none"
    READ_ONLY = "read_only"
    MANAGED_WORKTREE = "managed_worktree"


class WorktreeStatus(StrEnum):
    ALLOCATING = "allocating"
    READY = "ready"
    IN_USE = "in_use"
    VALIDATING = "validating"
    COMPLETED = "completed"
    RETAINED = "retained"
    REMOVED = "removed"
    FAILED = "failed"
    ORPHANED = "orphaned"
    BLOCKED = "blocked"


class MeetingState(StrEnum):
    PLANNED = "planned"
    CONTEXT_READY = "context_ready"
    ROUND1_RUNNING = "round1_running"
    ROUND1_COMPLETE = "round1_complete"
    CONFLICT_CHECKED = "conflict_checked"
    ROUND2_RUNNING = "round2_running"
    ROUND2_COMPLETE = "round2_complete"
    CONVERGING = "converging"
    VALIDATING = "validating"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CANCEL_UNVERIFIED = "cancel_unverified"
    BUDGET_EXHAUSTED = "budget_exhausted"


@dataclass(frozen=True)
class TaskProfile:
    """Small, explainable task assessment used before choosing a team size."""

    task_type: str
    complexity: int
    uncertainty: int
    impact: int
    failure_risk: int
    reversibility: str
    context_size: str
    coding_requirement: bool
    research_requirement: bool
    multimodal_requirement: bool
    privacy_requirement: str
    estimated_workload: str
    expected_quality: int
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("complexity", "uncertainty", "impact", "failure_risk", "expected_quality"):
            value = getattr(self, name)
            if not 1 <= value <= 5:
                raise ValueError(f"{name} must be between 1 and 5")
        if self.reversibility not in {"easy", "moderate", "hard"}:
            raise ValueError("reversibility must be easy, moderate, or hard")
        if self.context_size not in {"small", "medium", "large"}:
            raise ValueError("context_size must be small, medium, or large")
        if self.privacy_requirement not in {"normal", "high"}:
            raise ValueError("privacy_requirement must be normal or high")
        if self.estimated_workload not in {"small", "medium", "large"}:
            raise ValueError("estimated_workload must be small, medium, or large")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskProfile:
        return cls(
            task_type=str(data.get("task_type", "general")),
            complexity=int(data.get("complexity", 2)),
            uncertainty=int(data.get("uncertainty", 2)),
            impact=int(data.get("impact", 2)),
            failure_risk=int(data.get("failure_risk", 1)),
            reversibility=str(data.get("reversibility", "easy")),
            context_size=str(data.get("context_size", "small")),
            coding_requirement=bool(data.get("coding_requirement", False)),
            research_requirement=bool(data.get("research_requirement", False)),
            multimodal_requirement=bool(data.get("multimodal_requirement", False)),
            privacy_requirement=str(data.get("privacy_requirement", "normal")),
            estimated_workload=str(data.get("estimated_workload", "small")),
            expected_quality=int(data.get("expected_quality", 3)),
            evidence=tuple(str(item) for item in data.get("evidence", ())),
        )


@dataclass(frozen=True)
class RoutingDecision:
    mode: ExecutionMode
    reasons: tuple[str, ...]
    estimated_agent_calls: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "reasons": list(self.reasons),
            "estimated_agent_calls": self.estimated_agent_calls,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RoutingDecision:
        return cls(
            mode=ExecutionMode(data["mode"]),
            reasons=tuple(str(item) for item in data.get("reasons", ())),
            estimated_agent_calls=int(data.get("estimated_agent_calls", 1)),
        )


@dataclass(frozen=True)
class MeetingBudget:
    """Hard limits for one bounded meeting."""

    max_rounds: int = 3
    max_agent_calls: int = 7
    max_total_tokens: int | None = 100_000
    max_wall_time_seconds: int = 900
    max_cost_usd: float | None = None

    def __post_init__(self) -> None:
        for name in ("max_rounds", "max_agent_calls", "max_wall_time_seconds"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be positive")
        if self.max_rounds > 3:
            raise ValueError("bounded meetings support at most three rounds")
        if self.max_total_tokens is not None and self.max_total_tokens < 1:
            raise ValueError("max_total_tokens must be positive when configured")
        if self.max_cost_usd is not None and self.max_cost_usd < 0:
            raise ValueError("max_cost_usd must not be negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MeetingBudget:
        return cls(
            max_rounds=int(data.get("max_rounds", 3)),
            max_agent_calls=int(data.get("max_agent_calls", 7)),
            max_total_tokens=(
                int(data["max_total_tokens"])
                if data.get("max_total_tokens") is not None
                else None
            ),
            max_wall_time_seconds=int(data.get("max_wall_time_seconds", 900)),
            max_cost_usd=(
                float(data["max_cost_usd"])
                if data.get("max_cost_usd") is not None
                else None
            ),
        )


@dataclass(frozen=True)
class MeetingPlan:
    """Capability-shaped participants and limits attached to a multi-agent plan."""

    participant_task_ids: tuple[str, ...]
    validation_task_ids: tuple[str, ...] = ()
    budget: MeetingBudget = field(default_factory=MeetingBudget)
    minimum_participants: int = 2
    confidence_threshold: float = 0.65
    context_char_limit: int = 12_000

    def __post_init__(self) -> None:
        if len(set(self.participant_task_ids)) != len(self.participant_task_ids):
            raise ValueError("meeting participant task ids must be unique")
        if self.minimum_participants < 1:
            raise ValueError("minimum_participants must be positive")
        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError("confidence_threshold must be between zero and one")
        if self.context_char_limit < 256:
            raise ValueError("context_char_limit is too small")

    def to_dict(self) -> dict[str, Any]:
        return {
            "participant_task_ids": list(self.participant_task_ids),
            "validation_task_ids": list(self.validation_task_ids),
            "budget": self.budget.to_dict(),
            "minimum_participants": self.minimum_participants,
            "confidence_threshold": self.confidence_threshold,
            "context_char_limit": self.context_char_limit,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MeetingPlan:
        budget = data.get("budget")
        return cls(
            participant_task_ids=tuple(str(item) for item in data.get("participant_task_ids", ())),
            validation_task_ids=tuple(str(item) for item in data.get("validation_task_ids", ())),
            budget=MeetingBudget.from_dict(budget) if isinstance(budget, dict) else MeetingBudget(),
            minimum_participants=int(data.get("minimum_participants", 2)),
            confidence_threshold=float(data.get("confidence_threshold", 0.65)),
            context_char_limit=int(data.get("context_char_limit", 12_000)),
        )


@dataclass(frozen=True)
class AgentSpec:
    id: str
    display_name: str
    provider: str
    role: str
    capabilities: tuple[str, ...]
    command_template: tuple[str, ...]
    cost_class: str
    concurrency_limit: int
    permission_profile: tuple[str, ...]
    context_limit: int
    availability: bool
    workspace_mode: str
    enabled: bool = True
    model: str = "unspecified"
    mode: str = "command"
    tools: tuple[str, ...] = ()
    coding_ability: int = 1
    reasoning_ability: int = 1
    multimodal_ability: bool = False
    web_research_ability: bool = False
    local: bool = False
    privacy_level: str = "standard"
    expected_latency_ms: int | None = None
    estimated_cost_per_million_tokens: float | None = None
    authentication_state: str = "unconfigured"
    reliability: float | None = None
    current_quota: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TaskSpec:
    id: str
    title: str
    role: str
    required_capabilities: tuple[str, ...]
    preferred_capabilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    inputs: dict[str, Any] = field(default_factory=dict)
    expected_outputs: tuple[str, ...] = ()
    risk_level: RiskLevel = RiskLevel.LOW
    approval_requirements: tuple[str, ...] = ()
    required_permissions: tuple[str, ...] = ("read_workspace",)
    validation_commands: tuple[str, ...] = ()
    retry_limit: int = 1
    timeout_seconds: int = 300
    review_required: bool = False
    fallback_agent: str | None = None
    tool_requirement: str | None = None
    tool_policy_mode: str = "provider_default"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        # Preserve the legacy plan and prompt envelope unless a task explicitly
        # opts into a classified tool policy.
        if self.tool_requirement is None:
            data.pop("tool_requirement")
        if self.tool_policy_mode == "provider_default":
            data.pop("tool_policy_mode")
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskSpec:
        return cls(
            id=str(data["id"]),
            title=str(data.get("title", data["id"])),
            role=str(data["role"]),
            required_capabilities=tuple(data.get("required_capabilities", ())),
            preferred_capabilities=tuple(data.get("preferred_capabilities", ())),
            dependencies=tuple(data.get("dependencies", ())),
            inputs=dict(data.get("inputs", {})),
            expected_outputs=tuple(data.get("expected_outputs", ())),
            risk_level=RiskLevel(data.get("risk_level", RiskLevel.LOW.value)),
            approval_requirements=tuple(data.get("approval_requirements", ())),
            required_permissions=tuple(data.get("required_permissions", ("read_workspace",))),
            validation_commands=tuple(data.get("validation_commands", ())),
            retry_limit=int(data.get("retry_limit", 1)),
            timeout_seconds=int(data.get("timeout_seconds", 300)),
            review_required=bool(data.get("review_required", False)),
            fallback_agent=data.get("fallback_agent"),
            tool_requirement=(
                str(data["tool_requirement"])
                if data.get("tool_requirement") is not None
                else None
            ),
            tool_policy_mode=str(data.get("tool_policy_mode", "provider_default")),
        )


@dataclass(frozen=True)
class TaskPlan:
    goal: str
    tasks: tuple[TaskSpec, ...]
    schema_version: int = 1
    task_profile: TaskProfile | None = None
    routing_decision: RoutingDecision | None = None
    meeting_plan: MeetingPlan | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "schema_version": self.schema_version,
            "goal": self.goal,
            "tasks": [task.to_dict() for task in self.tasks],
        }
        if self.task_profile is not None:
            data["task_profile"] = self.task_profile.to_dict()
        if self.routing_decision is not None:
            data["routing_decision"] = self.routing_decision.to_dict()
        if self.meeting_plan is not None:
            data["meeting_plan"] = self.meeting_plan.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskPlan:
        profile_data = data.get("task_profile")
        decision_data = data.get("routing_decision")
        meeting_data = data.get("meeting_plan")
        return cls(
            goal=str(data["goal"]),
            tasks=tuple(TaskSpec.from_dict(item) for item in data.get("tasks", ())),
            schema_version=int(data.get("schema_version", 1)),
            task_profile=TaskProfile.from_dict(profile_data) if isinstance(profile_data, dict) else None,
            routing_decision=(
                RoutingDecision.from_dict(decision_data)
                if isinstance(decision_data, dict)
                else None
            ),
            meeting_plan=(
                MeetingPlan.from_dict(meeting_data)
                if isinstance(meeting_data, dict)
                else None
            ),
        )


@dataclass(frozen=True)
class MeetingContribution:
    """Structured opinion used by deterministic conflict and convergence rules."""

    position: str
    confidence: float
    key_reasons: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    blocking_concerns: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    acceptance_constraints_met: bool = True
    dissent: bool = False
    action: str | None = None
    position_changed: bool = False
    resolved: bool | None = None
    remaining_dissent: bool = False
    new_evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.position.strip():
            raise ValueError("meeting position must not be empty")
        if not 0 <= self.confidence <= 1:
            raise ValueError("meeting confidence must be between zero and one")
        if self.action not in {None, "defend", "revise", "reject", "combine"}:
            raise ValueError("invalid cross-review action")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MeetingContribution:
        return cls(
            position=str(data.get("position", "undetermined")),
            confidence=float(data.get("confidence", 0.0)),
            key_reasons=tuple(str(item) for item in data.get("key_reasons", ())),
            risks=tuple(str(item) for item in data.get("risks", ())),
            assumptions=tuple(str(item) for item in data.get("assumptions", ())),
            blocking_concerns=tuple(str(item) for item in data.get("blocking_concerns", ())),
            evidence_refs=tuple(str(item) for item in data.get("evidence_refs", ())),
            acceptance_constraints_met=bool(data.get("acceptance_constraints_met", True)),
            dissent=bool(data.get("dissent", False)),
            action=str(data["action"]) if data.get("action") is not None else None,
            position_changed=bool(data.get("position_changed", False)),
            resolved=data.get("resolved") if isinstance(data.get("resolved"), bool) else None,
            remaining_dissent=bool(data.get("remaining_dissent", False)),
            new_evidence=tuple(str(item) for item in data.get("new_evidence", ())),
        )


@dataclass(frozen=True)
class ProviderResult:
    success: bool
    summary: str
    outputs: dict[str, Any] = field(default_factory=dict)
    review: ReviewDecision | None = None
    findings: tuple[str, ...] = ()
    usage: UsageMetrics = field(default_factory=lambda: UsageMetrics())
    contribution: MeetingContribution | None = None
    cancelled: bool = False
    partial_result: bool = False
    termination: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["review"] = self.review.value if self.review else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProviderResult:
        review_value = data.get("review")
        contribution = data.get("contribution")
        usage = data.get("usage")
        return cls(
            success=bool(data.get("success", False)),
            summary=str(data.get("summary", "provider returned no summary")),
            outputs=dict(data.get("outputs", {})),
            review=ReviewDecision(str(review_value)) if review_value is not None else None,
            findings=tuple(str(item) for item in data.get("findings", ())),
            usage=UsageMetrics(**usage) if isinstance(usage, dict) else UsageMetrics(),
            contribution=(
                MeetingContribution.from_dict(contribution)
                if isinstance(contribution, dict)
                else None
            ),
            cancelled=bool(data.get("cancelled", False)),
            partial_result=bool(data.get("partial_result", False)),
            termination=(
                dict(data.get("termination", {}))
                if isinstance(data.get("termination"), dict)
                else {}
            ),
        )


@dataclass(frozen=True)
class UsageMetrics:
    """Provider-reported or locally measured usage; unknown values stay unknown."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    estimated_cost_usd: float | None = None
    token_status: str = "unavailable"
    cost_status: str = "unavailable"

    def __post_init__(self) -> None:
        for name in ("input_tokens", "output_tokens", "latency_ms", "estimated_cost_usd"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must not be negative")
        if self.token_status not in {"measured", "estimated", "unavailable"}:
            raise ValueError("invalid token_status")
        if self.cost_status not in {"measured", "estimated", "unavailable"}:
            raise ValueError("invalid cost_status")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

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

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
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
        )


@dataclass(frozen=True)
class TaskPlan:
    goal: str
    tasks: tuple[TaskSpec, ...]
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "goal": self.goal,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskPlan:
        return cls(
            goal=str(data["goal"]),
            tasks=tuple(TaskSpec.from_dict(item) for item in data.get("tasks", ())),
            schema_version=int(data.get("schema_version", 1)),
        )


@dataclass(frozen=True)
class ProviderResult:
    success: bool
    summary: str
    outputs: dict[str, Any] = field(default_factory=dict)
    review: ReviewDecision | None = None
    findings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["review"] = self.review.value if self.review else None
        return data

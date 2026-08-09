"""Rule-based offline planner with a stable task-plan schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .intelligence import RuleBasedTaskAnalyzer
from .models import (
    ExecutionMode,
    MeetingBudget,
    MeetingPlan,
    RiskLevel,
    TaskPlan,
    TaskProfile,
    TaskSpec,
)


class RuleBasedPlanner:
    """Build the minimum sufficient bounded plan without a model call."""

    def __init__(self, analyzer: RuleBasedTaskAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RuleBasedTaskAnalyzer()

    def plan(
        self,
        goal: str,
        *,
        profile_overrides: dict[str, Any] | None = None,
        execution_mode: str | ExecutionMode | None = None,
    ) -> TaskPlan:
        clean_goal = goal.strip()
        if not clean_goal:
            raise ValueError("goal must not be empty")
        profile = self.analyzer.analyze(clean_goal, profile_overrides)
        decision = self.analyzer.decide(profile, execution_mode)
        tasks = self._tasks(clean_goal, profile, decision.mode)
        meeting_plan = self._meeting_plan(tasks) if decision.mode == ExecutionMode.MULTI_AGENT else None
        return TaskPlan(
            clean_goal,
            tasks,
            task_profile=profile,
            routing_decision=decision,
            meeting_plan=meeting_plan,
        )

    @staticmethod
    def _meeting_plan(tasks: tuple[TaskSpec, ...]) -> MeetingPlan:
        participants = tuple(task.id for task in tasks if task.role != "tester")
        validation = tuple(task.id for task in tasks if task.role == "tester")
        return MeetingPlan(
            participant_task_ids=participants,
            validation_task_ids=validation,
            budget=MeetingBudget(
                max_rounds=3,
                max_agent_calls=max(4, len(participants) * 2 + len(validation)),
                max_total_tokens=100_000,
                max_wall_time_seconds=900,
            ),
            minimum_participants=min(2, len(participants)),
        )

    def _tasks(
        self,
        goal: str,
        profile: TaskProfile,
        mode: ExecutionMode,
    ) -> tuple[TaskSpec, ...]:
        tasks: list[TaskSpec] = []
        needs_architect = mode == ExecutionMode.MULTI_AGENT and (
            profile.task_type in {"architecture", "research"}
            or not profile.coding_requirement
        )
        if needs_architect:
            tasks.append(
                TaskSpec(
                    id="architect",
                    title="Prepare a bounded decision and context pack",
                    role="architect",
                    required_capabilities=("architecture",),
                    preferred_capabilities=("planning",),
                    inputs={"goal": goal},
                    expected_outputs=("decision", "risks", "implementation_context"),
                )
            )

        build_capability = "implementation" if profile.coding_requirement else "documentation"
        build = TaskSpec(
            id="build",
            title="Execute the requested work",
            role="builder",
            required_capabilities=(build_capability,),
            preferred_capabilities=("python",) if profile.coding_requirement else (),
            dependencies=("architect",) if needs_architect else (),
            inputs={"goal": goal, **({"context_task": "architect"} if needs_architect else {})},
            expected_outputs=("implementation", "change_summary"),
            required_permissions=("read_workspace", "write_workspace"),
            validation_commands=("git diff --check",) if profile.coding_requirement else (),
            retry_limit=1,
            review_required=mode != ExecutionMode.SINGLE_AGENT,
        )
        tasks.append(build)

        if mode != ExecutionMode.SINGLE_AGENT:
            tasks.append(
                TaskSpec(
                    id="review",
                    title="Independently review the result",
                    role="reviewer",
                    required_capabilities=("review",),
                    preferred_capabilities=("security_review",) if profile.failure_risk >= 3 else (),
                    dependencies=("build",),
                    inputs={"source_task": "build"},
                    expected_outputs=("review_decision", "findings"),
                )
            )

        if mode == ExecutionMode.MULTI_AGENT and profile.coding_requirement:
            tasks.append(
                TaskSpec(
                    id="test",
                    title="Validate the reviewed implementation",
                    role="tester",
                    required_capabilities=("testing",),
                    dependencies=("review",),
                    inputs={"source_task": "build"},
                    expected_outputs=("test_results",),
                    required_permissions=("read_workspace", "write_workspace"),
                    validation_commands=("python -m pytest", "ruff check ."),
                    retry_limit=1,
                )
            )
        return tuple(tasks)

    def load(self, path: Path | str) -> TaskPlan:
        data: Any = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("task file must contain a JSON object")
        if "tasks" in data:
            plan = TaskPlan.from_dict(data)
            self.validate(plan)
            return plan
        profile = data.get("task_profile", data.get("profile"))
        if profile is not None and not isinstance(profile, dict):
            raise ValueError("task_profile must be a JSON object")
        return self.plan(
            str(data.get("goal", "")),
            profile_overrides=profile,
            execution_mode=data.get("execution_mode"),
        )

    def validate(self, plan: TaskPlan) -> None:
        if plan.schema_version != 1:
            raise ValueError("unsupported task plan schema")
        ids = [task.id for task in plan.tasks]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("task ids must be present and unique")
        known: set[str] = set()
        for task in plan.tasks:
            unknown = set(task.dependencies) - set(ids)
            if unknown:
                raise ValueError(f"task {task.id} has unknown dependencies: {sorted(unknown)}")
            if task.id in task.dependencies:
                raise ValueError(f"task {task.id} cannot depend on itself")
            if any(dependency not in known for dependency in task.dependencies):
                raise ValueError("task plan must be in dependency order")
            known.add(task.id)
        if plan.meeting_plan is not None:
            meeting_ids = set(plan.meeting_plan.participant_task_ids)
            validation_ids = set(plan.meeting_plan.validation_task_ids)
            if not meeting_ids:
                raise ValueError("meeting plan must have participants")
            if not (meeting_ids | validation_ids).issubset(ids):
                raise ValueError("meeting plan references unknown task ids")
            if meeting_ids.intersection(validation_ids):
                raise ValueError("meeting participants and validation tasks must be separate")

    def from_goal_data(self, data: dict[str, Any]) -> TaskPlan:
        """Provider-adapter seam: accept structured data without requiring a provider."""

        return self.plan(str(data.get("goal", "")))


def high_risk_task(task_id: str, title: str, action: str) -> TaskSpec:
    """Create an explicitly approval-gated task for operator-authored plans."""

    return TaskSpec(
        id=task_id,
        title=title,
        role="builder",
        required_capabilities=("implementation",),
        inputs={"action": action},
        risk_level=RiskLevel.HIGH,
        approval_requirements=(action,),
        required_permissions=("read_workspace", "write_workspace"),
    )

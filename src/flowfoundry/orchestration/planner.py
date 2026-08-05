"""Rule-based offline planner with a stable task-plan schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import RiskLevel, TaskPlan, TaskSpec


class RuleBasedPlanner:
    """Build a bounded Builder → Reviewer → Tester plan without a model call."""

    def plan(self, goal: str) -> TaskPlan:
        clean_goal = goal.strip()
        if not clean_goal:
            raise ValueError("goal must not be empty")
        return TaskPlan(
            goal=clean_goal,
            tasks=(
                TaskSpec(
                    id="build",
                    title="Implement the requested change",
                    role="builder",
                    required_capabilities=("implementation",),
                    preferred_capabilities=("python",),
                    inputs={"goal": clean_goal},
                    expected_outputs=("implementation", "change_summary"),
                    required_permissions=("read_workspace", "write_workspace"),
                    validation_commands=("git diff --check",),
                    retry_limit=1,
                    review_required=True,
                ),
                TaskSpec(
                    id="review",
                    title="Review the implementation",
                    role="reviewer",
                    required_capabilities=("review",),
                    preferred_capabilities=("security_review",),
                    dependencies=("build",),
                    inputs={"goal": clean_goal, "source_task": "build"},
                    expected_outputs=("review_decision", "findings"),
                    required_permissions=("read_workspace",),
                    review_required=False,
                ),
                TaskSpec(
                    id="test",
                    title="Validate the reviewed implementation",
                    role="tester",
                    required_capabilities=("testing",),
                    dependencies=("review",),
                    inputs={"goal": clean_goal, "source_task": "build"},
                    expected_outputs=("test_results",),
                    required_permissions=("read_workspace", "write_workspace"),
                    validation_commands=("python -m pytest", "ruff check ."),
                    retry_limit=1,
                ),
            ),
        )

    def load(self, path: Path | str) -> TaskPlan:
        data: Any = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("task file must contain a JSON object")
        if "tasks" in data:
            plan = TaskPlan.from_dict(data)
            self.validate(plan)
            return plan
        return self.plan(str(data.get("goal", "")))

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

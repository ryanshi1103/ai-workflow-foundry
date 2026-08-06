from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from flowfoundry.orchestration.models import AgentSpec, RiskLevel, TaskSpec
from flowfoundry.orchestration.planner import RuleBasedPlanner, high_risk_task
from flowfoundry.orchestration.registry import AgentRegistry, default_registry
from flowfoundry.orchestration.router import TaskRouter


class RegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = default_registry().synthetic()

    def test_default_agents_include_required_examples(self) -> None:
        self.assertEqual(
            {agent.id for agent in self.registry.list()},
            {
                "claude-architect",
                "codex-builder",
                "deepseek-reviewer",
                "local-tester",
            },
        )

    def test_capability_and_role_matching(self) -> None:
        task = TaskSpec(
            id="implementation",
            title="Implement",
            role="builder",
            required_capabilities=("implementation", "python"),
            required_permissions=("read_workspace", "write_workspace"),
        )
        self.assertEqual(self.registry.match(task).id, "codex-builder")

    def test_unavailable_provider_is_not_routed_by_default(self) -> None:
        task = TaskSpec(
            id="implementation",
            title="Implement",
            role="builder",
            required_capabilities=("implementation",),
        )
        with self.assertRaises(LookupError):
            default_registry().match(task)

    def test_concurrency_limit_is_enforced(self) -> None:
        task = TaskSpec(
            id="review",
            title="Review",
            role="reviewer",
            required_capabilities=("review",),
        )
        with self.assertRaises(LookupError):
            self.registry.match(task, {"deepseek-reviewer": 2})

    def test_permission_profile_is_enforced(self) -> None:
        task = TaskSpec(
            id="review-write",
            title="Review and write",
            role="reviewer",
            required_capabilities=("review",),
            required_permissions=("write_workspace",),
        )
        with self.assertRaises(LookupError):
            self.registry.match(task)

    def test_fallback_agent_is_used(self) -> None:
        fallback = AgentSpec(
            id="fallback",
            display_name="Fallback",
            provider="fake",
            role="builder",
            capabilities=("general",),
            command_template=("fake",),
            cost_class="free",
            concurrency_limit=1,
            permission_profile=("read_workspace",),
            context_limit=1000,
            availability=True,
            workspace_mode="isolated",
        )
        registry = AgentRegistry((fallback,))
        task = TaskSpec(
            id="special",
            title="Special",
            role="builder",
            required_capabilities=("missing",),
            fallback_agent="fallback",
        )
        self.assertEqual(registry.match(task).id, "fallback")


class PlannerAndRouterTests(unittest.TestCase):
    def test_rule_plan_has_dependency_order(self) -> None:
        plan = RuleBasedPlanner().plan("Add a safe local workflow")
        self.assertEqual([task.id for task in plan.tasks], ["build", "review", "test"])
        self.assertEqual(plan.tasks[1].dependencies, ("build",))
        self.assertEqual(plan.tasks[2].dependencies, ("review",))

    def test_explicit_plan_round_trip(self) -> None:
        planner = RuleBasedPlanner()
        original = planner.plan("Round trip")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "task.json"
            path.write_text(json.dumps(original.to_dict()), encoding="utf-8")
            loaded = planner.load(path)
        self.assertEqual(loaded, original)

    def test_invalid_dependency_order_is_rejected(self) -> None:
        planner = RuleBasedPlanner()
        data = {
            "schema_version": 1,
            "goal": "bad",
            "tasks": [
                {
                    "id": "first",
                    "title": "First",
                    "role": "builder",
                    "required_capabilities": ["implementation"],
                    "dependencies": ["later"],
                },
                {
                    "id": "later",
                    "title": "Later",
                    "role": "builder",
                    "required_capabilities": ["implementation"],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dependency order"):
                planner.load(path)

    def test_router_uses_registry(self) -> None:
        task = RuleBasedPlanner().plan("Route").tasks[0]
        routed = TaskRouter(default_registry().synthetic()).route(task)
        self.assertEqual(routed.id, "codex-builder")

    def test_high_risk_helper_marks_approval(self) -> None:
        task = high_risk_task("release", "Release", "release")
        self.assertEqual(task.risk_level, RiskLevel.HIGH)
        self.assertEqual(task.approval_requirements, ("release",))


if __name__ == "__main__":
    unittest.main()

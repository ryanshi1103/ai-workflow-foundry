from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from flowfoundry.orchestration.discovery import ProviderDiscovery
from flowfoundry.orchestration.models import (
    AgentSpec,
    ExecutionMode,
    RiskLevel,
    TaskSpec,
)
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

    def test_registry_exposes_v1_capability_and_runtime_metadata(self) -> None:
        agent = self.registry.get("codex-builder")
        self.assertEqual(agent.model, "configured-by-codex-cli")
        self.assertEqual(agent.mode, "native_cli")
        self.assertIn("git", agent.tools)
        self.assertGreaterEqual(agent.coding_ability, 1)
        self.assertGreaterEqual(agent.reasoning_ability, 1)
        self.assertEqual(agent.privacy_level, "remote-provider")

    def test_provider_discovery_reports_state_without_secret_values(self) -> None:
        installed = {"codex": "/bin/codex", "python": "/bin/python"}
        commands: list[tuple[tuple[str, ...], float]] = []

        def logged_in(
            command: tuple[str, ...], timeout_seconds: float
        ) -> subprocess.CompletedProcess[str]:
            commands.append((command, timeout_seconds))
            return subprocess.CompletedProcess(
                command, 0, stdout="Logged in using ChatGPT\n", stderr=""
            )

        discovery = ProviderDiscovery(
            default_registry(),
            executable_lookup=installed.get,
            environ={"OPENAI_API_KEY": "synthetic-secret-value"},
            command_runner=logged_in,
        )
        statuses = {status.agent_id: status for status in discovery.inspect()}
        self.assertEqual(statuses["codex-builder"].authentication_state, "verified")
        self.assertEqual(statuses["codex-builder"].readiness, "READY")
        self.assertEqual(statuses["deepseek-reviewer"].availability, "unavailable")
        self.assertEqual(statuses["local-tester"].authentication_state, "not_required")
        self.assertEqual(statuses["local-tester"].readiness, "READY")
        self.assertEqual(commands[0][0], ("/bin/codex", "login", "status"))
        serialized = json.dumps([status.to_dict() for status in statuses.values()])
        self.assertNotIn("synthetic-secret-value", serialized)
        discovered = discovery.registry()
        self.assertTrue(discovered.get("codex-builder").availability)
        self.assertEqual(discovered.get("codex-builder").readiness, "READY")
        self.assertFalse(discovered.get("deepseek-reviewer").availability)

    def test_codex_not_logged_in_is_not_ready(self) -> None:
        discovery = ProviderDiscovery(
            default_registry(),
            executable_lookup={"codex": "/bin/codex"}.get,
            environ={},
            command_runner=lambda command, timeout: subprocess.CompletedProcess(
                command, 1, stdout="Not logged in", stderr=""
            ),
        )
        status = {item.agent_id: item for item in discovery.inspect()}["codex-builder"]
        self.assertEqual(status.authentication_state, "not_authenticated")
        self.assertEqual(status.availability, "available_unverified")
        self.assertEqual(status.readiness, "AVAILABLE_UNVERIFIED")
        self.assertEqual(status.setup_action, "run `codex login` to authenticate")

    def test_codex_unknown_login_output_is_unverified(self) -> None:
        discovery = ProviderDiscovery(
            default_registry(),
            executable_lookup={"codex": "/bin/codex"}.get,
            environ={},
            command_runner=lambda command, timeout: subprocess.CompletedProcess(
                command, 0, stdout="session state unavailable", stderr=""
            ),
        )
        status = {item.agent_id: item for item in discovery.inspect()}["codex-builder"]
        self.assertEqual(status.authentication_state, "unverified")
        self.assertEqual(status.readiness, "AVAILABLE_UNVERIFIED")

    def test_codex_login_timeout_is_unverified(self) -> None:
        def timeout(command: tuple[str, ...], seconds: float) -> subprocess.CompletedProcess[str]:
            raise subprocess.TimeoutExpired(command, seconds)

        discovery = ProviderDiscovery(
            default_registry(),
            executable_lookup={"codex": "/bin/codex"}.get,
            environ={},
            command_runner=timeout,
            auth_timeout_seconds=0.2,
        )
        status = {item.agent_id: item for item in discovery.inspect()}["codex-builder"]
        self.assertEqual(status.authentication_state, "unverified")
        self.assertEqual(status.readiness, "AVAILABLE_UNVERIFIED")

    def test_missing_codex_runtime_does_not_run_auth_probe(self) -> None:
        calls: list[tuple[str, ...]] = []

        def unexpected(
            command: tuple[str, ...], timeout_seconds: float
        ) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            raise AssertionError("auth probe must not run without an executable")

        discovery = ProviderDiscovery(
            default_registry(),
            executable_lookup=lambda executable: None,
            environ={},
            command_runner=unexpected,
        )
        status = {item.agent_id: item for item in discovery.inspect()}["codex-builder"]
        self.assertEqual(status.readiness, "UNAVAILABLE")
        self.assertEqual(status.availability, "unavailable")
        self.assertEqual(calls, [])

    def test_unverified_codex_is_not_routed_for_real_execution(self) -> None:
        registry = ProviderDiscovery(
            default_registry(),
            executable_lookup={"codex": "/bin/codex"}.get,
            environ={},
            command_runner=lambda command, timeout: subprocess.CompletedProcess(
                command, 0, stdout="unknown", stderr=""
            ),
        ).registry()
        task = TaskSpec(
            id="implementation",
            title="Implement",
            role="builder",
            required_capabilities=("implementation",),
        )
        with self.assertRaises(LookupError):
            registry.match(task)

    def test_verified_codex_is_routed_for_real_execution(self) -> None:
        registry = ProviderDiscovery(
            default_registry(),
            executable_lookup={"codex": "/bin/codex"}.get,
            environ={},
            command_runner=lambda command, timeout: subprocess.CompletedProcess(
                command, 0, stdout="Authenticated", stderr=""
            ),
        ).registry()
        task = TaskSpec(
            id="implementation",
            title="Implement",
            role="builder",
            required_capabilities=("implementation",),
        )
        self.assertEqual(registry.match(task).id, "codex-builder")

    def test_discovered_local_provider_remains_ready_without_authentication(self) -> None:
        registry = ProviderDiscovery(
            default_registry(),
            executable_lookup={"python": "/bin/python"}.get,
            environ={},
            command_runner=lambda command, timeout: subprocess.CompletedProcess(
                command, 0, stdout="", stderr=""
            ),
        ).registry()
        task = TaskSpec(
            id="test",
            title="Test",
            role="tester",
            required_capabilities=("testing",),
            required_permissions=("read_workspace", "write_workspace"),
        )
        self.assertEqual(registry.match(task).id, "local-tester")

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

    def test_role_is_a_preference_not_a_provider_lock(self) -> None:
        generalist = AgentSpec(
            id="generalist",
            display_name="Generalist",
            provider="compatible",
            role="generalist",
            capabilities=("review",),
            command_template=("compatible",),
            cost_class="free",
            concurrency_limit=1,
            permission_profile=("read_workspace",),
            context_limit=1000,
            availability=True,
            workspace_mode="read_only",
        )
        registry = AgentRegistry((generalist,))
        task = TaskSpec(
            id="review",
            title="Review",
            role="reviewer",
            required_capabilities=("review",),
        )
        self.assertEqual(registry.match(task).id, "generalist")

    def test_sufficient_history_can_prefer_reliability_over_call_price(self) -> None:
        def candidate(agent_id: str, cost_class: str) -> AgentSpec:
            return AgentSpec(
                id=agent_id,
                display_name=agent_id,
                provider="compatible",
                role="builder",
                capabilities=("implementation",),
                command_template=("compatible",),
                cost_class=cost_class,
                concurrency_limit=1,
                permission_profile=("read_workspace",),
                context_limit=1000,
                availability=True,
                workspace_mode="shared",
            )

        registry = AgentRegistry((candidate("cheap", "free"), candidate("reliable", "high")))
        task = TaskSpec(
            id="build",
            title="Build",
            role="builder",
            required_capabilities=("implementation",),
        )
        self.assertEqual(registry.match(task).id, "cheap")
        self.assertEqual(
            registry.match(task, history_scores={"cheap": 0.2, "reliable": 1.0}).id,
            "reliable",
        )

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
    def test_simple_goal_uses_one_agent(self) -> None:
        plan = RuleBasedPlanner().plan("Add a safe local workflow")
        self.assertEqual([task.id for task in plan.tasks], ["build"])
        self.assertEqual(plan.routing_decision.mode, ExecutionMode.SINGLE_AGENT)
        self.assertEqual(plan.routing_decision.estimated_agent_calls, 1)

    def test_risky_goal_adds_only_an_independent_reviewer(self) -> None:
        plan = RuleBasedPlanner().plan(
            "Update authentication code",
            profile_overrides={"complexity": 2, "uncertainty": 1},
        )
        self.assertEqual([task.id for task in plan.tasks], ["build", "review"])
        self.assertEqual(plan.routing_decision.mode, ExecutionMode.SINGLE_AGENT_REVIEWER)
        self.assertEqual(plan.tasks[1].dependencies, ("build",))

    def test_complex_cross_domain_goal_uses_bounded_team(self) -> None:
        plan = RuleBasedPlanner().plan(
            "Research and implement a new architecture",
            profile_overrides={"complexity": 5, "uncertainty": 4},
        )
        self.assertEqual(
            [task.id for task in plan.tasks],
            ["architect", "build", "review", "test"],
        )
        self.assertEqual(plan.routing_decision.mode, ExecutionMode.MULTI_AGENT)
        self.assertEqual(plan.routing_decision.estimated_agent_calls, 4)
        self.assertEqual(plan.tasks[1].dependencies, ("architect",))
        self.assertEqual(plan.tasks[2].dependencies, ("build",))
        self.assertEqual(plan.tasks[3].dependencies, ("review",))

    def test_operator_can_force_a_bounded_mode(self) -> None:
        plan = RuleBasedPlanner().plan("Document a setting", execution_mode="multi_agent")
        self.assertEqual(plan.routing_decision.mode, ExecutionMode.MULTI_AGENT)
        self.assertEqual([task.id for task in plan.tasks], ["architect", "build", "review"])

    def test_architecture_goal_uses_team_without_needing_magic_provider_names(self) -> None:
        plan = RuleBasedPlanner().plan("Design the system architecture")
        self.assertEqual(plan.routing_decision.mode, ExecutionMode.MULTI_AGENT)
        self.assertEqual([task.role for task in plan.tasks], ["architect", "builder", "reviewer"])

    def test_explicit_plan_round_trip(self) -> None:
        planner = RuleBasedPlanner()
        original = planner.plan("Round trip")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "task.json"
            path.write_text(json.dumps(original.to_dict()), encoding="utf-8")
            loaded = planner.load(path)
        self.assertEqual(loaded, original)

    def test_goal_file_accepts_profile_overrides(self) -> None:
        data = {
            "goal": "Document a critical release process",
            "profile": {"failure_risk": 4, "expected_quality": 5},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "goal.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            loaded = RuleBasedPlanner().load(path)
        self.assertEqual(loaded.routing_decision.mode, ExecutionMode.SINGLE_AGENT_REVIEWER)
        self.assertEqual(loaded.task_profile.failure_risk, 4)

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

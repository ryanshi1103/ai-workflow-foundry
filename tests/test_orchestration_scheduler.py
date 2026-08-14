from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from flowfoundry.orchestration.aggregator import ResultAggregator
from flowfoundry.orchestration.approvals import ApprovalGate
from flowfoundry.orchestration.models import (
    AgentSpec,
    ProviderResult,
    ReviewDecision,
    RiskLevel,
    TaskPlan,
    TaskSpec,
    TaskStatus,
    UsageMetrics,
)
from flowfoundry.orchestration.memory import AgentPerformanceMemory
from flowfoundry.orchestration.planner import RuleBasedPlanner
from flowfoundry.orchestration.execution import ManagedProcessResult
from flowfoundry.orchestration.providers import FakeProvider, LocalCommandProvider
from flowfoundry.orchestration.recovery import RecoveryManager
from flowfoundry.orchestration.registry import default_registry
from flowfoundry.orchestration.router import TaskRouter
from flowfoundry.orchestration.scheduler import RunScheduler
from flowfoundry.orchestration.workspace import RunWorkspace


class SchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "runs"
        self.plan = RuleBasedPlanner().plan(
            "Implement offline collaboration",
            execution_mode="multi_agent",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_plan(self, provider: FakeProvider, plan: TaskPlan | None = None) -> RunWorkspace:
        active_plan = plan or self.plan
        workspace = RunWorkspace.create(self.root, "test-run", active_plan)
        scheduler = RunScheduler(
            TaskRouter(default_registry().synthetic()),
            provider,
            max_workers=3,
        )
        scheduler.run(workspace)
        return workspace

    def test_synthetic_builder_reviewer_tester_end_to_end(self) -> None:
        workspace = self.run_plan(FakeProvider())
        manifest = workspace.manifest()
        self.assertEqual(manifest["status"], "completed")
        self.assertTrue(
            all(state["status"] == TaskStatus.COMPLETED.value for state in manifest["tasks"].values())
        )
        report = ResultAggregator().aggregate(workspace)
        self.assertEqual(report["completed_tasks"], ["build", "review", "test"])
        self.assertFalse(report["human_actions_required"])
        self.assertEqual(
            report["usage"],
            {
                "provider_calls": 3,
                "input_tokens": 0,
                "output_tokens": 0,
                "latency_ms": 0,
                "estimated_cost_usd": 0.0,
                "token_status": "measured",
                "cost_status": "measured",
            },
        )
        memory = json.loads(
            workspace.performance_memory_path.read_text(encoding="utf-8")
        )
        self.assertEqual(memory["agents"]["codex-builder"]["executions"], 1)
        self.assertEqual(memory["agents"]["codex-builder"]["categories"]["coding"]["successes"], 1)

    def test_retry_succeeds_within_limit(self) -> None:
        provider = FakeProvider(failures_before_success={"build": 1})
        workspace = self.run_plan(provider)
        self.assertEqual(provider.calls["build"], 2)
        self.assertEqual(workspace.manifest()["tasks"]["build"]["status"], "completed")
        self.assertEqual(
            workspace.manifest()["tasks"]["build"]["usage"]["provider_calls"],
            2,
        )

    def test_usage_metrics_reject_invented_negative_values(self) -> None:
        with self.assertRaises(ValueError):
            UsageMetrics(input_tokens=-1)

    def test_real_routing_scores_exclude_mock_experience(self) -> None:
        path = self.root / "performance.json"
        memory = AgentPerformanceMemory(path)
        agent = default_registry().synthetic().get("codex-builder")
        task = RuleBasedPlanner().plan("Implement one code fix").tasks[0]
        usage = {"provider_calls": 1, "latency_ms": 1}
        for _ in range(3):
            memory.record(
                agent,
                task,
                ProviderResult(False, "mock failure"),
                usage,
                "coding",
                execution_kind="mock",
            )
        memory.record(
            agent,
            task,
            ProviderResult(True, "real success"),
            usage,
            "coding",
            execution_kind="real",
        )

        self.assertEqual(
            memory.routing_scores(minimum_samples=1, execution_kind="mock")[agent.id],
            0.0,
        )
        self.assertEqual(
            memory.routing_scores(minimum_samples=1, execution_kind="real")[agent.id],
            1.0,
        )

    def test_local_command_provider_executes_in_shared_project_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "project"
            task_dir = Path(temp_dir) / "run" / "task"
            project_root.mkdir()
            task_dir.mkdir(parents=True)
            agent = AgentSpec(
                id="cwd-probe",
                display_name="CWD Probe",
                provider="local",
                role="builder",
                capabilities=("implementation",),
                command_template=(sys.executable, "-c", "import os; print(os.getcwd())"),
                cost_class="free",
                concurrency_limit=1,
                permission_profile=("read_workspace",),
                context_limit=1000,
                availability=True,
                workspace_mode="shared",
                local=True,
            )
            task = TaskSpec(
                id="probe",
                title="Probe",
                role="builder",
                required_capabilities=("implementation",),
            )
            result = LocalCommandProvider(enabled=True).execute(
                task,
                agent,
                task_dir,
                project_root,
            )
            self.assertTrue(result.success)
            self.assertEqual(result.outputs["stdout"].strip(), str(project_root))
            self.assertIsNotNone(result.usage.latency_ms)

    def test_codex_adapter_uses_stdin_schema_and_structured_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "project"
            task_dir = Path(temp_dir) / "run" / "tasks" / "build"
            project_root.mkdir()
            task_dir.mkdir(parents=True)
            task = RuleBasedPlanner().plan("Implement one code fix").tasks[0]
            agent = default_registry().synthetic().get("codex-builder")

            def complete(command: list[str], **kwargs: object) -> object:
                schema_path = Path(command[command.index("--output-schema") + 1])
                schema = json.loads(schema_path.read_text(encoding="utf-8"))

                def assert_strict_objects(node: object) -> None:
                    if isinstance(node, dict):
                        if node.get("type") == "object":
                            self.assertIs(node.get("additionalProperties"), False)
                            properties = node.get("properties", {})
                            self.assertEqual(set(node.get("required", [])), set(properties))
                        for value in node.values():
                            assert_strict_objects(value)
                    elif isinstance(node, list):
                        for value in node:
                            assert_strict_objects(value)

                assert_strict_objects(schema)
                output_path = Path(command[command.index("--output-last-message") + 1])
                output_path.write_text(
                    '{"success":true,"summary":"done","outputs":{'
                    '"details":"fixed","artifact_refs":[]},"review":null,'
                    '"findings":[],"contribution":null}',
                    encoding="utf-8",
                )
                return ManagedProcessResult(
                    0,
                    "",
                    "",
                    "executions/test/execution.json",
                    "completed",
                    False,
                    False,
                    False,
                    {"status": "completed", "exit_code": 0},
                )

            with patch.object(LocalCommandProvider, "_execute_managed", side_effect=complete) as run:
                result = LocalCommandProvider(enabled=True).execute(
                    task,
                    agent,
                    task_dir,
                    project_root,
                )
            self.assertTrue(result.success)
            command = run.call_args.args[0]
            self.assertIn("--output-schema", command)
            self.assertEqual(command[-1], "-")
            self.assertIn("FlowFoundry task", run.call_args.kwargs["input_text"])
            self.assertEqual(run.call_args.kwargs["project_root"], project_root)
            self.assertEqual(result.outputs["request_metrics_ref"], "provider-request-metrics.json")

    def test_native_request_metrics_are_safe_exact_and_written_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_root = Path(temp_dir) / "run"
            project_root = Path(temp_dir) / "project"
            task_dir = run_root / "tasks" / "build"
            dependency_dir = run_root / "tasks" / "source"
            project_root.mkdir()
            task_dir.mkdir(parents=True)
            dependency_dir.mkdir(parents=True)
            sentinel = "UNIQUE_SECRET_LIKE_SENTINEL_9f4a"
            (dependency_dir / "result.json").write_text(
                json.dumps({"content": sentinel}), encoding="utf-8"
            )
            task = TaskSpec(
                id="build",
                title="Unicode 修复 🛠️",
                role="builder",
                required_capabilities=("implementation",),
                dependencies=("source",),
                inputs={"instruction": f"Do not persist {sentinel}"},
            )
            agent = default_registry().synthetic().get("codex-builder")
            expected_prompt = LocalCommandProvider._task_prompt(task, task_dir)

            def complete(command: list[str], **kwargs: object) -> ManagedProcessResult:
                metrics_path = task_dir / "provider-request-metrics.json"
                self.assertTrue(metrics_path.is_file())
                self.assertEqual(kwargs["input_text"], expected_prompt)
                output_path = Path(command[command.index("--output-last-message") + 1])
                output_path.write_text(
                    '{"success":true,"summary":"done","outputs":{"details":null,'
                    '"artifact_refs":[]},"review":null,"findings":[],"contribution":null}',
                    encoding="utf-8",
                )
                return ManagedProcessResult(
                    0, "", "", "executions/test/execution.json", "completed",
                    False, False, False, {"status": "completed", "exit_code": 0},
                )

            with patch.object(LocalCommandProvider, "_execute_managed", side_effect=complete):
                result = LocalCommandProvider(enabled=True).execute(
                    task, agent, task_dir, project_root
                )

            metrics_text = (task_dir / "provider-request-metrics.json").read_text(
                encoding="utf-8"
            )
            metrics = json.loads(metrics_text)
            self.assertNotIn(sentinel, metrics_text)
            self.assertNotIn("Unicode", metrics_text)
            self.assertEqual(metrics["prompt_chars"], len(expected_prompt))
            self.assertEqual(metrics["prompt_bytes"], len(expected_prompt.encode("utf-8")))
            self.assertGreater(metrics["prompt_bytes"], metrics["prompt_chars"])
            self.assertEqual(metrics["dependency_artifact_count"], 1)
            self.assertIs(metrics["tokens_comparable"], False)
            self.assertEqual(result.outputs["request_metrics_ref"], "provider-request-metrics.json")

    def test_native_failures_preserve_request_metrics_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "project"
            task_dir = Path(temp_dir) / "run" / "tasks" / "build"
            project_root.mkdir()
            task_dir.mkdir(parents=True)
            task = RuleBasedPlanner().plan("Implement one code fix").tasks[0]
            agent = default_registry().synthetic().get("codex-builder")
            cases = (
                ManagedProcessResult(2, "", "failed", "exec.json", "completed", False, False, False, {}),
                ManagedProcessResult(None, "", "", "exec.json", "timed_out", True, False, True, {}),
                ManagedProcessResult(None, "partial", "", "exec.json", "cancelled", False, True, True, {}),
                ManagedProcessResult(None, "", "", "exec.json", "cancel_unverified", False, False, True, {}),
            )
            for completed in cases:
                with self.subTest(state=completed.state), patch.object(
                    LocalCommandProvider, "_execute_managed", return_value=completed
                ):
                    result = LocalCommandProvider(enabled=True).execute(
                        task, agent, task_dir, project_root
                    )
                self.assertEqual(
                    result.outputs["request_metrics_ref"], "provider-request-metrics.json"
                )

    def test_deepseek_adapter_reuses_isolated_claude_runtime_and_parses_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "project"
            task_dir = Path(temp_dir) / "run" / "tasks" / "review"
            project_root.mkdir()
            task_dir.mkdir(parents=True)
            task = TaskSpec(
                id="review",
                title="Review",
                role="reviewer",
                required_capabilities=("review",),
            )
            agent = default_registry().synthetic().get("deepseek-reviewer")
            wrapper = {
                "structured_output": {
                    "success": True,
                    "summary": "approved",
                    "outputs": {},
                    "review": "APPROVED",
                    "findings": [],
                },
                "usage": {"input_tokens": 12, "output_tokens": 4},
                "total_cost_usd": 0.002,
            }
            completed = ManagedProcessResult(
                0,
                json.dumps(wrapper),
                "",
                "executions/test/execution.json",
                "completed",
                False,
                False,
                False,
                {"status": "completed", "exit_code": 0},
            )
            with patch(
                "flowfoundry.orchestration.providers.LocalCommandProvider._execute_managed",
                return_value=completed,
            ) as run:
                result = LocalCommandProvider(enabled=True).execute(
                    task,
                    agent,
                    task_dir,
                    project_root,
                )
            self.assertEqual(result.review, ReviewDecision.APPROVED)
            self.assertEqual(result.usage.input_tokens, 12)
            self.assertEqual(result.usage.estimated_cost_usd, 0.002)
            command = run.call_args.args[0]
            self.assertEqual(command[0], "claude")
            self.assertIn("--json-schema", command)
            self.assertIn(".claude-deepseek", run.call_args.kwargs["env"]["CLAUDE_CONFIG_DIR"])

    def test_claude_provider_cannot_execute_through_deepseek_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "project"
            task_dir = Path(temp_dir) / "run" / "tasks" / "architecture"
            project_root.mkdir()
            task_dir.mkdir(parents=True)
            task = TaskSpec(
                id="architecture",
                title="Architect",
                role="architect",
                required_capabilities=("architecture",),
            )
            agent = replace(
                default_registry().synthetic().get("claude-architect"),
                runtime_profile="deepseek_compatible",
            )

            with patch.object(LocalCommandProvider, "_execute_managed") as run:
                result = LocalCommandProvider(enabled=True).execute(
                    task,
                    agent,
                    task_dir,
                    project_root,
                )

            self.assertFalse(result.success)
            self.assertEqual(result.summary, "PROVIDER_PROFILE_MISMATCH")
            self.assertEqual(
                result.outputs["error_code"], "PROVIDER_PROFILE_MISMATCH"
            )
            run.assert_not_called()

    def test_blocked_review_blocks_source_and_skips_test(self) -> None:
        provider = FakeProvider(reviews={"review": ReviewDecision.BLOCKED})
        workspace = self.run_plan(provider)
        states = workspace.manifest()["tasks"]
        self.assertEqual(states["build"]["status"], TaskStatus.BLOCKED.value)
        self.assertEqual(states["review"]["status"], TaskStatus.BLOCKED.value)
        self.assertEqual(states["test"]["status"], TaskStatus.SKIPPED.value)
        review = workspace.read_json("reviews/review.json")
        self.assertEqual(review["decision"], "BLOCKED")
        self.assertIn("commit", review)
        self.assertIn("tests", review)

    def test_review_pending_stops_dependent_test(self) -> None:
        provider = FakeProvider(reviews={"review": ReviewDecision.REVIEW_PENDING})
        workspace = self.run_plan(provider)
        manifest = workspace.manifest()
        self.assertEqual(manifest["status"], "review_pending")
        self.assertEqual(manifest["tasks"]["test"]["status"], TaskStatus.PENDING.value)

    def test_approved_with_notes_allows_validation(self) -> None:
        provider = FakeProvider(reviews={"review": ReviewDecision.APPROVED_WITH_NOTES})
        workspace = self.run_plan(provider)
        self.assertEqual(workspace.manifest()["status"], "completed")

    def test_high_risk_task_is_skipped_without_waiting(self) -> None:
        plan = TaskPlan(
            "Deploy",
            (
                TaskSpec(
                    id="deploy",
                    title="Deploy",
                    role="builder",
                    required_capabilities=("implementation",),
                    risk_level=RiskLevel.HIGH,
                    approval_requirements=("deployment",),
                ),
            ),
        )
        workspace = self.run_plan(FakeProvider(), plan)
        self.assertEqual(
            workspace.manifest()["tasks"]["deploy"]["status"],
            TaskStatus.SKIPPED_PENDING_HUMAN.value,
        )
        self.assertTrue(workspace.contained("HUMAN_ACTIONS_REQUIRED.md").exists())

    def test_missing_provider_enters_setup_flow_instead_of_crashing(self) -> None:
        plan = RuleBasedPlanner().plan("Implement one small code change")
        workspace = RunWorkspace.create(self.root, "provider-setup", plan)
        scheduler = RunScheduler(TaskRouter(default_registry()), FakeProvider())
        scheduler.run(workspace)
        manifest = workspace.manifest()
        self.assertEqual(manifest["status"], "completed_with_blockers")
        self.assertEqual(manifest["tasks"]["build"]["status"], TaskStatus.BLOCKED.value)
        setup = workspace.read_json("provider-setup/build.json")
        self.assertEqual(setup["status"], "setup_required")
        self.assertEqual(setup["candidates"][0]["agent_id"], "codex-builder")
        self.assertEqual(setup["candidates"][0]["runtime_profile"], "codex_native")
        self.assertEqual(
            setup["candidates"][0]["provider_identity_state"], "unverified"
        )
        self.assertNotIn("credential_value", setup["candidates"][0])
        self.assertTrue(workspace.contained("HUMAN_ACTIONS_REQUIRED.md").exists())


class RecoveryTests(unittest.TestCase):
    def test_resume_blocks_running_task_without_terminal_or_process_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = RuleBasedPlanner().plan("Recover", execution_mode="single_agent_reviewer")
            workspace = RunWorkspace.create(Path(temp_dir), "recover", plan)
            workspace.update_task("build", status=TaskStatus.COMPLETED.value)
            workspace.update_task("review", status=TaskStatus.RUNNING.value)
            RecoveryManager().recover_interrupted(workspace)
            manifest = workspace.manifest()
            states = manifest["tasks"]
            self.assertEqual(states["build"]["status"], TaskStatus.COMPLETED.value)
            self.assertEqual(states["review"]["status"], TaskStatus.RUNNING.value)
            self.assertEqual(manifest["status"], "reconciliation_blocked")
            self.assertFalse(manifest["recovery_decision"]["resume_execution"])

    def test_reconcile_does_not_repeat_unchanged_completed_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            planner = RuleBasedPlanner()
            plan = planner.plan("Stable")
            workspace = RunWorkspace.create(Path(temp_dir), "stable", plan)
            workspace.update_task("build", status=TaskStatus.COMPLETED.value)
            RecoveryManager().reconcile_plan(workspace, plan)
            self.assertEqual(
                workspace.manifest()["tasks"]["build"]["status"],
                TaskStatus.COMPLETED.value,
            )

    def test_changed_input_resets_task_and_dependents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            planner = RuleBasedPlanner()
            original = planner.plan("Original")
            workspace = RunWorkspace.create(Path(temp_dir), "changed", original)
            for task in original.tasks:
                workspace.update_task(task.id, status=TaskStatus.COMPLETED.value)
            changed_build = replace(original.tasks[0], inputs={"goal": "Changed"})
            changed = TaskPlan("Changed", (changed_build, *original.tasks[1:]))
            RecoveryManager().reconcile_plan(workspace, changed)
            states = workspace.manifest()["tasks"]
            self.assertTrue(all(state["status"] == "pending" for state in states.values()))

    def test_approved_gated_task_and_skipped_dependent_can_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = TaskPlan(
                "Approval chain",
                (
                    TaskSpec(
                        id="prepare",
                        title="Prepare",
                        role="builder",
                        required_capabilities=("implementation",),
                    ),
                    TaskSpec(
                        id="release",
                        title="Release",
                        role="builder",
                        required_capabilities=("implementation",),
                        dependencies=("prepare",),
                        risk_level=RiskLevel.HIGH,
                        approval_requirements=("release",),
                    ),
                    TaskSpec(
                        id="finish",
                        title="Finish",
                        role="tester",
                        required_capabilities=("testing",),
                        dependencies=("release",),
                    ),
                ),
            )
            workspace = RunWorkspace.create(Path(temp_dir), "approval-chain", plan)
            scheduler = RunScheduler(
                TaskRouter(default_registry().synthetic()),
                FakeProvider(),
            )
            scheduler.run(workspace)
            first_states = workspace.manifest()["tasks"]
            self.assertEqual(
                first_states["release"]["status"],
                TaskStatus.SKIPPED_PENDING_HUMAN.value,
            )
            self.assertEqual(first_states["finish"]["status"], TaskStatus.SKIPPED.value)

            ApprovalGate().record_approval(
                workspace,
                "release",
                ("release",),
                "test-operator",
            )
            recovered = RecoveryManager().retry_failed_task(workspace, "release")
            self.assertEqual(recovered["revived_tasks"], ["finish", "release"])
            self.assertEqual(recovered["tasks"]["finish"]["status"], TaskStatus.PENDING.value)

            scheduler.run(workspace)
            final_states = workspace.manifest()["tasks"]
            self.assertEqual(workspace.manifest()["status"], "completed")
            self.assertTrue(
                all(state["status"] == TaskStatus.COMPLETED.value for state in final_states.values())
            )


if __name__ == "__main__":
    unittest.main()

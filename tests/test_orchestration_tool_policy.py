from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from flowfoundry.orchestration.execution import ManagedProcessResult
from flowfoundry.orchestration.models import TaskPlan, TaskSpec
from flowfoundry.orchestration.providers import LocalCommandProvider
from flowfoundry.orchestration.registry import default_registry
from flowfoundry.orchestration.router import TaskRouter
from flowfoundry.orchestration.scheduler import RunScheduler
from flowfoundry.orchestration.tool_policy import (
    ProtocolTool,
    TaskToolRequirement,
    ToolCapability,
    ToolObservation,
    ToolPolicyMode,
    ToolPolicyStore,
    TranslationStatus,
    build_tool_policy,
    provider_tool_exposure,
)
from flowfoundry.orchestration.workspace import RunWorkspace


def minimum_task(requirement: str, *, task_id: str = "task") -> TaskSpec:
    inputs = (
        {"exact_file_path": "FACT.txt"}
        if requirement == TaskToolRequirement.READ_EXACT_FILE.value
        else {}
    )
    return TaskSpec(
        id=task_id,
        title="Bounded task",
        role="reviewer",
        required_capabilities=("review",),
        inputs=inputs,
        retry_limit=0,
        tool_requirement=requirement,
        tool_policy_mode=ToolPolicyMode.MINIMUM_SUFFICIENT.value,
    )


class ToolPolicyUnitTests(unittest.TestCase):
    def test_no_external_action_maps_to_no_task_tools(self) -> None:
        policy = build_tool_policy(
            minimum_task(TaskToolRequirement.NO_EXTERNAL_ACTION.value), "deepseek"
        )
        exposure = provider_tool_exposure(policy)

        self.assertTrue(policy.policy_applied)
        self.assertTrue(policy.coverage)
        self.assertEqual(policy.required_capabilities, ("NO_EXTERNAL_ACTION",))
        self.assertEqual(policy.task_tools, ())
        self.assertEqual(exposure.cli_args, ("--tools", ""))

    def test_read_exact_file_maps_to_provider_independent_read_file(self) -> None:
        policy = build_tool_policy(
            minimum_task(TaskToolRequirement.READ_EXACT_FILE.value), "deepseek"
        )
        exposure = provider_tool_exposure(policy)

        self.assertEqual(policy.task_tools, (ToolCapability.READ_FILE.value,))
        self.assertEqual(exposure.cli_args, ("--tools", "Read"))
        self.assertNotIn("Read", policy.required_capabilities)

    def test_structured_output_is_protocol_only(self) -> None:
        policy = build_tool_policy(
            minimum_task(TaskToolRequirement.READ_EXACT_FILE.value), "claude"
        )

        self.assertEqual(policy.protocol_tools, (ProtocolTool.STRUCTURED_OUTPUT.value,))
        self.assertNotIn(ProtocolTool.STRUCTURED_OUTPUT.value, policy.task_tools)
        self.assertNotIn(
            ProtocolTool.STRUCTURED_OUTPUT.value, policy.required_capabilities
        )

    def test_unclassified_legacy_task_preserves_provider_default(self) -> None:
        task = TaskSpec(
            id="legacy",
            title="Legacy",
            role="builder",
            required_capabilities=("implementation",),
        )
        policy = build_tool_policy(task, "deepseek")

        self.assertFalse(policy.policy_applied)
        self.assertFalse(policy.coverage)
        self.assertEqual(policy.mode, ToolPolicyMode.PROVIDER_DEFAULT)
        self.assertEqual(policy.translation_status, TranslationStatus.PROVIDER_DEFAULT)
        self.assertEqual(provider_tool_exposure(policy).cli_args, ())
        self.assertNotIn("tool_policy_mode", task.to_dict())
        self.assertNotIn("tool_requirement", task.to_dict())

    def test_unsupported_capability_fails_closed(self) -> None:
        policy = build_tool_policy(minimum_task("WRITE_FILE"), "deepseek")

        self.assertFalse(policy.runnable)
        self.assertEqual(policy.mode, ToolPolicyMode.UNSUPPORTED)
        self.assertEqual(policy.reason, "TOOL_POLICY_UNSUPPORTED_CAPABILITY")
        self.assertEqual(provider_tool_exposure(policy).cli_args, ())

    def test_read_exact_file_without_exact_path_fails_closed(self) -> None:
        task = replace(
            minimum_task(TaskToolRequirement.READ_EXACT_FILE.value), inputs={}
        )
        policy = build_tool_policy(task, "deepseek")

        self.assertFalse(policy.runnable)
        self.assertEqual(policy.reason, "TOOL_POLICY_EXACT_PATH_REQUIRED")

    def test_unknown_provider_does_not_claim_translation(self) -> None:
        policy = build_tool_policy(
            minimum_task(TaskToolRequirement.READ_EXACT_FILE.value), "codex"
        )

        self.assertFalse(policy.runnable)
        self.assertEqual(policy.reason, "TOOL_POLICY_UNSUPPORTED_PROVIDER")

    def test_requested_exposed_and_executed_are_separate(self) -> None:
        observation = ToolObservation.from_events(
            exposed=("Read", "StructuredOutput"),
            requested=("Read", "Write"),
            executed=("Read",),
        )

        self.assertEqual(observation.tools_requested, ("Read", "Write"))
        self.assertEqual(observation.tools_executed, ("Read",))
        self.assertEqual(observation.unexpected_tool_requests, ("Write",))
        self.assertNotIn("Write", observation.tools_exposed)

    def test_durable_decision_is_reused_instead_of_reclassified(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task_dir = Path(temp_dir)
            store = ToolPolicyStore(task_dir)
            first, first_ref = store.resolve(
                minimum_task(TaskToolRequirement.READ_EXACT_FILE.value), "deepseek"
            )
            changed_task = minimum_task(TaskToolRequirement.NO_EXTERNAL_ACTION.value)
            second, second_ref = store.resolve(changed_task, "deepseek")

            self.assertEqual(first.policy.tool_exposure_fingerprint, second.policy.tool_exposure_fingerprint)
            self.assertEqual(second.cli_args, ("--tools", "Read"))
            self.assertEqual(first_ref, "tool-policy-attempt-0001.json")
            self.assertEqual(second_ref, "tool-policy-attempt-0002.json")
            self.assertEqual(
                json.loads((task_dir / second_ref).read_text())["decision_ref"],
                "tool-exposure-policy.json",
            )


class ToolPolicyProviderTests(unittest.TestCase):
    def test_claude_argv_and_permission_policy_are_independent(self) -> None:
        agent = default_registry().synthetic().get("deepseek-reviewer")
        read_task = minimum_task(TaskToolRequirement.READ_EXACT_FILE.value)
        exposure = provider_tool_exposure(build_tool_policy(read_task, "deepseek"))
        schema = Path("schema.json")
        result = Path("result.json")

        read_only = LocalCommandProvider._native_command(
            agent, read_task, schema, result, tool_exposure=exposure
        )
        writable = LocalCommandProvider._native_command(
            agent,
            replace(read_task, required_permissions=("read_workspace", "write_workspace")),
            schema,
            result,
            tool_exposure=exposure,
        )

        self.assertEqual(read_only[read_only.index("--tools") + 1], "Read")
        self.assertEqual(writable[writable.index("--tools") + 1], "Read")
        self.assertEqual(read_only[read_only.index("--permission-mode") + 1], "plan")
        self.assertEqual(
            writable[writable.index("--permission-mode") + 1], "acceptEdits"
        )

    def test_strict_unsupported_task_never_starts_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "project"
            task_dir = root / "run" / "tasks" / "task"
            project_root.mkdir()
            task_dir.mkdir(parents=True)
            agent = default_registry().synthetic().get("deepseek-reviewer")

            with patch.object(LocalCommandProvider, "_execute_managed") as execute:
                result = LocalCommandProvider(enabled=True).execute(
                    minimum_task("WRITE_FILE"), agent, task_dir, project_root
                )

            execute.assert_not_called()
            self.assertFalse(result.success)
            self.assertEqual(
                result.outputs["error_code"], "TOOL_POLICY_UNSUPPORTED_CAPABILITY"
            )
            self.assertEqual(result.usage.input_tokens, 0)

    def test_read_only_unexpected_write_is_recorded_without_policy_widening(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "project"
            task_dir = root / "run" / "tasks" / "task"
            project_root.mkdir()
            task_dir.mkdir(parents=True)
            agent = default_registry().synthetic().get("deepseek-reviewer")
            wrapper = {
                "structured_output": {
                    "success": True,
                    "summary": "read succeeded",
                    "outputs": {"details": "4729", "artifact_refs": []},
                    "review": None,
                    "findings": [],
                    "contribution": None,
                },
                "permission_denials": [{"tool_name": "Write"}],
                "usage": {"input_tokens": 10, "output_tokens": 2},
                "total_cost_usd": 0.001,
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

            with patch.object(
                LocalCommandProvider, "_execute_managed", return_value=completed
            ) as execute:
                result = LocalCommandProvider(enabled=True).execute(
                    minimum_task(TaskToolRequirement.READ_EXACT_FILE.value),
                    agent,
                    task_dir,
                    project_root,
                )

            command = execute.call_args.args[0]
            self.assertEqual(command[command.index("--tools") + 1], "Read")
            observation = result.outputs["tool_observation"]
            self.assertEqual(observation["tools_requested"], ["Write"])
            self.assertEqual(observation["tools_executed"], [])
            self.assertEqual(observation["unexpected_tool_requests"], ["Write"])
            self.assertEqual(
                result.outputs["tool_policy"]["effective_tool_count"], 2
            )
            durable = json.loads(
                (task_dir / "tool-exposure-policy.json").read_text(encoding="utf-8")
            )
            self.assertEqual(durable["effective_tool_names"], ["Read", "StructuredOutput"])

    def test_scheduler_retry_reuses_the_same_durable_exposure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            task = replace(
                minimum_task(TaskToolRequirement.READ_EXACT_FILE.value),
                retry_limit=1,
            )
            workspace = RunWorkspace.create(
                root / "runs",
                "retry-policy",
                TaskPlan("Read one exact file", (task,)),
                project_root=root,
            )
            failed = ManagedProcessResult(
                2, "", "transient", "executions/one.json", "completed",
                False, False, False, {"status": "completed", "exit_code": 2},
            )
            succeeded = ManagedProcessResult(
                0,
                json.dumps(
                    {
                        "structured_output": {
                            "success": True,
                            "summary": "read succeeded",
                            "outputs": {"details": "4729", "artifact_refs": []},
                            "review": None,
                            "findings": [],
                            "contribution": None,
                        },
                        "usage": {"input_tokens": 10, "output_tokens": 2},
                    }
                ),
                "",
                "executions/two.json",
                "completed",
                False,
                False,
                False,
                {"status": "completed", "exit_code": 0},
            )
            provider = LocalCommandProvider(enabled=True)

            with patch.object(
                provider, "_execute_managed", side_effect=(failed, succeeded)
            ) as execute:
                RunScheduler(
                    TaskRouter(default_registry().synthetic()), provider, max_workers=1
                ).run(workspace)

            self.assertEqual(execute.call_count, 2)
            commands = [call.args[0] for call in execute.call_args_list]
            self.assertEqual(
                [command[command.index("--tools") + 1] for command in commands],
                ["Read", "Read"],
            )
            task_dir = workspace.task_dir(task.id)
            attempts = sorted(task_dir.glob("tool-policy-attempt-*.json"))
            self.assertEqual(len(attempts), 2)
            fingerprints = {
                json.loads(path.read_text())["tool_exposure_fingerprint"]
                for path in attempts
            }
            self.assertEqual(len(fingerprints), 1)


if __name__ == "__main__":
    unittest.main()

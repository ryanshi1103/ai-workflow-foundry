from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flowfoundry.orchestration.meeting import MeetingRuntime
from flowfoundry.orchestration.models import (
    AgentSpec,
    MeetingBudget,
    MeetingState,
    ProviderResult,
    TaskPlan,
    TaskSpec,
    UsageMetrics,
)
from flowfoundry.orchestration.planner import RuleBasedPlanner
from flowfoundry.orchestration.providers import FakeProvider
from flowfoundry.orchestration.recovery import RecoveryManager
from flowfoundry.orchestration.registry import AgentRegistry, default_registry
from flowfoundry.orchestration.router import TaskRouter
from flowfoundry.orchestration.scheduler import RunScheduler
from flowfoundry.orchestration.workspace import RunWorkspace


class RecordingFakeProvider(FakeProvider):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.received: list[TaskSpec] = []

    def execute(
        self,
        task: TaskSpec,
        agent: AgentSpec,
        task_dir: Path,
        project_root: Path,
    ) -> ProviderResult:
        self.received.append(task)
        return super().execute(task, agent, task_dir, project_root)


class InterruptingProvider(RecordingFakeProvider):
    def __init__(self, phase: int, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.phase = phase
        self.interrupted = False

    def execute(
        self,
        task: TaskSpec,
        agent: AgentSpec,
        task_dir: Path,
        project_root: Path,
    ) -> ProviderResult:
        meeting_round = task.inputs.get("meeting_round")
        if meeting_round == self.phase and not self.interrupted:
            if self.phase == 1 and task.id != "review":
                return super().execute(task, agent, task_dir, project_root)
            self.interrupted = True
            raise KeyboardInterrupt("synthetic interruption")
        return super().execute(task, agent, task_dir, project_root)


class UnknownUsageProvider(RecordingFakeProvider):
    def execute(
        self,
        task: TaskSpec,
        agent: AgentSpec,
        task_dir: Path,
        project_root: Path,
    ) -> ProviderResult:
        result = super().execute(task, agent, task_dir, project_root)
        return replace(result, usage=UsageMetrics(latency_ms=1))


class BoundedMeetingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "runs"
        self.plan = RuleBasedPlanner().plan(
            "Implement offline collaboration",
            execution_mode="multi_agent",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def workspace(self, run_id: str, plan: TaskPlan | None = None) -> RunWorkspace:
        return RunWorkspace.create(self.root, run_id, plan or self.plan)

    @staticmethod
    def scheduler(provider: FakeProvider, registry: AgentRegistry | None = None) -> RunScheduler:
        return RunScheduler(
            TaskRouter(registry or default_registry().synthetic()),
            provider,
        )

    def test_consensus_early_stops_and_reuses_one_context_pack(self) -> None:
        provider = RecordingFakeProvider(
            meeting_positions={"build": "option X", "review": "option X"}
        )
        workspace = self.workspace("consensus")
        self.scheduler(provider).run(workspace)
        meeting = workspace.manifest()["meeting"]

        self.assertEqual(meeting["state"], MeetingState.COMPLETED.value)
        self.assertTrue(meeting["early_stopped"])
        self.assertEqual(meeting["rounds_executed"], ["independent_views", "convergence"])
        self.assertEqual(meeting["budget_consumed"]["agent_calls"], 3)
        round1 = [task for task in provider.received if task.inputs.get("meeting_round") == 1]
        self.assertEqual(len(round1), 2)
        refs = {task.inputs["context_pack_ref"] for task in round1}
        self.assertEqual(len(refs), 1)
        self.assertTrue(Path(refs.pop()).is_file())
        self.assertFalse(any(task.inputs.get("conflict_pack_ref") for task in round1))

    def test_conflict_triggers_only_targeted_round2_and_resolves(self) -> None:
        provider = RecordingFakeProvider(
            meeting_positions={"build": "option X", "review": "option Y"},
            round2_positions={"build": "option X", "review": "option X"},
        )
        workspace = self.workspace("conflict")
        self.scheduler(provider).run(workspace)
        meeting = workspace.manifest()["meeting"]

        self.assertEqual(meeting["rounds_executed"], [
            "independent_views",
            "targeted_cross_review",
            "convergence",
        ])
        self.assertFalse(meeting["early_stopped"])
        self.assertTrue(meeting["conflicts"][0]["resolved"])
        self.assertEqual(meeting["dissent"], [])
        round2 = [task for task in provider.received if task.inputs.get("meeting_round") == 2]
        self.assertEqual({task.inputs["source_participant"] for task in round2}, {"build", "review"})
        self.assertTrue(all("conflict_pack_ref" in task.inputs for task in round2))
        self.assertTrue(all("context_pack_ref" not in task.inputs for task in round2))

        architecture_plan = RuleBasedPlanner().plan("Design a system architecture")
        selective_provider = RecordingFakeProvider(
            meeting_positions={"architect": "option X", "build": "option X", "review": "option Y"},
            round2_positions={"architect": "option X", "review": "option X"},
        )
        selective_workspace = self.workspace("selective-conflict", architecture_plan)
        self.scheduler(selective_provider).run(selective_workspace)
        selective_round2 = [
            task for task in selective_provider.received if task.inputs.get("meeting_round") == 2
        ]
        self.assertEqual(
            {task.inputs["source_participant"] for task in selective_round2},
            {"architect", "review"},
        )
        self.assertEqual(len(selective_round2), 2)

    def test_persistent_dissent_is_preserved_without_round3_debate(self) -> None:
        provider = RecordingFakeProvider(
            meeting_positions={"build": "option X", "review": "option Y"}
        )
        workspace = self.workspace("dissent")
        self.scheduler(provider).run(workspace)
        meeting = workspace.manifest()["meeting"]

        self.assertEqual(meeting["state"], MeetingState.COMPLETED.value)
        self.assertFalse(meeting["conflicts"][0]["resolved"])
        self.assertGreaterEqual(len(meeting["dissent"]), 1)
        self.assertEqual(len(meeting["rounds_executed"]), 3)
        result = workspace.read_json("final/meeting-result.json")
        self.assertEqual(result["unresolved_dissent"], meeting["dissent"])

    def test_agent_failure_uses_capability_compatible_fallback(self) -> None:
        fallback = AgentSpec(
            id="fallback-reviewer",
            display_name="Fallback Reviewer",
            provider="fake",
            role="reviewer",
            capabilities=("review",),
            command_template=("fake",),
            cost_class="high",
            concurrency_limit=1,
            permission_profile=("read_workspace",),
            context_limit=10_000,
            availability=True,
            workspace_mode="read_only",
        )
        registry = AgentRegistry((*default_registry().synthetic().list(), fallback))
        provider = RecordingFakeProvider(failures_by_agent={"deepseek-reviewer": 99})
        workspace = self.workspace("fallback")
        self.scheduler(provider, registry).run(workspace)
        participant = workspace.manifest()["meeting"]["participants"]["review"]

        self.assertEqual(participant["status"], "completed")
        self.assertEqual(participant["agent_id"], "fallback-reviewer")
        self.assertIn("deepseek-reviewer", participant["attempted_agents"])
        self.assertEqual(workspace.manifest()["meeting"]["state"], "completed")

    def test_agent_unavailable_blocks_when_remaining_team_is_insufficient(self) -> None:
        agents = tuple(
            replace(agent, availability=False)
            if agent.id == "deepseek-reviewer"
            else agent
            for agent in default_registry().synthetic().list()
        )
        workspace = self.workspace("unavailable")
        self.scheduler(RecordingFakeProvider(), AgentRegistry(agents)).run(workspace)
        meeting = workspace.manifest()["meeting"]
        self.assertEqual(meeting["state"], "blocked")
        self.assertEqual(meeting["participants"]["review"]["status"], "blocked")
        self.assertTrue(workspace.contained("provider-setup", "review.json").is_file())

    def test_call_budget_stops_with_partial_result_and_experience(self) -> None:
        assert self.plan.meeting_plan is not None
        limited = replace(
            self.plan,
            meeting_plan=replace(
                self.plan.meeting_plan,
                budget=replace(self.plan.meeting_plan.budget, max_agent_calls=1),
            ),
        )
        provider = RecordingFakeProvider()
        workspace = self.workspace("call-budget", limited)
        self.scheduler(provider).run(workspace)
        meeting = workspace.manifest()["meeting"]

        self.assertEqual(meeting["state"], "budget_exhausted")
        self.assertEqual(meeting["budget_exhaustion_reason"], "agent_call_budget")
        self.assertEqual(meeting["budget_consumed"]["agent_calls"], 1)
        self.assertTrue(workspace.contained("final", "meeting-experience.json").is_file())
        self.assertNotEqual(workspace.manifest()["status"], "completed")

    def test_token_and_timeout_budgets_are_hard_stops(self) -> None:
        assert self.plan.meeting_plan is not None
        token_plan = replace(
            self.plan,
            meeting_plan=replace(
                self.plan.meeting_plan,
                budget=replace(self.plan.meeting_plan.budget, max_total_tokens=1),
            ),
        )

        class TokenProvider(RecordingFakeProvider):
            def execute(self, *args: object, **kwargs: object) -> ProviderResult:
                result = super().execute(*args, **kwargs)
                return replace(
                    result,
                    usage=UsageMetrics(
                        input_tokens=2,
                        output_tokens=1,
                        latency_ms=1,
                        estimated_cost_usd=0.0,
                        token_status="measured",
                        cost_status="measured",
                    ),
                )

        token_workspace = self.workspace("token-budget", token_plan)
        self.scheduler(TokenProvider()).run(token_workspace)
        self.assertEqual(
            token_workspace.manifest()["meeting"]["budget_exhaustion_reason"],
            "token_budget",
        )

        cost_plan = replace(
            self.plan,
            meeting_plan=replace(
                self.plan.meeting_plan,
                budget=replace(
                    self.plan.meeting_plan.budget,
                    max_total_tokens=None,
                    max_cost_usd=0.001,
                ),
            ),
        )

        class CostProvider(RecordingFakeProvider):
            def execute(self, *args: object, **kwargs: object) -> ProviderResult:
                result = super().execute(*args, **kwargs)
                return replace(
                    result,
                    usage=UsageMetrics(
                        input_tokens=1,
                        output_tokens=1,
                        latency_ms=1,
                        estimated_cost_usd=0.002,
                        token_status="measured",
                        cost_status="measured",
                    ),
                )

        cost_workspace = self.workspace("cost-budget", cost_plan)
        self.scheduler(CostProvider()).run(cost_workspace)
        self.assertEqual(
            cost_workspace.manifest()["meeting"]["budget_exhaustion_reason"],
            "cost_budget",
        )

        timeout_workspace = self.workspace("timeout")

        def age(manifest: dict[str, object]) -> dict[str, object]:
            meeting = manifest["meeting"]
            assert isinstance(meeting, dict)
            meeting["started_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            return manifest

        timeout_workspace.update_manifest(age)
        timeout_provider = RecordingFakeProvider()
        self.scheduler(timeout_provider).run(timeout_workspace)
        self.assertEqual(
            timeout_workspace.manifest()["meeting"]["budget_exhaustion_reason"],
            "wall_time_budget",
        )
        self.assertEqual(timeout_provider.received, [])

    def test_unknown_tokens_remain_unknown(self) -> None:
        workspace = self.workspace("unknown-usage")
        self.scheduler(UnknownUsageProvider()).run(workspace)
        usage = workspace.manifest()["meeting"]["usage"]
        self.assertIsNone(usage["total_tokens"])
        self.assertIsNone(usage["estimated_cost_usd"])
        self.assertEqual(usage["token_status"], "unavailable")
        self.assertEqual(usage["cost_status"], "unavailable")

    def test_cancel_is_durable_and_prevents_calls(self) -> None:
        workspace = self.workspace("cancel")
        provider = RecordingFakeProvider()
        runtime = MeetingRuntime(TaskRouter(default_registry().synthetic()), provider)
        manifest = runtime.cancel(workspace)

        self.assertEqual(manifest["meeting"]["state"], "cancelled")
        self.assertEqual(manifest["status"], "cancelled")
        self.scheduler(provider).run(workspace)
        self.assertEqual(provider.received, [])

    def test_round1_resume_does_not_repeat_completed_call_or_context_artifact(self) -> None:
        provider = InterruptingProvider(phase=1)
        workspace = self.workspace("resume-round1")
        with self.assertRaises(KeyboardInterrupt):
            self.scheduler(provider).run(workspace)
        before = workspace.manifest()
        context_hash = before["meeting"]["context_pack_hash"]
        self.assertEqual(before["meeting"]["participants"]["build"]["status"], "completed")
        self.assertEqual(provider.calls["build"], 1)

        RecoveryManager().recover_interrupted(workspace)
        self.scheduler(provider).run(workspace)
        after = workspace.manifest()
        self.assertEqual(after["meeting"]["state"], "completed")
        self.assertEqual(after["meeting"]["context_pack_hash"], context_hash)
        self.assertEqual(provider.calls["build"], 1)
        self.assertEqual(after["meeting"]["budget_consumed"]["agent_calls"], 3)
        experience_path = workspace.contained("final", "meeting-experience.json")
        experience_mtime = experience_path.stat().st_mtime_ns
        self.scheduler(provider).run(workspace)
        self.assertEqual(experience_path.stat().st_mtime_ns, experience_mtime)
        self.assertEqual(provider.calls["build"], 1)

    def test_round2_resume_does_not_repeat_round1(self) -> None:
        provider = InterruptingProvider(
            phase=2,
            meeting_positions={"build": "X", "review": "Y"},
            round2_positions={"build": "X", "review": "X"},
        )
        workspace = self.workspace("resume-round2")
        with self.assertRaises(KeyboardInterrupt):
            self.scheduler(provider).run(workspace)
        self.assertEqual(workspace.manifest()["meeting"]["state"], "round2_running")
        round1_call_count = provider.calls["build"] + provider.calls["review"]

        RecoveryManager().recover_interrupted(workspace)
        self.scheduler(provider).run(workspace)
        self.assertEqual(workspace.manifest()["meeting"]["state"], "completed")
        self.assertEqual(provider.calls["build"] + provider.calls["review"], round1_call_count)

    def test_context_pack_bounds_large_references_and_illegal_transition_is_rejected(self) -> None:
        build = replace(
            self.plan.tasks[0],
            inputs={"relevant_files": ["x" * 20_000 for _ in range(100)]},
        )
        bounded_plan = replace(self.plan, tasks=(build, *self.plan.tasks[1:]))
        workspace = self.workspace("bounded-context", bounded_plan)
        runtime = MeetingRuntime(
            TaskRouter(default_registry().synthetic()),
            RecordingFakeProvider(),
        )
        runtime.run(workspace)
        context = workspace.read_json("artifacts/meeting/context-pack.json")
        serialized = json.dumps(context, ensure_ascii=False, indent=2)
        assert bounded_plan.meeting_plan is not None
        self.assertLessEqual(len(serialized), bounded_plan.meeting_plan.context_char_limit)
        self.assertTrue(context["content_truncated"])
        with self.assertRaisesRegex(ValueError, "illegal meeting transition"):
            runtime.transition(workspace, MeetingState.ROUND1_RUNNING)

    def test_round_budget_prevents_formal_extra_round(self) -> None:
        assert self.plan.meeting_plan is not None
        one_round = replace(
            self.plan,
            meeting_plan=replace(
                self.plan.meeting_plan,
                budget=replace(self.plan.meeting_plan.budget, max_rounds=1),
            ),
        )
        workspace = self.workspace("round-budget", one_round)
        self.scheduler(RecordingFakeProvider()).run(workspace)
        meeting = workspace.manifest()["meeting"]
        self.assertEqual(meeting["state"], "budget_exhausted")
        self.assertEqual(
            meeting["budget_exhaustion_reason"],
            "round_budget_before_convergence",
        )


if __name__ == "__main__":
    unittest.main()

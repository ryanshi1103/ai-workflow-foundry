from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from flowfoundry.orchestration.decisions import (
    DecisionLedger,
    DecisionLedgerError,
    DecisionQuery,
    query_for_plan,
)
from flowfoundry.orchestration.models import AgentSpec, ProviderResult, TaskPlan, TaskSpec
from flowfoundry.orchestration.planner import RuleBasedPlanner
from flowfoundry.orchestration.providers import FakeProvider
from flowfoundry.orchestration.registry import default_registry
from flowfoundry.orchestration.router import TaskRouter
from flowfoundry.orchestration.scheduler import RunScheduler
from flowfoundry.orchestration.workspace import RunWorkspace


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RecordingProvider(FakeProvider):
    def __init__(self) -> None:
        super().__init__()
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


def decision(
    decision_id: str = "FF-PRODUCT-900",
    *,
    status: str = "BINDING",
    slot: str | None = "official_name",
    value: str | None = "FlowFoundry",
    supersedes: list[str] | None = None,
    superseded_by: str | None = None,
) -> dict[str, object]:
    return {
        "decision_id": decision_id,
        "domain": "PRODUCT",
        "affected_surface": ["github-hero"],
        "project_scope": ["flowfoundry"],
        "semantic_slot": slot,
        "semantic_value": value,
        "date": "2026-08-27",
        "decision": "Keep the official product name FlowFoundry.",
        "status": status,
        "authority": "Test authority",
        "participants": ["Test participant"],
        "originating_contribution": "Test provenance",
        "meeting_id": None,
        "round": None,
        "human_gate": {"status": "NOT_REQUIRED", "evidence": None},
        "evidence": ["tests/test_orchestration_decisions.py"],
        "current_surface": ["README.md"],
        "implementation_status": "Test fixture.",
        "supersedes": supersedes or [],
        "superseded_by": superseded_by,
        "notes": "",
    }


def ledger_data(*records: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": 2,
        "project_id": "flowfoundry",
        "generated_at": "2026-08-27T00:00:00+08:00",
        "candidate_base": "e9692132c20285b348b261d3483c9ae04cfd362e",
        "decisions": list(records or (decision(),)),
    }


class DecisionLedgerValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / ".flowfoundry").mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write(self, data: object) -> Path:
        path = self.root / ".flowfoundry" / "decision-ledger.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def assert_code(self, data: object, code: str) -> None:
        self.write(data)
        with self.assertRaises(DecisionLedgerError) as caught:
            DecisionLedger.load(self.root)
        self.assertEqual(caught.exception.code, code)

    def test_completed_reconciliation_ledger_validates(self) -> None:
        ledger = DecisionLedger.load(PROJECT_ROOT)
        self.assertEqual((ledger.project_id, len(ledger.records)), ("flowfoundry", 36))

    def test_stale_schema_and_unknown_fields_fail(self) -> None:
        stale = ledger_data()
        stale["schema_version"] = 1
        self.assert_code(stale, "STALE_SCHEMA")
        unknown = ledger_data()
        unknown["forged_authority"] = True
        self.assert_code(unknown, "INVALID_LEDGER_SCHEMA")

    def test_duplicate_ids_and_unsupported_status_fail(self) -> None:
        item = decision()
        self.assert_code(ledger_data(item, deepcopy(item)), "DUPLICATE_DECISION_ID")
        malformed = decision(status="binding")
        self.assert_code(ledger_data(malformed), "UNSUPPORTED_STATUS")

    def test_missing_and_unsafe_evidence_references_fail(self) -> None:
        missing = decision()
        missing["evidence"] = []
        self.assert_code(ledger_data(missing), "MISSING_EVIDENCE_REFERENCE")
        unsafe = decision()
        unsafe["evidence"] = ["../outside.json"]
        self.assert_code(ledger_data(unsafe), "UNSAFE_EVIDENCE_REFERENCE")

    def test_invalid_link_and_supersession_cycle_fail(self) -> None:
        broken = decision(status="SUPERSEDED", superseded_by="FF-PRODUCT-901")
        self.assert_code(ledger_data(broken), "INVALID_SUPERSESSION_LINK")
        first = decision(
            "FF-PRODUCT-900",
            status="SUPERSEDED",
            supersedes=["FF-PRODUCT-901"],
            superseded_by="FF-PRODUCT-901",
        )
        second = decision(
            "FF-PRODUCT-901",
            status="SUPERSEDED",
            supersedes=["FF-PRODUCT-900"],
            superseded_by="FF-PRODUCT-900",
        )
        self.assert_code(ledger_data(first, second), "SUPERSESSION_CYCLE")

    def test_two_binding_decisions_in_one_exclusive_slot_fail(self) -> None:
        first = decision("FF-PRODUCT-900")
        second = decision("FF-PRODUCT-901", value="FlowFoundry AI")
        self.assert_code(ledger_data(first, second), "CONFLICTING_BINDING_SLOT")

    def test_human_review_item_warns_and_never_becomes_authority(self) -> None:
        item = decision(status="NEEDS_HUMAN_REVIEW")
        self.write(ledger_data(item))
        ledger = DecisionLedger.load(self.root)
        resolution = ledger.resolve(
            DecisionQuery(("PRODUCT",), ("github-hero",), ("flowfoundry",))
        )
        self.assertEqual(resolution.inherited, ())
        self.assertEqual(resolution.warnings[0]["code"], "HUMAN_REVIEW_DECISION_WARNING")

    def test_malformed_json_oversize_symlink_and_escape_fail(self) -> None:
        path = self.root / ".flowfoundry" / "decision-ledger.json"
        path.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(DecisionLedgerError, "MALFORMED_LEDGER"):
            DecisionLedger.load(self.root)
        path.write_text("x" * 1_000_001, encoding="utf-8")
        with self.assertRaisesRegex(DecisionLedgerError, "LEDGER_TOO_LARGE"):
            DecisionLedger.load(self.root)
        path.unlink()
        target = self.root / "target.json"
        target.write_text(json.dumps(ledger_data()), encoding="utf-8")
        path.symlink_to(target)
        with self.assertRaisesRegex(DecisionLedgerError, "LEDGER_SYMLINK"):
            DecisionLedger.load(self.root)
        with self.assertRaisesRegex(DecisionLedgerError, "LEDGER_PATH_ESCAPE"):
            DecisionLedger.load(self.root, "../target.json")


class DecisionResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = DecisionLedger.load(PROJECT_ROOT)

    def query(self, domains: tuple[str, ...], surfaces: tuple[str, ...]) -> DecisionQuery:
        return DecisionQuery(domains, surfaces, ("flowfoundry",))

    def test_real_brand_task_inherits_exact_authoritative_decisions(self) -> None:
        plan = RuleBasedPlanner().plan("modify GitHub hero")
        resolution = self.ledger.resolve(query_for_plan(plan, self.ledger.project_id))
        by_id = {item.decision_id: item for item in resolution.inherited}
        self.assertTrue(
            {
                "FF-PRODUCT-001",
                "FF-PRODUCT-004",
                "FF-PRODUCT-005",
                "FF-BRAND-002",
            }.issubset(by_id)
        )
        self.assertNotIn("FF-BRAND-001", by_id)
        self.assertEqual(
            by_id["FF-PRODUCT-004"].exact_decision_text,
            "Use the primary English tagline: One goal. The smallest sufficient AI team.",
        )
        self.assertEqual(
            by_id["FF-PRODUCT-005"].exact_decision_text,
            "Use the Chinese campus headline: 你定目标，AI组队实现.",
        )

    def test_deepseek_codex_and_cross_provider_authority_is_status_based(self) -> None:
        resolution = self.ledger.resolve(self.query(("PRODUCT",), ("github-hero",)))
        by_id = {item.decision_id: item for item in resolution.inherited}
        self.assertIn("DeepSeek originated", str(by_id["FF-PRODUCT-005"].provenance))
        self.assertIn("Later productization", str(by_id["FF-PRODUCT-007"].provenance))
        self.assertIn("Both providers independently", str(by_id["FF-PRODUCT-004"].provenance))
        self.assertEqual(by_id["FF-PRODUCT-007"].status, "ADOPTED")

    def test_product_category_and_stage_label_remain_distinct(self) -> None:
        resolution = self.ledger.resolve(self.query(("PRODUCT",), ("github-hero",)))
        by_id = {item.decision_id: item for item in resolution.inherited}
        self.assertEqual(by_id["FF-PRODUCT-002"].semantic_slot, "product_category")
        self.assertEqual(by_id["FF-PRODUCT-002"].status, "BINDING")
        self.assertEqual(by_id["FF-PRODUCT-007"].semantic_slot, "current_stage_label")
        self.assertEqual(by_id["FF-PRODUCT-007"].status, "ADOPTED")

    def test_unrelated_cancellation_task_excludes_brand(self) -> None:
        query = query_for_plan(RuleBasedPlanner().plan("fix cancellation test"), "flowfoundry")
        resolution = self.ledger.resolve(query)
        self.assertIn("FF-RUNTIME-003", {item.decision_id for item in resolution.inherited})
        self.assertFalse(any(item.domain == "BRAND" for item in resolution.inherited))
        self.assertFalse(any(item.semantic_slot == "primary_tagline" for item in resolution.inherited))

    def test_superseded_and_advisory_decisions_are_not_authority(self) -> None:
        resolution = self.ledger.resolve(self.query(("BRAND", "PRODUCT"), ("brand",)))
        ids = {item.decision_id for item in resolution.inherited}
        self.assertNotIn("FF-BRAND-001", ids)
        self.assertIn("FF-BRAND-002", ids)
        self.assertNotIn("FF-PRODUCT-008", ids)

    def test_advisory_is_discoverable_only_when_explicit_and_remains_labeled(self) -> None:
        query = DecisionQuery(
            ("PRODUCT",),
            ("github-hero",),
            ("flowfoundry",),
            include_advisory_context=True,
        )
        resolution = self.ledger.resolve(query)
        self.assertNotIn(
            "FF-PRODUCT-008", {item.decision_id for item in resolution.inherited}
        )
        self.assertIn(
            "FF-PRODUCT-008", {item.decision_id for item in resolution.advisory_context}
        )

    def test_open_decision_warns_but_is_not_inherited(self) -> None:
        resolution = self.ledger.resolve(self.query(("PRODUCT",), ("campus-poster",)))
        self.assertNotIn("FF-PRODUCT-006", {item.decision_id for item in resolution.inherited})
        self.assertIn("OPEN_DECISION_WARNING", {item["code"] for item in resolution.warnings})

    def test_semantic_slot_conflict_warns_without_rewriting_proposal(self) -> None:
        query = DecisionQuery(
            ("RUNTIME",),
            ("cancellation",),
            ("flowfoundry",),
            proposed_changes=(("official_name", "FlowFoundry AI"),),
        )
        warning = next(
            item for item in self.ledger.resolve(query).warnings
            if item["code"] == "DECISION_CONFLICT_WARNING"
        )
        self.assertEqual(warning["existing_value"], "FlowFoundry")
        self.assertEqual(warning["proposed_value"], "FlowFoundry AI")

    def test_vision_narrative_does_not_occupy_primary_tagline_slot(self) -> None:
        query = DecisionQuery(
            ("PRODUCT",),
            ("github-hero",),
            ("flowfoundry",),
            proposed_changes=(("vision_narrative", "A newer launch narrative"),),
        )
        self.assertNotIn(
            "DECISION_CONFLICT_WARNING", {item["code"] for item in self.ledger.resolve(query).warnings}
        )

    def test_context_is_bounded_and_never_truncates_decision_text(self) -> None:
        query = self.query(("BRAND", "PRODUCT"), ("brand", "github-hero"))
        context = self.ledger.context_pack(query, max_chars=3_000)
        rendered = json.dumps(context, ensure_ascii=False, indent=2)
        self.assertLessEqual(len(rendered), 3_000)
        self.assertGreater(context["omitted_decision_count"], 0)
        for item in context["items"]:
            record = next(record for record in self.ledger.records if record.decision_id == item["ID"])
            self.assertEqual(item["EXACT_DECISION"], record.exact_decision_text)
            self.assertNotIn("[truncated]", item["EXACT_DECISION"])


class DecisionContextInjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runs_root = Path(self.temp_dir.name) / "runs"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def scheduler(self, provider: RecordingProvider) -> RunScheduler:
        return RunScheduler(TaskRouter(default_registry().synthetic()), provider)

    def test_simple_task_receives_filtered_decision_context_before_provider(self) -> None:
        plan = RuleBasedPlanner().plan("fix cancellation test", execution_mode="single_agent")
        workspace = RunWorkspace.create(
            self.runs_root, "simple-context", plan, project_root=PROJECT_ROOT
        )
        provider = RecordingProvider()
        self.scheduler(provider).run(workspace)
        context = provider.received[0].inputs["decision_context"]
        ids = {item["ID"] for item in context["items"]}
        self.assertIn("FF-RUNTIME-003", ids)
        self.assertNotIn("FF-PRODUCT-004", ids)
        self.assertFalse(context["automatic_write_back"])

    def test_invalid_ledger_hard_fails_before_any_provider_call(self) -> None:
        project = Path(self.temp_dir.name) / "invalid-project"
        (project / ".flowfoundry").mkdir(parents=True)
        data = ledger_data()
        data["schema_version"] = 1
        (project / ".flowfoundry" / "decision-ledger.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        plan = RuleBasedPlanner().plan("modify GitHub hero", execution_mode="single_agent")
        workspace = RunWorkspace.create(
            self.runs_root, "invalid-ledger", plan, project_root=project
        )
        provider = RecordingProvider()
        with self.assertRaisesRegex(DecisionLedgerError, "STALE_SCHEMA"):
            self.scheduler(provider).run(workspace)
        self.assertEqual(provider.received, [])

    def test_declared_slot_proposal_is_injected_as_warning_without_rewrite(self) -> None:
        task = TaskSpec(
            id="brand",
            title="Modify GitHub hero",
            role="builder",
            required_capabilities=("documentation",),
            inputs={
                "decision_scope": {
                    "domains": ["product"],
                    "affected_surfaces": ["github-hero"],
                    "proposed_changes": {"official_name": "FlowFoundry AI"},
                }
            },
        )
        plan = TaskPlan("Modify GitHub hero", (task,))
        workspace = RunWorkspace.create(
            self.runs_root, "slot-warning", plan, project_root=PROJECT_ROOT
        )
        provider = RecordingProvider()
        self.scheduler(provider).run(workspace)
        context = provider.received[0].inputs["decision_context"]
        warning = next(
            item for item in context["warnings"]
            if item["code"] == "DECISION_CONFLICT_WARNING"
        )
        self.assertEqual(warning["proposed_value"], "FlowFoundry AI")
        self.assertEqual(warning["existing_value"], "FlowFoundry")

    def test_meeting_context_pack_contains_decisions_before_round_one(self) -> None:
        plan = RuleBasedPlanner().plan("modify GitHub hero", execution_mode="multi_agent")
        workspace = RunWorkspace.create(
            self.runs_root, "meeting-context", plan, project_root=PROJECT_ROOT
        )
        provider = RecordingProvider()
        self.scheduler(provider).run(workspace)
        context = workspace.read_json("artifacts/meeting/context-pack.json")
        ids = {item["ID"] for item in context["decision_context"]["items"]}
        self.assertTrue(
            {"FF-PRODUCT-001", "FF-PRODUCT-004", "FF-PRODUCT-005"}.issubset(ids)
        )
        round_one = [task for task in provider.received if task.inputs.get("meeting_round") == 1]
        self.assertTrue(round_one)
        self.assertTrue(all(Path(task.inputs["context_pack_ref"]).is_file() for task in round_one))
        self.assertEqual(
            workspace.manifest()["decision_context"]["inherited_decision_ids"],
            [item["ID"] for item in workspace.read_json("artifacts/decision-context.json")["items"]],
        )


if __name__ == "__main__":
    unittest.main()

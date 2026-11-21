from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from flowfoundry.core.authority import assess_authority
from flowfoundry.core.decisions import decision_conflicts, load_relevant_decisions
from flowfoundry.core.evaluation import EvaluationStatus, evaluate_result
from flowfoundry.core.selection import TaskKind, select_path


class SelectionTests(unittest.TestCase):
    def test_repo_task_uses_one_coding_executor_without_broker(self) -> None:
        selection = select_path("Fix the failing Python test in this repository")
        self.assertEqual(selection.task_kind, TaskKind.CODING)
        self.assertEqual(selection.executor, "codex")
        self.assertFalse(selection.broker_requested)

    def test_recent_research_requests_current_context_broker(self) -> None:
        selection = select_path("Find the latest AI agent changes with sources")
        self.assertEqual(selection.task_kind, TaskKind.RESEARCH)
        self.assertTrue(selection.broker_requested)
        self.assertIn("web_current", selection.required_capabilities)

    def test_maintenance_language_with_research_word_stays_coding(self) -> None:
        selection = select_path("Investigate and research the failing repository tests, implement a fix, and run tests")
        self.assertEqual(selection.task_kind, TaskKind.CODING)

    def test_contract_evidence_overrides_weak_research_keyword(self) -> None:
        selection = select_path("Investigate the issue", expected_artifact="changed repository files", acceptance_criteria="tests pass")
        self.assertEqual(selection.task_kind, TaskKind.CODING)

    def test_explicit_capability_is_respected(self) -> None:
        selection = select_path("check current source notes", requested_capability="coding")
        self.assertEqual(selection.task_kind, TaskKind.CODING)


class DecisionTests(unittest.TestCase):
    def test_loads_only_relevant_authority_and_honors_supersession(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ledger = root / ".flowfoundry" / "decisions.jsonl"
            ledger.parent.mkdir()
            values = (
                {
                    "id": "old-tests",
                    "status": "binding",
                    "text": "Use pytest for repository validation.",
                    "scope": ["testing"],
                    "slot": "test_runner",
                    "value": "pytest",
                },
                {
                    "id": "new-tests",
                    "status": "adopted",
                    "text": "Use unittest for repository validation.",
                    "scope": ["testing"],
                    "slot": "test_runner",
                    "value": "unittest",
                    "supersedes": ["old-tests"],
                },
                {
                    "id": "advisory",
                    "status": "advisory",
                    "text": "Maybe use a different framework for tests.",
                },
                {
                    "id": "branding",
                    "status": "binding",
                    "text": "The brand color is navy.",
                    "scope": ["branding"],
                },
            )
            ledger.write_text(
                "".join(json.dumps(value) + "\n" for value in values),
                encoding="utf-8",
            )
            selected = load_relevant_decisions(root, "Run repository unittest tests")

        self.assertEqual([item.id for item in selected], ["new-tests"])
        conflicts = decision_conflicts(selected, {"test_runner": "pytest"})
        self.assertEqual([item.id for item in conflicts], ["new-tests"])

    def test_no_relevance_means_no_decision_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "docs").mkdir()
            (root / "docs" / "decisions.md").write_text(
                "# Decisions\n\n## 当前有效决定\n- Use navy for all public brand illustrations and diagrams.\n",
                encoding="utf-8",
            )
            self.assertEqual(load_relevant_decisions(root, "run Python tests"), ())


class EvaluatorTests(unittest.TestCase):
    def evaluate_commands(self, commands=(), checks=()):
        return evaluate_result(
            task_kind=TaskKind.CODING,
            executor_succeeded=True,
            output="Fixed",
            commands=commands,
            checks=checks,
            changed_paths=("M source.py",),
        )

    def test_search_without_matches_does_not_override_passing_tests(self) -> None:
        result = self.evaluate_commands(commands=(
            {"command": "rg missing_symbol src", "exit_code": 1},
            {"command": "python -m unittest", "exit_code": 0},
        ))
        self.assertEqual(result.status, EvaluationStatus.PASS)
        self.assertEqual(result.evidence[0]["exit_code"], 1)

    def test_successful_rerun_resolves_same_failed_test_command(self) -> None:
        result = self.evaluate_commands(commands=(
            {"command": "python -m unittest", "exit_code": 1},
            {"command": "python -m unittest", "exit_code": 0},
        ))
        self.assertEqual(result.status, EvaluationStatus.PASS)
        self.assertEqual([item["exit_code"] for item in result.evidence], [1, 0])

    def test_reading_test_files_is_not_acceptance_evidence(self) -> None:
        result = self.evaluate_commands(commands=(
            {"command": "cat tests/test_core.py", "exit_code": 0},
            {"command": "rg --files src tests; git diff --check", "exit_code": 0},
        ))
        self.assertEqual(result.status, EvaluationStatus.PARTIAL)
        self.assertFalse(any(item["acceptance_check"] for item in result.evidence))

    def test_report_heredoc_does_not_replay_embedded_test_text(self) -> None:
        result = self.evaluate_commands(commands=(
            {
                "command": "python - <<'PY'\nprint('python -m unittest')\nPY",
                "exit_code": 0,
            },
        ))
        self.assertEqual(result.status, EvaluationStatus.PARTIAL)

    def test_command_text_and_masked_failures_are_not_acceptance(self) -> None:
        for command in (
            "echo 'python -m unittest'",
            "printf '%s' 'pytest'",
            "rg 'python -m unittest' README.md",
            "python -m unittest; true",
            "python -m unittest || true",
            "python -m unittest | cat",
            "true || python -m unittest",
            "python -m unittest\ntrue",
            "bash -lc \"echo 'python -m unittest'\"",
            "python -m unittest --help",
        ):
            with self.subTest(command=command):
                result = self.evaluate_commands(commands=({"command": command, "exit_code": 0},))
                self.assertEqual(result.status, EvaluationStatus.PARTIAL)

    def test_executed_checks_support_shell_and_environment_prefixes(self) -> None:
        for command in (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest discover -s tests -v",
            "/bin/bash -lc 'python -m unittest discover -s tests'",
            "cd /project && python -m unittest",
            ".venv/bin/python -m unittest",
            "env PYTHONPATH=src python -m unittest",
            "ruff check src",
            "npm run test",
        ):
            with self.subTest(command=command):
                result = self.evaluate_commands(commands=({"command": command, "exit_code": 0},))
                self.assertEqual(result.status, EvaluationStatus.PASS)

    def test_unrelated_passing_test_does_not_resolve_failed_test(self) -> None:
        result = self.evaluate_commands(commands=(
            {"command": "python -m unittest tests.test_a", "exit_code": 1},
            {"command": "python -m unittest tests.test_b", "exit_code": 0},
        ))
        self.assertEqual(result.status, EvaluationStatus.FAIL)

    def test_passing_explicit_acceptance_supersedes_exploratory_failure(self) -> None:
        result = self.evaluate_commands(
            commands=(
                {"command": "python -m unittest tests.test_core", "exit_code": 1},
            ),
            checks=(
                {"command": "python -m unittest discover -s tests", "exit_code": 0},
                {"command": "git diff --check", "exit_code": 0},
            ),
        )
        self.assertEqual(result.status, EvaluationStatus.PASS)

    def test_diff_check_does_not_hide_exploratory_test_failure(self) -> None:
        result = self.evaluate_commands(
            commands=(
                {"command": "python -m unittest tests.test_core", "exit_code": 1},
            ),
            checks=({"command": "git diff --check", "exit_code": 0},),
        )
        self.assertEqual(result.status, EvaluationStatus.FAIL)

    def test_later_failure_overrides_earlier_pass(self) -> None:
        result = self.evaluate_commands(commands=(
            {"command": "python -m unittest", "exit_code": 0},
            {"command": "python -m unittest", "exit_code": 1},
        ))
        self.assertEqual(result.status, EvaluationStatus.FAIL)

    def test_explicit_check_errors_and_failures_override_passing_tests(self) -> None:
        for check in (
            {"command": "custom-validator", "exit_code": 1},
            {"command": "custom-validator", "exit_code": None, "error": "timed out"},
            {"command": "git diff --check", "exit_code": 2},
        ):
            with self.subTest(check=check):
                result = self.evaluate_commands(
                    commands=({"command": "python -m unittest", "exit_code": 0},),
                    checks=(check,),
                )
                self.assertEqual(result.status, EvaluationStatus.FAIL)
                self.assertEqual(result.evidence[-1]["command"], check["command"])

    def test_agent_done_without_evidence_is_unknown(self) -> None:
        result = evaluate_result(
            task_kind=TaskKind.GENERAL,
            executor_succeeded=True,
            output="Done",
            commands=(),
            checks=(),
            changed_paths=(),
        )
        self.assertEqual(result.status, EvaluationStatus.UNKNOWN)

    def test_git_diff_check_alone_is_not_coding_acceptance(self) -> None:
        result = evaluate_result(
            task_kind=TaskKind.CODING,
            executor_succeeded=True,
            output="Fixed",
            commands=(),
            checks=({"command": "git diff --check", "exit_code": 0},),
            changed_paths=("M source.py",),
        )
        self.assertEqual(result.status, EvaluationStatus.PARTIAL)

    def test_passing_tests_are_pass(self) -> None:
        result = evaluate_result(
            task_kind=TaskKind.CODING,
            executor_succeeded=True,
            output="Fixed",
            commands=({"command": "python -m unittest", "exit_code": 0},),
            checks=(),
            changed_paths=("M source.py",),
        )
        self.assertEqual(result.status, EvaluationStatus.PASS)

    def test_failed_check_overrides_executor_claim(self) -> None:
        result = evaluate_result(
            task_kind=TaskKind.CODING,
            executor_succeeded=True,
            output="Done",
            commands=(),
            checks=({"command": "python -m unittest", "exit_code": 1},),
            changed_paths=(),
        )
        self.assertEqual(result.status, EvaluationStatus.FAIL)

    def test_research_without_sources_fails(self) -> None:
        result = evaluate_result(
            task_kind=TaskKind.RESEARCH,
            executor_succeeded=True,
            output="Three important changes happened.",
            commands=(),
            checks=(),
            changed_paths=(),
        )
        self.assertEqual(result.status, EvaluationStatus.FAIL)

    def test_research_sources_are_partial_not_automatic_pass(self) -> None:
        result = evaluate_result(
            task_kind=TaskKind.RESEARCH,
            executor_succeeded=True,
            output="Official change: https://example.com/changelog",
            commands=(),
            checks=(),
            changed_paths=(),
        )
        self.assertEqual(result.status, EvaluationStatus.PARTIAL)


class AuthorityTests(unittest.TestCase):
    def test_external_action_requires_human(self) -> None:
        decision = assess_authority("Prepare and publish the release")
        self.assertTrue(decision.human_required)
        self.assertIn("publish", decision.human_actions)

    def test_local_fix_does_not_require_human_action(self) -> None:
        self.assertFalse(assess_authority("Fix one local test").human_required)


if __name__ == "__main__":
    unittest.main()

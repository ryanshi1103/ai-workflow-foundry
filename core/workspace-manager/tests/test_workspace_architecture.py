"""Phase 1 contracts for the canonical workspace package layout."""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path

from flowfoundry.workspace.providers import (
    CLAUDE_PERMISSION_MODES,
    CODEX_PROFILES,
    claude_config_dir,
    prepare_claude_environment,
)


class CompatibilityImportTests(unittest.TestCase):
    def test_legacy_modules_alias_canonical_implementations(self):
        aliases = {
            "flowfoundry.workspace.auto_name": (
                "flowfoundry.workspace.lifecycle.auto_name"
            ),
            "flowfoundry.workspace.cc_launcher": (
                "flowfoundry.workspace.cli.launcher"
            ),
            "flowfoundry.workspace.finalize": (
                "flowfoundry.workspace.sessions.finalize"
            ),
            "flowfoundry.workspace.git_manager": (
                "flowfoundry.workspace.lifecycle.git_manager"
            ),
            "flowfoundry.workspace.hook_entry": (
                "flowfoundry.workspace.sessions.hook_entry"
            ),
            "flowfoundry.workspace.hooks": "flowfoundry.workspace.sessions.hooks",
            "flowfoundry.workspace.launcher": (
                "flowfoundry.workspace.lifecycle.launcher"
            ),
            "flowfoundry.workspace.maintain": (
                "flowfoundry.workspace.maintenance.projects"
            ),
            "flowfoundry.workspace.maintain_cli": (
                "flowfoundry.workspace.cli.maintenance"
            ),
            "flowfoundry.workspace.project": (
                "flowfoundry.workspace.lifecycle.project"
            ),
            "flowfoundry.workspace.recovery": (
                "flowfoundry.workspace.sessions.recovery"
            ),
            "flowfoundry.workspace.redact": "flowfoundry.workspace.policy.redact",
            "flowfoundry.workspace.transcript_claude": (
                "flowfoundry.workspace.sessions.transcript_claude"
            ),
            "flowfoundry.workspace.transcript_codex": (
                "flowfoundry.workspace.sessions.transcript_codex"
            ),
            "flowfoundry.workspace.utils": "flowfoundry.workspace.policy.runtime",
        }

        for legacy_name, canonical_name in aliases.items():
            with self.subTest(legacy=legacy_name):
                legacy = importlib.import_module(legacy_name)
                canonical = importlib.import_module(canonical_name)
                self.assertIs(legacy, canonical)

    def test_legacy_cli_package_exports_run(self):
        legacy_cli = importlib.import_module("flowfoundry.workspace.cli")
        canonical_cli = importlib.import_module("flowfoundry.workspace.cli.project")
        self.assertIs(legacy_cli.run, canonical_cli.run)


class ProviderIsolationTests(unittest.TestCase):
    def test_claude_clears_conflicting_provider_credentials(self):
        environment = {
            "ANTHROPIC_BASE_URL": "https://example.invalid",
            "ANTHROPIC_AUTH_TOKEN": "synthetic-token",
            "ANTHROPIC_API_KEY": "synthetic-key",
            "UNRELATED": "preserved",
        }

        result = prepare_claude_environment("claude", environment)

        self.assertEqual(result["UNRELATED"], "preserved")
        self.assertNotIn("ANTHROPIC_BASE_URL", result)
        self.assertNotIn("ANTHROPIC_AUTH_TOKEN", result)
        self.assertNotIn("ANTHROPIC_API_KEY", result)
        self.assertEqual(result["CLAUDE_CONFIG_DIR"], str(Path.home() / ".claude-native"))

    def test_deepseek_uses_an_isolated_config_directory(self):
        environment = {"ANTHROPIC_AUTH_TOKEN": "synthetic-token"}

        result = prepare_claude_environment("deepseek", environment)

        self.assertEqual(
            result["CLAUDE_CONFIG_DIR"], str(Path.home() / ".claude-deepseek")
        )
        self.assertEqual(result["ANTHROPIC_AUTH_TOKEN"], "synthetic-token")
        self.assertEqual(
            claude_config_dir("deepseek", home=Path("/tmp/synthetic-home")),
            Path("/tmp/synthetic-home/.claude-deepseek"),
        )

    def test_public_permission_and_profile_values_remain_stable(self):
        self.assertEqual(CLAUDE_PERMISSION_MODES["m"]["mode"], "default")
        self.assertEqual(CLAUDE_PERMISSION_MODES["e"]["mode"], "acceptEdits")
        self.assertEqual(CLAUDE_PERMISSION_MODES["p"]["mode"], "plan")
        self.assertEqual(CLAUDE_PERMISSION_MODES["a"]["mode"], "auto")
        self.assertEqual(
            CLAUDE_PERMISSION_MODES["b"]["mode"], "bypassPermissions"
        )
        self.assertEqual(CODEX_PROFILES["m"]["profile"], "gpt56-sol-manual")
        self.assertEqual(CODEX_PROFILES["p"]["profile"], "gpt56-sol-readonly")
        self.assertEqual(CODEX_PROFILES["a"]["profile"], "gpt56-sol-auto")
        self.assertEqual(CODEX_PROFILES["b"]["profile"], "gpt56-sol-full")


if __name__ == "__main__":
    unittest.main()

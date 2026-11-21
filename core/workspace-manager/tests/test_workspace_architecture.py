"""Contracts for the canonical workspace package layout."""

from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path

from flowfoundry.workspace.providers import (
    CLAUDE_NATIVE_PROFILE,
    CLAUDE_PERMISSION_MODES,
    CODEX_PROFILES,
    DEEPSEEK_COMPATIBLE_PROFILE,
    claude_config_dir,
    claude_profile_provider,
    claude_runtime_profile,
    prepare_claude_environment,
    prepare_claude_profile_environment,
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[3] / "src/flowfoundry/workspace"
ROOT_SHIM_NAMES = {
    "auto_name",
    "cc_launcher",
    "finalize",
    "git_manager",
    "hook_entry",
    "hooks",
    "launcher",
    "maintain",
    "maintain_cli",
    "project",
    "recovery",
    "redact",
    "transcript_claude",
    "transcript_codex",
    "utils",
}


class CanonicalImportTests(unittest.TestCase):
    def test_canonical_workspace_modules_import(self):
        modules = (
            "flowfoundry.workspace.cli.launcher",
            "flowfoundry.workspace.cli.maintenance",
            "flowfoundry.workspace.lifecycle.project",
            "flowfoundry.workspace.lifecycle.launcher",
            "flowfoundry.workspace.lifecycle.git_manager",
            "flowfoundry.workspace.sessions.finalize",
            "flowfoundry.workspace.sessions.finalization.pipeline",
            "flowfoundry.workspace.sessions.finalization.validation",
            "flowfoundry.workspace.sessions.finalization.recovery",
            "flowfoundry.workspace.sessions.finalization.output",
            "flowfoundry.workspace.sessions.finalization.hooks",
            "flowfoundry.workspace.sessions.hooks",
            "flowfoundry.workspace.sessions.recovery",
            "flowfoundry.workspace.policy.redact",
            "flowfoundry.workspace.policy.runtime",
            "flowfoundry.workspace.maintenance.projects",
        )
        for module_name in modules:
            with self.subTest(module=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))

    def test_root_level_workspace_shims_are_absent(self):
        for module_name in ROOT_SHIM_NAMES:
            with self.subTest(module=module_name):
                self.assertFalse((WORKSPACE_ROOT / f"{module_name}.py").exists())

    def test_internal_imports_do_not_target_removed_root_shims(self):
        violations = []
        absolute_shims = {
            f"flowfoundry.workspace.{name}" for name in ROOT_SHIM_NAMES
        }
        for source_path in WORKSPACE_ROOT.rglob("*.py"):
            tree = ast.parse(source_path.read_text(encoding="utf-8"), source_path)
            relative = source_path.relative_to(WORKSPACE_ROOT).with_suffix("")
            module_parts = ["flowfoundry", "workspace", *relative.parts]
            package = ".".join(module_parts[:-1])
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or not node.module:
                    continue
                target = node.module
                if node.level:
                    target = importlib.util.resolve_name(
                        "." * node.level + node.module,
                        package,
                    )
                if target in absolute_shims:
                    violations.append(f"{source_path}:{node.lineno}:{target}")
        self.assertEqual(violations, [])

    def test_cli_package_exports_run(self):
        cli_package = importlib.import_module("flowfoundry.workspace.cli")
        cli_module = importlib.import_module("flowfoundry.workspace.cli.project")
        self.assertIs(cli_package.run, cli_module.run)

    def test_legacy_package_maps_directly_to_canonical_modules(self):
        legacy = importlib.import_module("ai_project_manager.project")
        canonical = importlib.import_module("flowfoundry.workspace.lifecycle.project")
        self.assertIs(legacy, canonical)


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

    def test_claude_compatible_profiles_have_distinct_provider_identity(self):
        self.assertEqual(claude_runtime_profile("claude"), CLAUDE_NATIVE_PROFILE)
        self.assertEqual(
            claude_runtime_profile("deepseek"), DEEPSEEK_COMPATIBLE_PROFILE
        )
        self.assertEqual(claude_profile_provider(CLAUDE_NATIVE_PROFILE), "claude")
        self.assertEqual(
            claude_profile_provider(DEEPSEEK_COMPATIBLE_PROFILE), "deepseek"
        )
        self.assertIsNone(claude_profile_provider("generic_claude"))

    def test_profile_environment_matches_real_provider_launch_context(self):
        inherited = {
            "ANTHROPIC_BASE_URL": "https://example.invalid",
            "ANTHROPIC_AUTH_TOKEN": "synthetic-token",
        }
        native = prepare_claude_profile_environment(
            CLAUDE_NATIVE_PROFILE, dict(inherited)
        )
        deepseek = prepare_claude_profile_environment(
            DEEPSEEK_COMPATIBLE_PROFILE, dict(inherited)
        )

        self.assertTrue(native["CLAUDE_CONFIG_DIR"].endswith(".claude-native"))
        self.assertNotIn("ANTHROPIC_BASE_URL", native)
        self.assertNotIn("ANTHROPIC_AUTH_TOKEN", native)
        self.assertTrue(deepseek["CLAUDE_CONFIG_DIR"].endswith(".claude-deepseek"))
        self.assertEqual(deepseek["ANTHROPIC_BASE_URL"], "https://example.invalid")
        self.assertEqual(deepseek["ANTHROPIC_AUTH_TOKEN"], "synthetic-token")

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

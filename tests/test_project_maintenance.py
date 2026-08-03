#!/usr/bin/env python3
"""Regression tests for project classification, protection, and naming safety."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_project_manager import auto_name, maintain


class ProjectMaintenanceTests(unittest.TestCase):
    def test_managed_project_policy_parses_safe_direct_children(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy = Path(tmp) / "managed-projects"
            policy.write_text(
                "mirror | managed | true | public mirror\n"
                "legacy | archive | false | old workspace\n"
                "../escape | managed | true | invalid\n",
                encoding="utf-8",
            )
            with patch.object(maintain, "MANAGED_PROJECTS_LIST", policy):
                self.assertEqual(
                    maintain.load_managed_projects(),
                    [
                        {"name": "mirror", "group": "managed", "auto_update": True, "reason": "public mirror"},
                        {"name": "legacy", "group": "archive", "auto_update": False, "reason": "old workspace"},
                    ],
                )

    def test_managed_project_sync_only_fast_forwards_clean_clone(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "Projects"
            remote = Path(tmp) / "remote.git"
            seed = Path(tmp) / "seed"
            managed = root / "managed-copy"
            root.mkdir()
            subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
            subprocess.run(["git", "init", "-q", "-b", "main", str(seed)], check=True)
            subprocess.run(["git", "-C", str(seed), "config", "user.name", "Test User"], check=True)
            subprocess.run(["git", "-C", str(seed), "config", "user.email", "test@example.invalid"], check=True)
            (seed / "version.txt").write_text("one\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(seed), "add", "version.txt"], check=True)
            subprocess.run(["git", "-C", str(seed), "commit", "-qm", "initial"], check=True)
            subprocess.run(["git", "-C", str(seed), "remote", "add", "origin", str(remote)], check=True)
            subprocess.run(["git", "-C", str(seed), "push", "-qu", "origin", "main"], check=True)
            subprocess.run(["git", "--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/main"], check=True)
            subprocess.run(["git", "clone", "-q", str(remote), str(managed)], check=True)

            (seed / "version.txt").write_text("two\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(seed), "commit", "-qam", "update"], check=True)
            subprocess.run(["git", "-C", str(seed), "push", "-q"], check=True)
            policy = Path(tmp) / "managed-projects"
            policy.write_text("managed-copy | managed | true | test\n", encoding="utf-8")

            with (
                patch.object(maintain, "PROJECTS_ROOT", root),
                patch.object(maintain, "MANAGED_PROJECTS_LIST", policy),
            ):
                result = maintain.sync_managed_projects()
            self.assertEqual(result[0]["status"], "updated")
            self.assertEqual((managed / "version.txt").read_text(encoding="utf-8"), "two\n")

            (managed / "local.txt").write_text("keep\n", encoding="utf-8")
            with (
                patch.object(maintain, "PROJECTS_ROOT", root),
                patch.object(maintain, "MANAGED_PROJECTS_LIST", policy),
            ):
                dirty_result = maintain.sync_managed_projects()
            self.assertEqual(dirty_result[0]["status"], "dirty")
            self.assertTrue((managed / "local.txt").exists())

    def test_annotated_protected_list_uses_first_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            protected_file = Path(tmp) / "protected-projects"
            protected_file.write_text(
                "# comment\n"
                "/tmp/core | infrastructure | source of truth\n"
                "plain-project\n",
                encoding="utf-8",
            )
            with patch.object(maintain, "PROTECTED_LIST", protected_file):
                self.assertEqual(
                    maintain.load_protected(),
                    {"/tmp/core", "plain-project"},
                )

    def test_workspace_manager_is_core_infrastructure(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "ai-project-workspace-manager"
            (project / "src").mkdir(parents=True)
            (project / "CLAUDE.md").write_text("rules", encoding="utf-8")
            self.assertEqual(maintain.classify_project(project), "A")

    def test_flowfoundry_has_core_protection_reason(self):
        self.assertEqual(
            maintain._protection_reason("ai-workflow-foundry", True),
            "核心基础设施",
        )

    def test_nested_deliverables_are_real_project_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "A"
            (project / "deliverables").mkdir(parents=True)
            (project / "deliverables" / "nameplates.pdf").write_bytes(b"pdf")
            self.assertEqual(maintain.classify_project(project), "B")

    def test_nested_project_under_generic_container_is_real(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "System"
            child = project / "grub-minimal-focus-theme"
            (child / "theme").mkdir(parents=True)
            (child / "README.md").write_text("# GRUB theme\n", encoding="utf-8")
            self.assertEqual(maintain.classify_project(project), "B")

    def test_analysis_preserves_project_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "sample-project"
            (project / ".ai").mkdir(parents=True)
            (project / ".ai" / "project.json").write_text(
                '{"status": "active", "tool": "codex"}',
                encoding="utf-8",
            )
            self.assertEqual(auto_name.analyze_project(project)["status"], "active")

    def test_readme_prose_is_used_before_source_fragments(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "presentation-project"
            project.mkdir()
            (project / "README.md").write_text(
                "# Four Schools Presentation\n\n"
                "A presentation for high-school students about four universities.\n\n"
                "## Files\n",
                encoding="utf-8",
            )
            (project / "build.py").write_text("def rect():\n    pass\n", encoding="utf-8")
            analysis = auto_name.analyze_project(project)
            self.assertEqual(
                analysis["summary"],
                "A presentation for high-school students about four universities.",
            )

    def test_project_state_overview_overrides_readme_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "stateful-project"
            (project / ".ai").mkdir(parents=True)
            (project / "README.md").write_text(
                "# Stateful Project\n\nREADME summary.\n",
                encoding="utf-8",
            )
            (project / ".ai" / "PROJECT_STATE.md").write_text(
                "# Stateful Project — Status\n\n"
                "## 项目概述\n\nAuthoritative project overview.\n",
                encoding="utf-8",
            )
            self.assertEqual(
                auto_name.analyze_project(project)["summary"],
                "Authoritative project overview.",
            )

    def test_sole_nested_readme_supplies_display_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "System"
            child = project / "grub-theme"
            (child / "theme").mkdir(parents=True)
            (child / "README.md").write_text(
                "# Minimal Focus GRUB2 Theme\n\nA Fedora-focused boot theme.\n",
                encoding="utf-8",
            )
            analysis = auto_name.analyze_project(project)
            self.assertEqual(analysis["display_name"], "Minimal Focus GRUB2 Theme")
            self.assertEqual(analysis["summary"], "A Fedora-focused boot theme.")
            self.assertEqual(analysis["project_type"], "system-theme")

    def test_project_type_does_not_require_session_tool_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "slides"
            project.mkdir()
            (project / "README.md").write_text("# Slides\n", encoding="utf-8")
            (project / "presentation.pptx").write_bytes(b"pptx")
            self.assertEqual(
                auto_name.analyze_project(project)["project_type"],
                "presentation",
            )

    def test_backend_templates_are_classified_as_web_application(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "shop"
            (project / "backend" / "templates").mkdir(parents=True)
            (project / "README.md").write_text("# Shop\n", encoding="utf-8")
            self.assertEqual(
                auto_name.analyze_project(project)["project_type"],
                "web-application",
            )

    def test_safe_rename_rejects_dirty_git_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects_root = Path(tmp)
            project = projects_root / "13"
            project.mkdir()
            subprocess.run(
                ["git", "init", "-q", str(project)],
                check=True,
                capture_output=True,
            )
            (project / "uncommitted.txt").write_text("keep me", encoding="utf-8")
            with patch.object(auto_name, "PROJECTS_ROOT", projects_root):
                result = auto_name.safe_rename_project(project, "named-project")
            self.assertFalse(result["success"])
            self.assertIn("uncommitted", result["error"])
            self.assertTrue(project.exists())


if __name__ == "__main__":
    unittest.main()

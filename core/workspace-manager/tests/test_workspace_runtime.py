"""Minimum runtime coverage for lifecycle, sessions, policy, and finalization."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flowfoundry.workspace.lifecycle import project
from flowfoundry.workspace.policy import redact, runtime
from flowfoundry.workspace.sessions import finalize, recovery


class LifecycleTests(unittest.TestCase):
    def test_project_structure_and_status_transition_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = Path(temporary) / "workspace"
            project.create_project_structure(project_dir, "Workspace Fixture")

            self.assertTrue((project_dir / ".ai-session/private").is_dir())
            self.assertEqual(
                (project_dir / ".ai-session/private").stat().st_mode & 0o777,
                0o700,
            )
            self.assertIn(".ai-session/private/", (project_dir / ".gitignore").read_text())
            self.assertTrue(project.validate_status_transition("initializing", "running"))
            self.assertFalse(project.validate_status_transition("completed", "running"))


class PolicyTests(unittest.TestCase):
    def test_atomic_json_round_trip_and_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "state/data.json"
            lock_path = root / "state/runtime.lock"

            with runtime.file_lock(lock_path):
                runtime.atomic_write_json(target, {"status": "safe"})

            self.assertEqual(runtime.read_json(target), {"status": "safe"})

    def test_redaction_removes_synthetic_credentials(self):
        text = "token=sk-" + "x" * 48
        redacted, changed = redact.redact_text(text)

        self.assertTrue(changed)
        self.assertNotIn("x" * 48, redacted)
        self.assertIn("REDACTED", redacted)


class RecoveryTests(unittest.TestCase):
    def test_scan_finds_stale_running_project(self):
        with tempfile.TemporaryDirectory() as temporary:
            projects_root = Path(temporary) / "Projects"
            project_dir = projects_root / "interrupted-workspace"
            project.create_project_structure(project_dir)
            meta = project.create_project_meta(project_dir, "claude", "session-1")
            meta["status"] = "running"
            runtime.atomic_write_json(project_dir / ".ai-session/project.json", meta)

            with patch.object(recovery, "PROJECTS_ROOT", projects_root):
                interrupted = recovery.scan_interrupted_projects()

            self.assertEqual(len(interrupted), 1)
            self.assertEqual(interrupted[0]["session_id"], "session-1")
            self.assertEqual(interrupted[0]["status"], "running")


class FinalizePipelineTests(unittest.TestCase):
    def test_finalize_pipeline_redacts_and_completes_without_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project_dir = root / "workspace"
            state_dir = root / "state"
            transcript = root / "claude-transcript.jsonl"
            session_id = "session-finalize"
            secret = "sk-" + "z" * 48
            transcript.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "user",
                                "message": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "Complete the workspace cleanup",
                                        }
                                    ]
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "assistant",
                                "message": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"Completed cleanup; token={secret}",
                                        }
                                    ]
                                },
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            project.create_project_structure(project_dir, "Finalize Fixture")
            project_meta = project.create_project_meta(
                project_dir,
                "claude",
                session_id,
                transcript_path=str(transcript),
            )
            session_meta = project.create_session_meta(
                project_dir,
                session_id,
                "claude",
                transcript_path=str(transcript),
            )
            project_meta["status"] = "running"
            session_meta["status"] = "running"
            runtime.atomic_write_json(
                project_dir / ".ai-session/project.json", project_meta
            )
            runtime.atomic_write_json(
                project_dir / ".ai-session/sessions" / session_id / "meta.json",
                session_meta,
            )

            with (
                patch.object(runtime, "STATE_DIR", state_dir),
                patch.object(runtime, "GLOBAL_LOCK_FILE", state_dir / "global.lock"),
            ):
                result = finalize.finalize_session(
                    project_dir, session_id=session_id, tool="claude"
                )

            final_meta = runtime.read_json(project_dir / ".ai-session/project.json")
            redacted_path = (
                project_dir
                / ".ai-session/sessions"
                / session_id
                / "transcript.redacted.jsonl"
            )
            private_path = (
                project_dir
                / ".ai-session/private"
                / session_id
                / "transcript.raw.jsonl"
            )

            self.assertTrue(result["success"], result)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(final_meta["status"], "completed")
            self.assertTrue(final_meta["transcript_hash"])
            self.assertTrue(redacted_path.is_file())
            self.assertNotIn(secret, redacted_path.read_text(encoding="utf-8"))
            self.assertIn(secret, private_path.read_text(encoding="utf-8"))
            self.assertTrue(
                (project_dir / "docs/sessions" / session_id / "conversation.md").is_file()
            )

    def test_finalize_missing_metadata_fails_without_side_effects(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = Path(temporary)

            result = finalize.finalize_session(project_dir, session_id="missing")

            self.assertFalse(result["success"])
            self.assertEqual(result["error"], "No project.json found")


if __name__ == "__main__":
    unittest.main()

"""Durable, ownership-safe Git worktrees for mutating agent executions."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .models import IsolationMode, WorktreeStatus
from .workspace import (
    RunWorkspace,
    atomic_write_json,
    atomic_write_text,
    secure_file_lock,
    utc_now,
)


class WorktreeError(RuntimeError):
    """A bounded, operator-visible isolation failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class GitWorktree:
    path: Path
    head: str | None
    branch: str | None
    bare: bool = False
    detached: bool = False
    prunable: bool = False


@dataclass(frozen=True)
class CandidateResult:
    base_commit: str
    worktree_id: str
    branch: str
    changed_files: tuple[str, ...]
    diff_summary: str
    git_status: str
    diff_artifact_ref: str
    validation: dict[str, Any]
    provider_result: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_commit": self.base_commit,
            "worktree_id": self.worktree_id,
            "branch": self.branch,
            "changed_files": list(self.changed_files),
            "changed_files_count": len(self.changed_files),
            "diff_summary": self.diff_summary,
            "git_status": self.git_status,
            "diff_artifact_ref": self.diff_artifact_ref,
            "validation": self.validation,
            "provider_result": self.provider_result,
        }


_SAFE_CHARS = re.compile(r"[^a-zA-Z0-9._-]+")
_TERMINAL = {
    WorktreeStatus.COMPLETED.value,
    WorktreeStatus.RETAINED.value,
    WorktreeStatus.FAILED.value,
    WorktreeStatus.BLOCKED.value,
}
_TRANSITIONS = {
    WorktreeStatus.ALLOCATING.value: {
        WorktreeStatus.READY.value,
        WorktreeStatus.FAILED.value,
        WorktreeStatus.ORPHANED.value,
    },
    WorktreeStatus.READY.value: {
        WorktreeStatus.IN_USE.value,
        WorktreeStatus.VALIDATING.value,
        WorktreeStatus.COMPLETED.value,
        WorktreeStatus.RETAINED.value,
        WorktreeStatus.ORPHANED.value,
    },
    WorktreeStatus.IN_USE.value: {
        WorktreeStatus.READY.value,
        WorktreeStatus.VALIDATING.value,
        WorktreeStatus.COMPLETED.value,
        WorktreeStatus.RETAINED.value,
        WorktreeStatus.FAILED.value,
        WorktreeStatus.ORPHANED.value,
    },
    WorktreeStatus.VALIDATING.value: {
        WorktreeStatus.COMPLETED.value,
        WorktreeStatus.RETAINED.value,
        WorktreeStatus.FAILED.value,
        WorktreeStatus.ORPHANED.value,
    },
    WorktreeStatus.COMPLETED.value: {
        WorktreeStatus.IN_USE.value,
        WorktreeStatus.VALIDATING.value,
        WorktreeStatus.RETAINED.value,
        WorktreeStatus.REMOVED.value,
        WorktreeStatus.ORPHANED.value,
    },
    WorktreeStatus.RETAINED.value: {
        WorktreeStatus.IN_USE.value,
        WorktreeStatus.VALIDATING.value,
        WorktreeStatus.COMPLETED.value,
        WorktreeStatus.REMOVED.value,
        WorktreeStatus.ORPHANED.value,
    },
    WorktreeStatus.FAILED.value: {
        WorktreeStatus.IN_USE.value,
        WorktreeStatus.RETAINED.value,
        WorktreeStatus.REMOVED.value,
        WorktreeStatus.ORPHANED.value,
    },
    WorktreeStatus.ORPHANED.value: {
        WorktreeStatus.READY.value,
        WorktreeStatus.RETAINED.value,
        WorktreeStatus.FAILED.value,
    },
    WorktreeStatus.BLOCKED.value: set(),
    WorktreeStatus.REMOVED.value: set(),
}


def sanitize_component(value: object, *, max_length: int = 48) -> str:
    """Make a portable component while preserving collision resistance."""

    raw = str(value)
    digest = hashlib.sha256(raw.encode("utf-8", errors="surrogatepass")).hexdigest()[:10]
    slug = _SAFE_CHARS.sub("-", raw).strip("._-").lower()
    while ".." in slug:
        slug = slug.replace("..", ".")
    if not slug:
        slug = "item"
    slug = slug[: max(1, max_length - len(digest) - 1)].rstrip("._-") or "item"
    return f"{slug}-{digest}"


def parse_worktree_porcelain_z(data: bytes) -> tuple[GitWorktree, ...]:
    """Parse `git worktree list --porcelain -z` without path ambiguity."""

    records: list[GitWorktree] = []
    current: dict[str, Any] = {}
    for token in data.split(b"\0"):
        if not token:
            if current.get("worktree") is not None:
                records.append(
                    GitWorktree(
                        path=Path(os.fsdecode(current["worktree"])).resolve(),
                        head=_decode_optional(current.get("HEAD")),
                        branch=_decode_optional(current.get("branch")),
                        bare=bool(current.get("bare")),
                        detached=bool(current.get("detached")),
                        prunable=bool(current.get("prunable")),
                    )
                )
                current = {}
            continue
        key, separator, value = token.partition(b" ")
        current[os.fsdecode(key)] = value if separator else True
    if current.get("worktree") is not None:
        records.append(
            GitWorktree(
                path=Path(os.fsdecode(current["worktree"])).resolve(),
                head=_decode_optional(current.get("HEAD")),
                branch=_decode_optional(current.get("branch")),
                bare=bool(current.get("bare")),
                detached=bool(current.get("detached")),
                prunable=bool(current.get("prunable")),
            )
        )
    return tuple(records)


def _decode_optional(value: object) -> str | None:
    return os.fsdecode(value) if isinstance(value, bytes) else None


class WorktreeManager:
    """Owns only worktrees backed by a matching durable FlowFoundry record."""

    def __init__(self, workspace: RunWorkspace, *, managed_root: Path | None = None) -> None:
        self.workspace = workspace
        self.repository_root = self._repository_root(workspace.project_root)
        self.repository_id = self._repository_identity(self.repository_root)
        self.managed_root = (
            Path(managed_root).resolve()
            if managed_root is not None
            else self._default_managed_root()
        )
        self.records_root = workspace.contained("worktrees")
        self.records_root.mkdir(parents=True, exist_ok=True, mode=0o700)

    @staticmethod
    def isolation_mode(
        *,
        required_permissions: Iterable[str],
        agent_permissions: Iterable[str],
        provider_requires_isolation: bool,
        meeting: bool = False,
    ) -> IsolationMode:
        required = set(required_permissions)
        allowed = set(agent_permissions)
        if "read_workspace" not in required and "write_workspace" not in required:
            return IsolationMode.NONE
        if meeting or "write_workspace" not in required:
            return IsolationMode.READ_ONLY
        if "write_workspace" not in allowed:
            raise WorktreeError("WRITE_PERMISSION_DENIED", "agent lacks write_workspace permission")
        return (
            IsolationMode.MANAGED_WORKTREE
            if provider_requires_isolation
            else IsolationMode.NONE
        )

    def allocate(
        self,
        *,
        task_id: str,
        participant_id: str,
        attempt_id: int,
        base_commit: str = "HEAD",
        candidate_id: str | None = None,
        dirty_base_required: bool = False,
    ) -> dict[str, Any]:
        if dirty_base_required:
            raise WorktreeError(
                "DIRTY_BASE_REQUIRES_SNAPSHOT",
                "task explicitly depends on uncommitted state; snapshot support is not implemented",
            )
        candidate = candidate_id or task_id
        identity_seed = "\0".join(
            (self.repository_id, self.workspace.run_id, candidate, participant_id)
        )
        worktree_id = f"wt-{hashlib.sha256(identity_seed.encode()).hexdigest()[:20]}"
        record_path = self._record_path(worktree_id)
        with secure_file_lock(self.records_root / ".leases.lock"):
            if record_path.is_file():
                record = self.workspace.read_json(str(record_path.relative_to(self.workspace.path)))
                self._validate_owned_record(record)
                return record

            base_sha = self._git_text("rev-parse", "--verify", f"{base_commit}^{{commit}}")
            run_component = sanitize_component(self.workspace.run_id)
            candidate_component = sanitize_component(candidate)
            participant_component = sanitize_component(participant_id)
            leaf = f"{candidate_component}-{participant_component}-{worktree_id[-8:]}"
            path = self._contained_managed(run_component, leaf)
            branch = self._branch_name(task_id, participant_id, attempt_id, worktree_id)
            record = {
                "schema_version": 1,
                "owner": "flowfoundry",
                "worktree_id": worktree_id,
                "run_id": self.workspace.run_id,
                "task_id": task_id,
                "participant_id": participant_id,
                "attempt_id": attempt_id,
                "repository_id": self.repository_id,
                "repository_root": str(self.repository_root),
                "managed_root": str(self.managed_root),
                "path": str(path),
                "branch": branch,
                "base_commit": base_sha,
                "write_capable": True,
                "submodules": (
                    "present_not_initialized"
                    if self._git_completed(
                        "cat-file", "-e", f"{base_sha}:.gitmodules"
                    ).returncode
                    == 0
                    else "not_present"
                ),
                "status": WorktreeStatus.ALLOCATING.value,
                "active_writer": None,
                "allocation_latency_ms": None,
                "cleanup_latency_ms": None,
                "created_at": utc_now(),
                "updated_at": utc_now(),
            }
            atomic_write_json(record_path, record)
            self.managed_root.mkdir(parents=True, exist_ok=True, mode=0o700)
            started = time.monotonic()
            try:
                self._git("worktree", "add", "-b", branch, str(path), base_sha)
            except WorktreeError as exc:
                record.update(
                    {
                        "status": WorktreeStatus.FAILED.value,
                        "error": str(exc),
                        "updated_at": utc_now(),
                    }
                )
                atomic_write_json(record_path, record)
                raise
            record.update(
                {
                    "status": WorktreeStatus.READY.value,
                    "allocation_latency_ms": round((time.monotonic() - started) * 1000),
                    "updated_at": utc_now(),
                }
            )
            atomic_write_json(record_path, record)
            return record

    def acquire_writer(self, worktree_id: str, *, participant_id: str, attempt_id: int) -> dict[str, Any]:
        with secure_file_lock(self.records_root / ".leases.lock"):
            record = self.record(worktree_id)
            active = record.get("active_writer")
            if active is not None:
                if (
                    active.get("participant_id") == participant_id
                    and int(active.get("attempt_id", -1)) == attempt_id
                ):
                    return record
                raise WorktreeError("WRITER_LEASE_HELD", "managed worktree already has an active writer")
            if record["status"] not in {
                WorktreeStatus.READY.value,
                WorktreeStatus.COMPLETED.value,
                WorktreeStatus.RETAINED.value,
                WorktreeStatus.FAILED.value,
            }:
                raise WorktreeError(
                    "ILLEGAL_WORKTREE_TRANSITION",
                    f"cannot acquire writer from {record['status']}",
                )
            record["active_writer"] = {
                "participant_id": participant_id,
                "attempt_id": attempt_id,
                "acquired_at": utc_now(),
            }
            return self._write_transition(record, WorktreeStatus.IN_USE)

    def release_writer(
        self,
        worktree_id: str,
        *,
        participant_id: str,
        attempt_id: int,
        outcome: str,
    ) -> dict[str, Any]:
        with secure_file_lock(self.records_root / ".leases.lock"):
            record = self.record(worktree_id)
            active = record.get("active_writer")
            if active is None:
                return record
            if (
                active.get("participant_id") != participant_id
                or int(active.get("attempt_id", -1)) != attempt_id
            ):
                raise WorktreeError("WRITER_LEASE_MISMATCH", "writer cannot release another writer's lease")
            record["active_writer"] = None
            record["last_writer_outcome"] = outcome
            target = {
                "success": WorktreeStatus.COMPLETED,
                "cancelled": WorktreeStatus.RETAINED,
                "failed": WorktreeStatus.FAILED,
                "retry": WorktreeStatus.READY,
            }.get(outcome, WorktreeStatus.RETAINED)
            if target == WorktreeStatus.FAILED and self.is_dirty(record):
                target = WorktreeStatus.RETAINED
                record["failure_retained"] = True
                record["retained_after_run"] = True
            if target == WorktreeStatus.RETAINED:
                record["retained_after_run"] = True
            return self._write_transition(record, target)

    def begin_validation(self, worktree_id: str) -> dict[str, Any]:
        with secure_file_lock(self.records_root / ".leases.lock"):
            record = self.record(worktree_id)
            if record.get("active_writer") is not None:
                raise WorktreeError("WRITER_LEASE_HELD", "validation cannot overlap an active writer")
            return self._write_transition(record, WorktreeStatus.VALIDATING)

    def finish_validation(
        self,
        worktree_id: str,
        validation: dict[str, Any],
    ) -> dict[str, Any]:
        with secure_file_lock(self.records_root / ".leases.lock"):
            record = self.record(worktree_id)
            record["validation"] = validation
            target = WorktreeStatus.COMPLETED if validation.get("success") else WorktreeStatus.RETAINED
            if target == WorktreeStatus.RETAINED:
                record["retained_after_run"] = True
            return self._write_transition(record, target)

    def retain(self, worktree_id: str, *, reason: str) -> dict[str, Any]:
        """Conservatively retain a non-active candidate without deleting data."""

        with secure_file_lock(self.records_root / ".leases.lock"):
            record = self.record(worktree_id)
            if record["status"] in {
                WorktreeStatus.RETAINED.value,
                WorktreeStatus.COMPLETED.value,
                WorktreeStatus.FAILED.value,
            }:
                record["retained_after_run"] = True
                record["retention_reason"] = reason
                return self._write_record(record)
            if record.get("active_writer") is not None:
                raise WorktreeError("WRITER_LEASE_HELD", "active writer must release its lease first")
            record["retained_after_run"] = True
            record["retention_reason"] = reason
            return self._write_transition(record, WorktreeStatus.RETAINED)

    def candidate_result(
        self,
        worktree_id: str,
        *,
        provider_result: dict[str, Any] | None = None,
        validation: dict[str, Any] | None = None,
    ) -> CandidateResult:
        record = self.record(worktree_id)
        path = self._validated_path(record)
        status_bytes = self._git_bytes("status", "--porcelain=v1", "-z", cwd=path)
        changed_files = self._changed_files(status_bytes)
        tracked_diff = self._git_bytes(
            "diff", "--binary", record["base_commit"], "--", cwd=path
        )
        untracked = self._git_bytes(
            "ls-files", "--others", "--exclude-standard", "-z", cwd=path
        ).split(b"\0")
        patch_parts = [tracked_diff]
        for raw in untracked:
            if not raw:
                continue
            relative = Path(os.fsdecode(raw))
            candidate = (path / relative).resolve()
            if path not in candidate.parents:
                raise WorktreeError("PATH_ESCAPE", "untracked file escapes managed worktree")
            completed = self._git_completed(
                "diff", "--no-index", "--binary", "--", "/dev/null", str(relative), cwd=path
            )
            if completed.returncode not in {0, 1}:
                self._raise_git(completed)
            patch_parts.append(completed.stdout)
        artifact = self.workspace.contained("artifacts", "candidates", f"{worktree_id}.patch")
        atomic_write_text(artifact, b"".join(patch_parts).decode("utf-8", errors="replace"))
        summary = self._git_text(
            "diff", "--stat", record["base_commit"], "--", cwd=path, allow_empty=True
        )
        if untracked_names := [os.fsdecode(item) for item in untracked if item]:
            extra = "\n".join(f"untracked: {name}" for name in untracked_names)
            summary = "\n".join(part for part in (summary, extra) if part)
        return CandidateResult(
            base_commit=str(record["base_commit"]),
            worktree_id=worktree_id,
            branch=str(record["branch"]),
            changed_files=changed_files,
            diff_summary=summary[-20_000:],
            git_status=status_bytes.decode("utf-8", errors="replace").replace("\0", "\n")[-20_000:],
            diff_artifact_ref=str(artifact.relative_to(self.workspace.path)),
            validation=validation or dict(record.get("validation", {})),
            provider_result=provider_result or {},
        )

    def reconcile(self, *, active_executions: Iterable[dict[str, Any]] = ()) -> list[dict[str, Any]]:
        active_pairs = {
            (str(item.get("task_id")), str(item.get("participant_id")))
            for item in active_executions
            if item.get("state") in {"running", "cancel_requested", "terminating", "killing"}
            and item.get("liveness", "verified") == "verified"
        }
        uncertain_pairs = {
            (str(item.get("task_id")), str(item.get("participant_id")))
            for item in active_executions
            if item.get("state") in {"running", "cancel_requested", "terminating", "killing"}
            and item.get("liveness") == "unverified"
        }
        discovered = {item.path: item for item in self.discover()}
        reconciled: list[dict[str, Any]] = []
        with secure_file_lock(self.records_root / ".leases.lock"):
            for record in self.records():
                try:
                    self._validate_owned_record(record)
                except WorktreeError:
                    record["status"] = WorktreeStatus.ORPHANED.value
                    record["orphan_reason"] = "ownership or path validation failed"
                    self._write_record(record)
                    reconciled.append(record)
                    continue
                path = Path(record["path"]).resolve()
                listed = discovered.get(path)
                expected_branch = f"refs/heads/{record['branch']}"
                if listed is None or listed.branch != expected_branch:
                    if record["status"] != WorktreeStatus.REMOVED.value:
                        record["status"] = WorktreeStatus.ORPHANED.value
                        record["orphan_reason"] = "Git worktree state does not match durable ownership"
                        self._write_record(record)
                    reconciled.append(record)
                    continue
                if record["status"] == WorktreeStatus.ALLOCATING.value:
                    record["status"] = WorktreeStatus.READY.value
                    record["allocation_recovered_at"] = utc_now()
                    self._write_record(record)
                active = record.get("active_writer")
                if record["status"] == WorktreeStatus.IN_USE.value and active:
                    pair = (str(record["task_id"]), str(active.get("participant_id")))
                    if pair in uncertain_pairs:
                        record["status"] = WorktreeStatus.ORPHANED.value
                        record["orphan_reason"] = "native process identity is unverified"
                        self._write_record(record)
                    elif pair not in active_pairs:
                        record["active_writer"] = None
                        record["recovered_at"] = utc_now()
                        record["status"] = (
                            WorktreeStatus.RETAINED.value
                            if self.is_dirty(record)
                            else WorktreeStatus.READY.value
                        )
                        if record["status"] == WorktreeStatus.RETAINED.value:
                            record["retained_after_run"] = True
                        self._write_record(record)
                reconciled.append(record)
        return reconciled

    def cleanup(self, worktree_id: str) -> dict[str, Any]:
        with secure_file_lock(self.records_root / ".leases.lock"):
            record = self.record(worktree_id)
            self._validate_owned_record(record)
            if record["status"] == WorktreeStatus.REMOVED.value:
                return record
            if record["status"] not in _TERMINAL:
                record["cleanup_decision"] = "retained_non_terminal"
                return self._write_record(record)
            if self.is_dirty(record):
                record["status"] = WorktreeStatus.RETAINED.value
                record["retained_after_run"] = True
                record["cleanup_decision"] = "retained_dirty"
                return self._write_record(record)
            branch_head = self._git_text("rev-parse", "--verify", record["branch"])
            if branch_head != record["base_commit"]:
                record["status"] = WorktreeStatus.RETAINED.value
                record["retained_after_run"] = True
                record["cleanup_decision"] = "retained_unintegrated_commits"
                return self._write_record(record)
            path = self._validated_path(record)
            listed = {item.path: item for item in self.discover()}.get(path)
            if listed is None or listed.branch != f"refs/heads/{record['branch']}":
                record["status"] = WorktreeStatus.ORPHANED.value
                record["cleanup_decision"] = "retained_ownership_mismatch"
                return self._write_record(record)
            started = time.monotonic()
            self._git("worktree", "remove", str(path))
            self._git("branch", "-d", record["branch"])
            record["cleanup_latency_ms"] = round((time.monotonic() - started) * 1000)
            record["cleanup_decision"] = "removed_clean_terminal"
            record["retained_after_run"] = False
            return self._write_transition(record, WorktreeStatus.REMOVED)

    def release_cancelled_leases(self) -> list[dict[str, Any]]:
        released: list[dict[str, Any]] = []
        for record in self.records():
            active = record.get("active_writer")
            if not active:
                if record["status"] in {
                    WorktreeStatus.READY.value,
                    WorktreeStatus.VALIDATING.value,
                }:
                    released.append(
                        self.retain(
                            str(record["worktree_id"]),
                            reason="operator cancellation",
                        )
                    )
                continue
            released.append(
                self.release_writer(
                    str(record["worktree_id"]),
                    participant_id=str(active["participant_id"]),
                    attempt_id=int(active["attempt_id"]),
                    outcome="cancelled",
                )
            )
        return released

    def discover(self) -> tuple[GitWorktree, ...]:
        return parse_worktree_porcelain_z(
            self._git_bytes("worktree", "list", "--porcelain", "-z")
        )

    def records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for path in sorted(self.records_root.glob("wt-*.json")):
            records.append(
                self.workspace.read_json(str(path.relative_to(self.workspace.path)))
            )
        return records

    def status_records(self) -> list[dict[str, Any]]:
        """Return bounded observability data without private absolute paths."""

        statuses: list[dict[str, Any]] = []
        for record in self.records():
            dirty: bool | None
            try:
                dirty = self.is_dirty(record) if Path(str(record["path"])).exists() else None
            except WorktreeError:
                dirty = None
            statuses.append(
                {
                    "worktree_id": record.get("worktree_id"),
                    "task_id": record.get("task_id"),
                    "participant_id": record.get("participant_id"),
                    "status": record.get("status"),
                    "base_commit": str(record.get("base_commit", ""))[:12],
                    "candidate_branch": record.get("branch"),
                    "directory": Path(str(record.get("path", "candidate"))).name,
                    "dirty": dirty,
                    "retained_after_run": bool(record.get("retained_after_run", False)),
                    "allocation_latency_ms": record.get("allocation_latency_ms"),
                    "cleanup_latency_ms": record.get("cleanup_latency_ms"),
                    "active_writer": record.get("active_writer") is not None,
                }
            )
        owned_paths = {Path(str(record["path"])).resolve() for record in self.records()}
        for item in self.discover():
            if item.path in owned_paths:
                continue
            if item.path != self.managed_root and self.managed_root in item.path.parents:
                statuses.append(
                    {
                        "worktree_id": None,
                        "status": WorktreeStatus.ORPHANED.value,
                        "base_commit": str(item.head or "")[:12],
                        "candidate_branch": item.branch,
                        "directory": item.path.name,
                        "dirty": None,
                        "retained_after_run": True,
                        "active_writer": False,
                        "reason": "managed-root worktree has no durable ownership record",
                    }
                )
        return statuses

    def record(self, worktree_id: str) -> dict[str, Any]:
        path = self._record_path(worktree_id)
        if not path.is_file():
            raise WorktreeError("UNKNOWN_WORKTREE", f"unknown managed worktree: {worktree_id}")
        record = self.workspace.read_json(str(path.relative_to(self.workspace.path)))
        self._validate_owned_record(record)
        return record

    def is_dirty(self, record: dict[str, Any]) -> bool:
        path = self._validated_path(record)
        return bool(self._git_bytes("status", "--porcelain=v1", "-z", cwd=path))

    def _default_managed_root(self) -> Path:
        runtime_root = self.workspace.root.parent.resolve()
        if runtime_root == self.repository_root or self.repository_root in runtime_root.parents:
            return (
                self.repository_root.parent
                / f".flowfoundry-worktrees-{self.repository_id[:12]}"
            ).resolve()
        return (runtime_root / "worktrees" / self.repository_id[:16]).resolve()

    def _validated_path(self, record: dict[str, Any]) -> Path:
        path = Path(str(record["path"])).resolve()
        if path == self.managed_root or self.managed_root not in path.parents:
            raise WorktreeError("PATH_ESCAPE", "managed worktree path escapes its root")
        return path

    def _contained_managed(self, *parts: str) -> Path:
        candidate = self.managed_root.joinpath(*parts).resolve()
        if candidate == self.managed_root or self.managed_root not in candidate.parents:
            raise WorktreeError("PATH_ESCAPE", "managed path escapes configured root")
        return candidate

    def _validate_owned_record(self, record: dict[str, Any]) -> None:
        if record.get("owner") != "flowfoundry":
            raise WorktreeError("UNKNOWN_OWNERSHIP", "worktree is not FlowFoundry-owned")
        if record.get("repository_id") != self.repository_id:
            raise WorktreeError("REPOSITORY_MISMATCH", "worktree repository identity changed")
        if Path(str(record.get("managed_root", ""))).resolve() != self.managed_root:
            raise WorktreeError("MANAGED_ROOT_MISMATCH", "worktree managed root changed")
        self._validated_path(record)

    def _write_transition(
        self,
        record: dict[str, Any],
        status: WorktreeStatus,
    ) -> dict[str, Any]:
        current = str(record["status"])
        if status.value != current and status.value not in _TRANSITIONS.get(current, set()):
            raise WorktreeError(
                "ILLEGAL_WORKTREE_TRANSITION",
                f"cannot transition worktree from {current} to {status.value}",
            )
        record["status"] = status.value
        return self._write_record(record)

    def _write_record(self, record: dict[str, Any]) -> dict[str, Any]:
        record["updated_at"] = utc_now()
        atomic_write_json(self._record_path(str(record["worktree_id"])), record)
        return record

    def _record_path(self, worktree_id: str) -> Path:
        if not re.fullmatch(r"wt-[a-f0-9]{20}", worktree_id):
            raise WorktreeError("INVALID_WORKTREE_ID", "invalid managed worktree id")
        return self.records_root / f"{worktree_id}.json"

    def _branch_name(
        self,
        task_id: str,
        participant_id: str,
        attempt_id: int,
        worktree_id: str,
    ) -> str:
        task = sanitize_component(task_id, max_length=28)
        participant = sanitize_component(participant_id, max_length=28)
        return f"flowfoundry/{task}/{participant}/a{attempt_id}-{worktree_id[-8:]}"

    @staticmethod
    def _repository_root(project_root: Path) -> Path:
        completed = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "--show-toplevel"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if completed.returncode != 0:
            raise WorktreeError("WORKTREE_UNAVAILABLE", "project workspace is not a Git repository")
        return Path(completed.stdout.strip()).resolve()

    @staticmethod
    def _repository_identity(repository_root: Path) -> str:
        completed = subprocess.run(
            ["git", "-C", str(repository_root), "rev-parse", "--git-common-dir"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if completed.returncode != 0:
            raise WorktreeError("WORKTREE_UNAVAILABLE", "cannot resolve Git repository identity")
        common_path = Path(completed.stdout.strip())
        if not common_path.is_absolute():
            common_path = repository_root / common_path
        common = str(common_path.resolve())
        return hashlib.sha256(common.encode()).hexdigest()

    def _git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[bytes]:
        completed = self._git_completed(*args, cwd=cwd)
        if completed.returncode != 0:
            self._raise_git(completed)
        return completed

    def _git_completed(
        self,
        *args: str,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", "-C", str(cwd or self.repository_root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _git_bytes(self, *args: str, cwd: Path | None = None) -> bytes:
        return self._git(*args, cwd=cwd).stdout

    def _git_text(
        self,
        *args: str,
        cwd: Path | None = None,
        allow_empty: bool = False,
    ) -> str:
        value = self._git_bytes(*args, cwd=cwd).decode("utf-8", errors="replace").strip()
        if not value and not allow_empty:
            raise WorktreeError("GIT_EMPTY_RESULT", f"Git returned no value for {' '.join(args)}")
        return value

    @staticmethod
    def _raise_git(completed: subprocess.CompletedProcess[bytes]) -> None:
        stderr = completed.stderr.decode("utf-8", errors="replace")[-4000:].strip()
        raise WorktreeError("GIT_COMMAND_FAILED", stderr or "Git command failed")

    @staticmethod
    def _changed_files(status: bytes) -> tuple[str, ...]:
        entries = status.split(b"\0")
        changed: list[str] = []
        index = 0
        while index < len(entries):
            entry = entries[index]
            index += 1
            if not entry:
                continue
            text = os.fsdecode(entry)
            if len(text) < 4:
                continue
            path = text[3:]
            if text[:2] in {"R ", " R", "C ", " C"} and index < len(entries):
                path = os.fsdecode(entries[index])
                index += 1
            changed.append(path)
        return tuple(sorted(set(changed)))

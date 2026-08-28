"""Auditable reconciliation of stale durable run manifests.

The top-level manifest is a cache of operational state, not proof that a native
execution is still alive.  This module derives an effective state from durable
receipts, candidate validation, writer leases, and Durable Process Identity v2.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .execution import ProviderExecutionHandle
from .workspace import RunWorkspace, stable_hash, utc_now


RECONCILER_VERSION = 1
_ACTIVE_EXECUTION_STATES = {"running", "cancel_requested", "terminating", "killing"}
_TERMINAL_EXECUTION_STATES = {
    "cancelled",
    "cancel_unverified",
    "completed",
    "failed",
    "timed_out",
}
_RETAINED_WORKTREE_STATES = {"retained", "failed", "orphaned"}


class ReconciliationState(str, Enum):
    STILL_RUNNING = "still_running"
    COMPLETED = "completed"
    COMPLETED_AWAITING_INTEGRATION = "completed_awaiting_integration"
    FAILED = "failed"
    FAILED_RETAINED = "failed_retained"
    CANCELLED = "cancelled"
    CANCELLED_RETAINED = "cancelled_retained"
    RETAINED_CANDIDATE = "retained_candidate"
    RECONCILIATION_BLOCKED = "reconciliation_blocked"


@dataclass(frozen=True)
class ReconciliationResult:
    applicable: bool
    observed_original_state: str
    reconciled_state: str
    active_process: bool | None
    execution_terminal: bool
    retained: bool
    validated: bool | None
    candidate_commit: bool
    integration_state: str
    confidence: str
    human_action_required: bool
    resume_execution: bool
    reason: str
    evidence: tuple[str, ...]
    evidence_hash: str
    mutation_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DurableRunReconciler:
    """Derive and optionally persist a terminal/retained run classification."""

    def __init__(
        self,
        execution_status_reader: Callable[[Path], list[dict[str, Any]]] | None = None,
    ) -> None:
        self._execution_status_reader = (
            execution_status_reader or ProviderExecutionHandle.recovery_status_for_run
        )

    def reconcile(
        self,
        workspace: RunWorkspace,
        *,
        apply: bool = False,
    ) -> ReconciliationResult:
        manifest = workspace.manifest()
        prior = manifest.get("reconciliation", {}).get("current")
        observed = (
            str(prior.get("observed_original_state", "running"))
            if isinstance(prior, dict)
            else str(manifest.get("status", "unknown"))
        )

        if isinstance(prior, dict) and prior.get("reconciler_version") == RECONCILER_VERSION:
            result = self._evaluate(workspace, manifest, observed)
            if (
                result.applicable
                and prior.get("evidence_hash") == result.evidence_hash
                and prior.get("reconciled_state") == result.reconciled_state
            ):
                return ReconciliationResult(
                    **{**result.to_dict(), "mutation_performed": False}
                )
        else:
            result = self._evaluate(workspace, manifest, observed)

        if not apply or not result.applicable:
            return result

        record = {
            "schema_version": 1,
            "observed_original_state": result.observed_original_state,
            "reconciled_state": result.reconciled_state,
            "reconciliation_reason": result.reason,
            "reconciliation_evidence": list(result.evidence),
            "evidence_hash": result.evidence_hash,
            "reconciled_at": utc_now(),
            "reconciler_version": RECONCILER_VERSION,
            "confidence": result.confidence,
            "human_action_required": result.human_action_required,
        }

        def persist(run_manifest: dict[str, Any]) -> dict[str, Any]:
            reconciliation = run_manifest.setdefault(
                "reconciliation", {"schema_version": 1, "history": []}
            )
            history = reconciliation.setdefault("history", [])
            current = reconciliation.get("current")
            if not (
                isinstance(current, dict)
                and current.get("evidence_hash") == record["evidence_hash"]
                and current.get("reconciled_state") == record["reconciled_state"]
            ):
                history.append(record)
            reconciliation["current"] = record
            run_manifest["status"] = result.reconciled_state
            return run_manifest

        workspace.update_manifest(persist)
        return ReconciliationResult(
            **{**result.to_dict(), "mutation_performed": True}
        )

    def _evaluate(
        self,
        workspace: RunWorkspace,
        manifest: dict[str, Any],
        observed: str,
    ) -> ReconciliationResult:
        evidence: list[str] = []
        facts = self._collect_facts(workspace, evidence)

        if observed != "running":
            return self._result(
                False,
                observed,
                observed,
                facts,
                "high",
                False,
                True,
                "manifest_not_claiming_running",
                evidence,
            )

        meeting = manifest.get("meeting")
        if isinstance(meeting, dict) and meeting.get("state") not in {
            "completed",
            "blocked",
            "failed",
            "cancelled",
            "cancel_unverified",
            "budget_exhausted",
        }:
            return self._result(
                False,
                observed,
                observed,
                facts,
                "high",
                False,
                True,
                "meeting_has_its_own_durable_resume_state",
                evidence,
            )

        retry_authorized = any(
            state.get("status") == "pending" and state.get("retry_requested_at")
            for state in manifest.get("tasks", {}).values()
            if isinstance(state, dict)
        )
        if retry_authorized:
            evidence.append("explicit_retry_request")
            return self._result(
                False,
                observed,
                observed,
                facts,
                "high",
                False,
                True,
                "explicit_retry_is_authorized_to_resume",
                evidence,
            )

        if facts["active_verified"]:
            return self._result(
                True,
                observed,
                ReconciliationState.STILL_RUNNING.value,
                facts,
                "high",
                False,
                False,
                "durable_process_identity_verified_live",
                evidence,
            )
        if facts["active_unverified"]:
            return self._result(
                True,
                observed,
                ReconciliationState.RECONCILIATION_BLOCKED.value,
                facts,
                "low",
                True,
                False,
                "active_execution_identity_cannot_be_verified",
                evidence,
            )

        terminal_classes = facts["terminal_classes"]
        if len(terminal_classes) > 1:
            evidence.append("conflicting_terminal_receipts")
            return self._result(
                True,
                observed,
                ReconciliationState.RECONCILIATION_BLOCKED.value,
                facts,
                "low",
                True,
                False,
                "terminal_receipts_conflict",
                evidence,
            )

        terminal = next(iter(terminal_classes), None)
        retained = facts["retained"]
        if terminal == "cancelled":
            state = (
                ReconciliationState.CANCELLED_RETAINED
                if retained
                else ReconciliationState.CANCELLED
            )
            return self._result(
                True, observed, state.value, facts, "high", False, False,
                "terminal_cancellation_receipt", evidence,
            )
        if terminal == "failed":
            state = ReconciliationState.FAILED_RETAINED if retained else ReconciliationState.FAILED
            return self._result(
                True, observed, state.value, facts, "high", retained, False,
                "terminal_failure_receipt", evidence,
            )
        if terminal == "completed":
            if facts["candidate_commit"] and facts["validated"] is True:
                state = (
                    ReconciliationState.COMPLETED
                    if facts["integration_state"] == "integrated"
                    else ReconciliationState.COMPLETED_AWAITING_INTEGRATION
                )
                return self._result(
                    True,
                    observed,
                    state.value,
                    facts,
                    "high",
                    state is ReconciliationState.COMPLETED_AWAITING_INTEGRATION,
                    False,
                    (
                        "terminal_success_candidate_validated_and_integrated"
                        if state is ReconciliationState.COMPLETED
                        else "terminal_success_candidate_validated_integration_pending"
                    ),
                    evidence,
                )
            return self._result(
                True,
                observed,
                ReconciliationState.COMPLETED.value,
                facts,
                "high",
                False,
                False,
                "terminal_success_receipt",
                evidence,
            )

        if retained and facts["candidate_commit"]:
            return self._result(
                True,
                observed,
                ReconciliationState.RETAINED_CANDIDATE.value,
                facts,
                "medium",
                True,
                False,
                "candidate_retained_without_terminal_execution_receipt",
                evidence,
            )

        evidence.append("no_terminal_receipt")
        return self._result(
            True,
            observed,
            ReconciliationState.RECONCILIATION_BLOCKED.value,
            facts,
            "low",
            True,
            False,
            "process_not_live_but_terminal_evidence_is_incomplete",
            evidence,
        )

    def _collect_facts(self, workspace: RunWorkspace, evidence: list[str]) -> dict[str, Any]:
        terminal_classes: set[str] = set()
        active_verified = False
        active_unverified = False
        for status in self._execution_status_reader(workspace.path):
            state = str(status.get("state", "unknown"))
            if state in _ACTIVE_EXECUTION_STATES:
                liveness = status.get("liveness")
                if liveness == "verified":
                    active_verified = True
                    evidence.append("process_identity_verified_live")
                elif liveness == "missing":
                    evidence.append("persisted_process_identity_gone")
                else:
                    active_unverified = True
                    evidence.append("persisted_process_identity_unverified")
            elif state in _TERMINAL_EXECUTION_STATES:
                terminal_classes.add(self._terminal_class(state))
                evidence.append(f"terminal_execution:{state}")

        for path in sorted(workspace.contained("tasks").glob("*/result.json")):
            record = self._read_json(path)
            if record is None:
                continue
            terminal = self._result_terminal_class(record)
            if terminal:
                terminal_classes.add(terminal)
                evidence.append(f"terminal_task_result:{terminal}")

        validated_values: set[bool] = set()
        candidate_commit = False
        for path in sorted(workspace.contained("artifacts/candidates").glob("*.json")):
            record = self._read_json(path)
            if record is None:
                continue
            provider_result = record.get("provider_result")
            if isinstance(provider_result, dict) and isinstance(
                provider_result.get("success"), bool
            ):
                terminal_classes.add("completed" if provider_result["success"] else "failed")
                evidence.append(
                    "terminal_candidate_result:"
                    + ("completed" if provider_result["success"] else "failed")
                )
            validation = record.get("validation")
            if isinstance(validation, dict):
                if isinstance(validation.get("success"), bool):
                    validated_values.add(validation["success"])
                    evidence.append(
                        "candidate_validation:"
                        + ("passed" if validation["success"] else "failed")
                    )
                candidate_commit = candidate_commit or bool(validation.get("candidate_commit"))
                if validation.get("candidate_commit"):
                    evidence.append("candidate_commit_recorded")

        retained = False
        integration_state = "unknown"
        for path in sorted(workspace.contained("worktrees").glob("wt-*.json")):
            record = self._read_json(path)
            if record is None:
                continue
            retained = retained or bool(record.get("retained_after_run")) or str(
                record.get("status")
            ) in _RETAINED_WORKTREE_STATES
            if record.get("active_writer") is None:
                evidence.append("writer_lease_released")
            if bool(record.get("retained_after_run")) or str(record.get("status")) in {
                "retained",
                "failed",
                "orphaned",
            }:
                evidence.append("worktree_retained")
            writer_outcome = str(record.get("last_writer_outcome", ""))
            if writer_outcome in {"success", "failed", "cancelled"}:
                terminal_classes.add(
                    "completed" if writer_outcome == "success" else writer_outcome
                )
                evidence.append(f"terminal_writer_receipt:{writer_outcome}")
            validation = record.get("validation")
            if isinstance(validation, dict) and isinstance(validation.get("success"), bool):
                validated_values.add(validation["success"])
                evidence.append(
                    "worktree_validation:"
                    + ("passed" if validation["success"] else "failed")
                )
            if record.get("cleanup_decision") == "retained_unintegrated_commits":
                candidate_commit = True
                integration_state = "pending"
                evidence.append("retained_unintegrated_candidate_commit")
            if record.get("integration_state") in {"integrated", "pending", "not_required"}:
                integration_state = str(record["integration_state"])

        if candidate_commit and integration_state == "unknown":
            integration_state = "pending"
        validated: bool | None = None
        if validated_values == {True}:
            validated = True
        elif validated_values == {False}:
            validated = False
        elif validated_values:
            evidence.append("conflicting_validation_records")

        return {
            "active_verified": active_verified,
            "active_unverified": active_unverified,
            "terminal_classes": terminal_classes,
            "retained": retained,
            "validated": validated,
            "candidate_commit": candidate_commit,
            "integration_state": integration_state,
        }

    @staticmethod
    def _terminal_class(state: str) -> str:
        if state in {"cancelled", "cancel_unverified"}:
            return "cancelled"
        if state in {"failed", "timed_out"}:
            return "failed"
        return "completed"

    @classmethod
    def _result_terminal_class(cls, record: dict[str, Any]) -> str | None:
        if record.get("cancelled") is True:
            return "cancelled"
        termination = record.get("termination")
        if isinstance(termination, dict):
            state = termination.get("status") or termination.get("state")
            if state in _TERMINAL_EXECUTION_STATES:
                return cls._terminal_class(str(state))
        state = record.get("state") or record.get("status")
        if state in _TERMINAL_EXECUTION_STATES:
            return cls._terminal_class(str(state))
        if isinstance(record.get("success"), bool):
            return "completed" if record["success"] else "failed"
        return None

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    @staticmethod
    def _result(
        applicable: bool,
        observed: str,
        state: str,
        facts: dict[str, Any],
        confidence: str,
        human_action: bool,
        resume_execution: bool,
        reason: str,
        evidence: list[str],
    ) -> ReconciliationResult:
        evidence_tuple = tuple(sorted(set(evidence)))
        evidence_hash = stable_hash(
            {
                "observed": observed,
                "state": state,
                "reason": reason,
                "evidence": evidence_tuple,
                "retained": facts["retained"],
                "validated": facts["validated"],
                "candidate_commit": facts["candidate_commit"],
                "integration_state": facts["integration_state"],
            }
        )
        return ReconciliationResult(
            applicable=applicable,
            observed_original_state=observed,
            reconciled_state=state,
            active_process=(
                True
                if facts["active_verified"]
                else (None if facts["active_unverified"] else False)
            ),
            execution_terminal=bool(facts["terminal_classes"]),
            retained=bool(facts["retained"]),
            validated=facts["validated"],
            candidate_commit=bool(facts["candidate_commit"]),
            integration_state=str(facts["integration_state"]),
            confidence=confidence,
            human_action_required=human_action,
            resume_execution=resume_execution,
            reason=reason,
            evidence=evidence_tuple,
            evidence_hash=evidence_hash,
        )

"""Human approval policy for hazardous task classes."""

from __future__ import annotations

from dataclasses import dataclass

from .models import RiskLevel, TaskSpec
from .workspace import RunWorkspace, atomic_write_json, utc_now

HUMAN_GATED_ACTIONS = frozenset(
    {
        "push",
        "force_push",
        "protected_branch_merge",
        "delete",
        "repository_rename",
        "deployment",
        "release",
        "external_message",
        "credential_access",
        "high_risk_shell",
    }
)


@dataclass(frozen=True)
class ApprovalDecision:
    allowed: bool
    pending_actions: tuple[str, ...] = ()
    reason: str = ""


class ApprovalGate:
    def required_actions(self, task: TaskSpec) -> tuple[str, ...]:
        requested = set(task.approval_requirements)
        action = task.inputs.get("action")
        if isinstance(action, str) and action in HUMAN_GATED_ACTIONS:
            requested.add(action)
        if task.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL} and not requested:
            requested.add("high_risk_shell")
        return tuple(sorted(requested.intersection(HUMAN_GATED_ACTIONS)))

    def evaluate(self, workspace: RunWorkspace, task: TaskSpec) -> ApprovalDecision:
        required = self.required_actions(task)
        if not required:
            return ApprovalDecision(True)
        approval_path = workspace.contained("approvals", f"{task.id}.json")
        if approval_path.exists():
            record = workspace.read_json(str(approval_path.relative_to(workspace.path)))
            granted = set(record.get("granted_actions", ()))
            if set(required).issubset(granted) and record.get("status") == "approved":
                return ApprovalDecision(True)
        reason = f"human approval required for: {', '.join(required)}"
        atomic_write_json(
            approval_path,
            {
                "schema_version": 1,
                "task_id": task.id,
                "status": "pending",
                "required_actions": required,
                "created_at": utc_now(),
            },
        )
        workspace.append_human_action(task.id, reason)
        return ApprovalDecision(False, required, reason)

    def record_approval(
        self,
        workspace: RunWorkspace,
        task_id: str,
        actions: tuple[str, ...],
        actor: str,
    ) -> None:
        if not actor.strip():
            raise ValueError("approval actor is required")
        unknown = set(actions) - HUMAN_GATED_ACTIONS
        if unknown:
            raise ValueError(f"unknown approval actions: {sorted(unknown)}")
        atomic_write_json(
            workspace.contained("approvals", f"{task_id}.json"),
            {
                "schema_version": 1,
                "task_id": task_id,
                "status": "approved",
                "granted_actions": actions,
                "actor": actor,
                "approved_at": utc_now(),
            },
        )

"""Orchestration policy helpers kept independent from provider implementations."""

from __future__ import annotations

from .approvals import HUMAN_GATED_ACTIONS
from .models import TaskSpec


def requested_action(task: TaskSpec) -> str | None:
    action = task.inputs.get("action")
    return action if isinstance(action, str) else None


def has_implicit_hazard(task: TaskSpec) -> bool:
    action = requested_action(task)
    return action in HUMAN_GATED_ACTIONS if action else False

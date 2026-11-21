"""Small session-wide permission ceiling contract."""

from __future__ import annotations

from enum import IntEnum


class PermissionLevel(IntEnum):
    READ_ONLY = 1
    PROJECT_AUTO = 2
    CONFIRM = 3
    FULL = 4


SESSION_PERMISSION_CEILINGS = {
    PermissionLevel.READ_ONLY: {
        "level": int(PermissionLevel.READ_ONLY),
        "name": "只读规划",
        "detail": "read-only",
        "read_only": True,
    },
    PermissionLevel.PROJECT_AUTO: {
        "level": int(PermissionLevel.PROJECT_AUTO),
        "name": "项目内自动修改",
        "detail": "workspace-write",
        "read_only": False,
    },
    PermissionLevel.CONFIRM: {
        "level": int(PermissionLevel.CONFIRM),
        "name": "手动确认",
        "detail": "session ceiling",
        "read_only": False,
    },
    PermissionLevel.FULL: {
        "level": int(PermissionLevel.FULL),
        "name": "完全访问",
        "detail": "maximum ceiling",
        "read_only": False,
    },
}


def normalize_level(value: int | str | None) -> int:
    try:
        level = int(value) if value is not None else int(PermissionLevel.PROJECT_AUTO)
    except (TypeError, ValueError):
        level = int(PermissionLevel.PROJECT_AUTO)
    return max(int(PermissionLevel.READ_ONLY), min(int(PermissionLevel.FULL), level))


def session_permission(value: int | str | PermissionLevel) -> dict[str, object]:
    """Return the canonical display/runtime contract for one session ceiling."""
    level = PermissionLevel(normalize_level(value))
    return dict(SESSION_PERMISSION_CEILINGS[level])


def worker_level(session_level: int | str | None, capability: str) -> int:
    """Assign the least useful level while never exceeding the session ceiling."""
    ceiling = normalize_level(session_level)
    required = 1 if capability in {"research", "general"} else 3
    return min(ceiling, required)

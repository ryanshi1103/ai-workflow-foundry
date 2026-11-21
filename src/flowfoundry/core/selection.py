"""Minimum-sufficient capability selection for the default product path."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class TaskKind(StrEnum):
    CODING = "coding"
    RESEARCH = "research"
    GENERAL = "general"


@dataclass(frozen=True)
class PathSelection:
    task_kind: TaskKind
    required_capabilities: tuple[str, ...]
    executor: str
    broker_requested: bool
    needs_second_opinion: bool
    reason: str
    expected_result: str
    verification_hint: str


_CODING = (
    "repo",
    "repository",
    "code",
    "bug",
    "test",
    "python",
    "文件",
    "代码",
    "测试",
    "tests",
    "修复",
    "仓库",
    "implement",
    "improvement",
    "improve",
    "refactor",
    "modify",
    "maintenance",
)
# Verbs alone are not coding. They count only with a code/object/path cue, so
# "fix my schedule" stays general while "fix coordinator timeout" can write.
_IMPLEMENT_VERBS = (
    "fix",
    "repair",
    "add",
    "update",
    "patch",
    "wire",
    "introduce",
    "接入",
    "添加",
    "增加",
    "更新",
    "实现",
    "修改",
)
_IMPLEMENT_OBJECTS = (
    "mapping",
    "provider",
    "client",
    "module",
    "function",
    "class",
    "timeout",
    "handler",
    "adapter",
    "cli",
    "sdk",
    "api",
    "coordinator",
    "launcher",
    "executor",
    "broker",
    "readme",
    "file",
    "files",
    "映射",
    "模块",
    "函数",
    "超时",
    "适配",
    "接口",
)
_PATH = re.compile(
    r"(?<![a-z0-9])(?:[\w.-]+/)+[\w.-]+"
    r"|(?<![a-z0-9])[\w.-]+\.(?:py|ts|tsx|js|jsx|mjs|cjs|go|rs|toml|md)(?![a-z0-9])",
    re.IGNORECASE,
)
_CURRENT_RESEARCH = (
    "latest",
    "recent",
    "last month",
    "today",
    "current news",
    "real-time",
    "twitter",
    "最近",
    "近一个月",
    "实时",
    "最新",
    "新闻",
    "查询",
)
_RESEARCH = ("research", "sources", "source", "调查", "研究", "来源")
_SECOND_OPINION = (
    "material conflict",
    "high uncertainty",
    "independent opinion",
    "重大冲突",
    "高度不确定",
    "独立意见",
)


def select_path(
    goal: str,
    *,
    expected_artifact: str | None = None,
    acceptance_criteria: str | None = None,
    requested_capability: str | None = None,
) -> PathSelection:
    folded = goal.casefold()

    def contains(marker: str) -> bool:
        if marker.isascii() and marker.replace("-", "").replace(" ", "").isalpha():
            return bool(re.search(rf"(?<![a-z]){re.escape(marker)}(?![a-z])", folded))
        return marker in folded

    contract = f"{expected_artifact or ''} {acceptance_criteria or ''}".casefold()
    contract_coding = any(word in contract for word in ("test", "code", "repository", "build", "lint", "type-check", "changed files"))
    contract_research = any(word in contract for word in ("source", "url", "fresh", "citation", "current intelligence"))
    implement = any(contains(marker) for marker in _IMPLEMENT_VERBS) and (
        any(contains(marker) for marker in _IMPLEMENT_OBJECTS) or bool(_PATH.search(folded))
    )
    coding = contract_coding or implement or any(contains(marker) for marker in _CODING)
    current = any(contains(marker) for marker in _CURRENT_RESEARCH)
    research = current or (any(contains(marker) for marker in _RESEARCH) and not contract_coding)
    if requested_capability and requested_capability.casefold() in {"coding", "research", "general"}:
        requested = TaskKind(requested_capability.casefold())
        if requested == TaskKind.CODING and not contract_research:
            coding, research = True, False
        elif requested == TaskKind.RESEARCH and not contract_coding:
            coding, research = False, True
    second_opinion = any(contains(marker) for marker in _SECOND_OPINION)

    if coding:
        return PathSelection(
            task_kind=TaskKind.CODING,
            required_capabilities=("coding", "repo_read", "repo_write", "tool_use"),
            executor="codex",
            broker_requested=False,
            needs_second_opinion=second_opinion,
            reason="The goal is a repository task; one coding executor is sufficient.",
            expected_result="A concrete repository result, with changed files only when needed.",
            verification_hint="Prefer tests, lint, type checks, build, and Git diff checks.",
        )
    if research:
        capabilities = ("web_current", "research", "source_citation") if current else (
            "research",
            "source_citation",
        )
        return PathSelection(
            task_kind=TaskKind.RESEARCH,
            required_capabilities=capabilities,
            executor="codex",
            broker_requested=current,
            needs_second_opinion=second_opinion,
            reason=(
                "Current external context may improve routing and source discovery."
                if current
                else "One research-capable executor is sufficient."
            ),
            expected_result="A concise answer whose material claims trace to sources.",
            verification_hint="Require sources; prefer fresh official or primary sources and surface contradictions.",
        )
    return PathSelection(
        task_kind=TaskKind.GENERAL,
        required_capabilities=("general_reasoning", "tool_use"),
        executor="codex",
        broker_requested=False,
        needs_second_opinion=second_opinion,
        reason="No specialized capability is clearly required; one executor is sufficient.",
        expected_result="A direct result that answers the goal.",
        verification_hint="Use deterministic checks when available; otherwise report uncertainty.",
    )

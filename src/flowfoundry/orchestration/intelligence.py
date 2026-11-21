"""Deterministic task profiling and minimum-sufficient-path selection."""

from __future__ import annotations

from typing import Any

from .models import ExecutionMode, RoutingDecision, TaskProfile


def _contains(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


class RuleBasedTaskAnalyzer:
    """Cheap first pass that is inspectable, overridable, and uses no model call."""

    _ARCHITECTURE = ("architecture", "architect", "system design", "架构", "系统设计", "重构")
    _RESEARCH = ("research", "investigate", "compare", "latest", "调研", "研究", "比较", "最新")
    _CODING = (
        "code", "implement", "build", "fix", "bug", "refactor", "test", "api", "cli",
        "代码", "实现", "开发", "修复", "测试", "接口", "命令行",
    )
    _DOCUMENTATION = ("document", "readme", "docs", "copyedit", "文档", "说明", "校对")
    _MULTIMODAL = ("image", "video", "audio", "pdf", "media", "图片", "视频", "音频", "媒体")
    _HIGH_RISK = (
        "production", "deploy", "release", "database", "migration", "delete", "security",
        "credential", "auth", "payment", "生产", "部署", "发布", "数据库", "迁移", "删除",
        "安全", "凭证", "认证", "支付",
    )
    _IRREVERSIBLE = ("delete", "drop", "force push", "rewrite history", "删除", "清空", "强推", "重写历史")
    _UNCERTAIN = ("unknown", "unclear", "explore", "diagnose", "why", "未知", "不确定", "探索", "诊断", "为什么")
    _LARGE = ("entire", "whole", "large", "monorepo", "repository audit", "全部", "整个", "大型", "全仓库", "审计")
    _HIGH_IMPACT = ("critical", "core", "v1", "launch", "customer", "关键", "核心", "上线", "客户")
    _PRIVATE = ("private", "secret", "credential", "personal", "local only", "隐私", "秘密", "凭证", "仅本地")

    def analyze(self, goal: str, overrides: dict[str, Any] | None = None) -> TaskProfile:
        clean_goal = goal.strip()
        if not clean_goal:
            raise ValueError("goal must not be empty")
        text = clean_goal.casefold()
        architecture = _contains(text, self._ARCHITECTURE)
        research = _contains(text, self._RESEARCH)
        coding = _contains(text, self._CODING)
        documentation = _contains(text, self._DOCUMENTATION)
        multimodal = _contains(text, self._MULTIMODAL)
        high_risk = _contains(text, self._HIGH_RISK)
        uncertain = _contains(text, self._UNCERTAIN)
        large = _contains(text, self._LARGE) or len(clean_goal) > 500
        high_impact = _contains(text, self._HIGH_IMPACT)
        private = _contains(text, self._PRIVATE)

        if architecture:
            task_type = "architecture"
        elif research:
            task_type = "research"
        elif coding:
            task_type = "coding"
        elif documentation:
            task_type = "documentation"
        else:
            task_type = "general"

        complexity = 2 + int(architecture) + int(large) + int(research and coding)
        uncertainty = 1 + int(uncertain) * 2 + int(research) + int(architecture)
        impact = 2 + int(high_impact) * 2 + int(high_risk)
        failure_risk = 1 + int(high_risk) * 2 + int(architecture)
        evidence = [f"classified as {task_type}"]
        if large:
            evidence.append("large-context language detected")
        if high_risk:
            evidence.append("high-risk domain language detected")
        if uncertain:
            evidence.append("uncertainty language detected")
        if multimodal:
            evidence.append("multimodal input requested")

        profile = TaskProfile(
            task_type=task_type,
            complexity=min(complexity, 5),
            uncertainty=min(uncertainty, 5),
            impact=min(impact, 5),
            failure_risk=min(failure_risk, 5),
            reversibility="hard" if _contains(text, self._IRREVERSIBLE) else ("moderate" if high_risk else "easy"),
            context_size="large" if large else ("medium" if len(clean_goal) > 180 else "small"),
            coding_requirement=coding,
            research_requirement=research,
            multimodal_requirement=multimodal,
            privacy_requirement="high" if private else "normal",
            estimated_workload="large" if large else ("medium" if complexity >= 3 else "small"),
            expected_quality=5 if high_risk or high_impact else 3,
            evidence=tuple(evidence),
        )
        if overrides:
            unknown = set(overrides) - set(profile.to_dict())
            if unknown:
                raise ValueError(f"unknown task profile fields: {sorted(unknown)}")
            merged = {**profile.to_dict(), **overrides}
            profile = TaskProfile.from_dict(merged)
        return profile

    def decide(
        self,
        profile: TaskProfile,
        requested_mode: str | ExecutionMode | None = None,
    ) -> RoutingDecision:
        if requested_mode is not None:
            mode = ExecutionMode(requested_mode)
            return RoutingDecision(mode, ("operator explicitly selected execution mode",), self._calls(mode, profile))

        reasons: list[str] = []
        needs_team = (
            profile.complexity >= 4
            or profile.uncertainty >= 4
            or (profile.task_type == "architecture" and profile.complexity >= 3)
            or (profile.research_requirement and profile.coding_requirement)
            or (profile.multimodal_requirement and profile.coding_requirement)
        )
        if needs_team:
            mode = ExecutionMode.MULTI_AGENT
            if profile.complexity >= 4:
                reasons.append("complexity requires complementary roles")
            if profile.uncertainty >= 4:
                reasons.append("uncertainty benefits from independent challenge")
            if profile.task_type == "architecture":
                reasons.append("architecture benefits from an independent decision role")
            if profile.research_requirement and profile.coding_requirement:
                reasons.append("research and implementation capabilities are both required")
        elif (
            profile.failure_risk >= 3
            or profile.impact >= 4
            or profile.expected_quality >= 5
            or profile.privacy_requirement == "high"
        ):
            mode = ExecutionMode.SINGLE_AGENT_REVIEWER
            reasons.append("independent review is justified by risk, impact, privacy, or quality")
        else:
            mode = ExecutionMode.SINGLE_AGENT
            reasons.append("one capable agent is sufficient for the assessed task")
        return RoutingDecision(mode, tuple(reasons), self._calls(mode, profile))

    @staticmethod
    def _calls(mode: ExecutionMode, profile: TaskProfile) -> int:
        if mode == ExecutionMode.SINGLE_AGENT:
            return 1
        if mode == ExecutionMode.SINGLE_AGENT_REVIEWER:
            return 2
        return (
            2
            + int(
                profile.task_type in {"architecture", "research"}
                or not profile.coding_requirement
            )
            + int(profile.coding_requirement)
        )

"""Keep consequential authority with the human, without a governance framework."""

from __future__ import annotations

from dataclasses import dataclass


_HUMAN_ACTIONS = {
    "push": (
        "git push",
        "push to",
        "push this",
        "push origin",
        "push the branch",
        "push branch",
        "推送",
    ),
    "publish": ("publish", "发布到", "公开发布"),
    "release": (
        "create a release",
        "github release",
        "gh release",
        "发布版本",
        "正式发布",
        "创建 release",
    ),
    "deploy": ("deploy", "部署到", "上线"),
    "purchase": ("purchase", "buy ", "付款", "购买"),
    "external_message": ("send email", "send a message", "发送邮件", "发送消息"),
    "destructive_delete": ("delete permanently", "永久删除", "清空数据"),
}


@dataclass(frozen=True)
class AuthorityDecision:
    preparation_allowed: bool
    human_actions: tuple[str, ...]

    @property
    def human_required(self) -> bool:
        return bool(self.human_actions)


def assess_authority(goal: str) -> AuthorityDecision:
    """Identify only the small set of irreversible or external actions we gate."""

    folded = goal.casefold()
    actions = tuple(
        action
        for action, markers in _HUMAN_ACTIONS.items()
        if any(marker in folded for marker in markers)
    )
    return AuthorityDecision(preparation_allowed=True, human_actions=actions)

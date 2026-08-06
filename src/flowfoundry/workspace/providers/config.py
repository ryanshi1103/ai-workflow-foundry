"""Portable provider and permission configuration for workspace launches.

Only provider-independent, machine-safe settings live here. Authentication,
tokens, generated profiles, endpoints, and local network metadata remain in
the user's own provider configuration directories.
"""

from __future__ import annotations

import os
from collections.abc import MutableMapping
from pathlib import Path

CLAUDE_PERMISSION_MODES = {
    "m": {"mode": "default", "name": "Manual", "bypass": False},
    "e": {"mode": "acceptEdits", "name": "acceptEdits", "bypass": False},
    "p": {"mode": "plan", "name": "plan (只分析)", "bypass": False},
    "a": {"mode": "auto", "name": "auto", "bypass": False},
    "b": {
        "mode": "bypassPermissions",
        "name": "bypassPermissions",
        "bypass": True,
    },
}

CODEX_PROFILES = {
    "m": {
        "profile": "gpt56-sol-manual",
        "name": "手动确认 (workspace-write + on-request)",
        "is_full": False,
    },
    "p": {
        "profile": "gpt56-sol-readonly",
        "name": "只读规划 (read-only + never)",
        "is_full": False,
    },
    "a": {
        "profile": "gpt56-sol-auto",
        "name": "项目内自动执行 (workspace-write + never)",
        "is_full": False,
    },
    "b": {
        "profile": "gpt56-sol-full",
        "name": "完全访问 ⚠️ (danger-full-access + never)",
        "is_full": True,
    },
}

PROVIDER_NAMES = {
    "c": "Claude (Anthropic 原生)",
    "d": "DeepSeek V4 Pro",
    "o": "OpenAI Codex (GPT-5.6 Sol)",
}

_ANTHROPIC_ENVIRONMENT_KEYS = (
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL",
    "CLAUDE_CODE_EFFORT_LEVEL",
)


def claude_config_dir(provider: str, *, home: Path | None = None) -> Path:
    """Return the isolated Claude-compatible config directory for a provider."""
    provider_home = home or Path.home()
    directory = ".claude-deepseek" if provider == "deepseek" else ".claude-native"
    return provider_home / directory


def prepare_claude_environment(
    provider: str,
    environment: MutableMapping[str, str] | None = None,
) -> MutableMapping[str, str]:
    """Select a provider config without importing credentials into FlowFoundry."""
    target = environment if environment is not None else os.environ
    target["CLAUDE_CONFIG_DIR"] = str(claude_config_dir(provider))
    if provider == "claude":
        for key in _ANTHROPIC_ENVIRONMENT_KEYS:
            target.pop(key, None)
    return target

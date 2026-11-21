"""Small replaceable Grok broker contract with a deterministic fallback."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Sequence


_ENDPOINT = "https://api.x.ai/v1/responses"
_DEFAULT_MODEL = "grok-4.6"
_MAX_RESPONSE_BYTES = 1_000_000


@dataclass(frozen=True)
class BrokerDecision:
    selected_executor: str
    selected_capabilities: tuple[str, ...]
    selected_tools: tuple[str, ...]
    reason: str
    execution_instruction: str
    expected_result: str
    needs_second_opinion: bool
    verification_hint: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> BrokerDecision:
        return cls(
            selected_executor=str(value.get("selected_executor", "codex")),
            selected_capabilities=tuple(
                str(item) for item in value.get("selected_capabilities", ())
            ),
            selected_tools=tuple(str(item) for item in value.get("selected_tools", ())),
            reason=str(value.get("reason", "")),
            execution_instruction=str(value.get("execution_instruction", "")),
            expected_result=str(value.get("expected_result", "")),
            needs_second_opinion=bool(value.get("needs_second_opinion", False)),
            verification_hint=(
                str(value["verification_hint"])
                if value.get("verification_hint")
                else None
            ),
        )


@dataclass(frozen=True)
class BrokerOutcome:
    status: str
    used: bool
    decision: BrokerDecision
    reason: str
    usage: dict[str, Any] | None = None


def _fallback(
    capabilities: Sequence[str], expected_result: str, verification_hint: str
) -> BrokerDecision:
    return BrokerDecision(
        selected_executor="codex",
        selected_capabilities=tuple(capabilities),
        selected_tools=("web",) if "web_current" in capabilities else (),
        reason="Deterministic fallback selected the available executor by capability.",
        execution_instruction=(
            "Use current official or primary web sources and include direct source URLs."
            if "web_current" in capabilities
            else "Execute the goal directly with the available capabilities."
        ),
        expected_result=expected_result,
        needs_second_opinion=False,
        verification_hint=verification_hint,
    )


def _schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "selected_executor": {"type": "string", "enum": ["codex"]},
            "selected_capabilities": {"type": "array", "items": {"type": "string"}},
            "selected_tools": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"},
            "execution_instruction": {"type": "string"},
            "expected_result": {"type": "string"},
            "needs_second_opinion": {"type": "boolean"},
            "verification_hint": {"type": ["string", "null"]},
        },
        "required": [
            "selected_executor",
            "selected_capabilities",
            "selected_tools",
            "reason",
            "execution_instruction",
            "expected_result",
            "needs_second_opinion",
            "verification_hint",
        ],
    }


def _extract(response: dict[str, Any]) -> dict[str, Any]:
    for item in response.get("output", ()):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for block in item.get("content", ()):
            if isinstance(block, dict) and block.get("type") == "output_text":
                value = json.loads(str(block.get("text", "")))
                if isinstance(value, dict):
                    return value
    raise ValueError("Grok broker returned no structured decision")


def broker_goal(
    *,
    goal: str,
    relevant_context: str,
    capabilities: Sequence[str],
    expected_result: str,
    verification_hint: str,
    requested: bool,
    timeout_seconds: float = 60.0,
) -> BrokerOutcome:
    """Use Grok only when requested and available; otherwise fail open to fallback."""

    fallback = _fallback(capabilities, expected_result, verification_hint)
    if not requested:
        return BrokerOutcome("SKIPPED", False, fallback, "The goal has an obvious single path.")
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        return BrokerOutcome(
            "DEFERRED",
            False,
            fallback,
            "Grok was useful for current-context routing but XAI_API_KEY is unavailable.",
        )

    prompt = {
        "goal": goal,
        "relevant_context": relevant_context,
        "available_capabilities": list(capabilities),
        "instruction": (
            "Select the minimum sufficient capability path. You are an optional broker, "
            "not project authority, memory, executor, or evaluator."
        ),
    }
    payload = {
        "model": os.environ.get("FLOWFOUNDRY_GROK_MODEL", _DEFAULT_MODEL),
        "input": json.dumps(prompt, ensure_ascii=False),
        "store": False,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "flowfoundry_broker_decision",
                "schema": _schema(),
                "strict": True,
            }
        },
    }
    request = urllib.request.Request(
        _ENDPOINT,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
        if len(raw) > _MAX_RESPONSE_BYTES:
            raise ValueError("response too large")
        response_value = json.loads(raw)
        decision = BrokerDecision.from_dict(_extract(response_value))
        if decision.selected_executor != "codex":
            raise ValueError("broker selected an unavailable executor")
        usage = response_value.get("usage")
        return BrokerOutcome(
            "WORKING",
            True,
            decision,
            "Grok supplied the optional semantic routing decision.",
            usage if isinstance(usage, dict) else None,
        )
    except (
        OSError,
        TimeoutError,
        ValueError,
        json.JSONDecodeError,
        urllib.error.URLError,
    ) as exc:
        return BrokerOutcome(
            "FALLBACK",
            False,
            fallback,
            f"Grok broker failed cleanly ({type(exc).__name__}); deterministic fallback used.",
        )

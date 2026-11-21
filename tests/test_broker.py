from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from flowfoundry.broker.semantic import broker_goal


class _Response:
    def __init__(self, value: dict[str, object]) -> None:
        self.value = json.dumps(value).encode()

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, limit: int) -> bytes:
        return self.value[:limit]


class BrokerTests(unittest.TestCase):
    def test_obvious_goal_skips_broker_even_when_key_exists(self) -> None:
        with patch.dict(os.environ, {"XAI_API_KEY": "secret"}), patch(
            "flowfoundry.broker.semantic.urllib.request.urlopen"
        ) as request:
            outcome = broker_goal(
                goal="fix one test",
                relevant_context="none",
                capabilities=("coding",),
                expected_result="fixed test",
                verification_hint="run tests",
                requested=False,
            )
        self.assertEqual(outcome.status, "SKIPPED")
        self.assertFalse(outcome.used)
        request.assert_not_called()

    def test_missing_key_cleanly_uses_fallback(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            outcome = broker_goal(
                goal="latest agent changes",
                relevant_context="none",
                capabilities=("web_current", "research"),
                expected_result="three changes",
                verification_hint="official sources",
                requested=True,
            )
        self.assertEqual(outcome.status, "DEFERRED")
        self.assertEqual(outcome.decision.selected_executor, "codex")
        self.assertIn("web", outcome.decision.selected_tools)

    def test_grok_maps_into_small_provider_neutral_contract(self) -> None:
        decision = {
            "selected_executor": "codex",
            "selected_capabilities": ["web_current", "research"],
            "selected_tools": ["web"],
            "reason": "Current sources are needed.",
            "execution_instruction": "Use official changelogs.",
            "expected_result": "Three cited changes.",
            "needs_second_opinion": False,
            "verification_hint": "Check dates.",
        }
        response = {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": json.dumps(decision)}],
                }
            ],
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
        captured: dict[str, object] = {}

        def urlopen(request: object, timeout: float) -> _Response:
            captured["authorization"] = request.get_header("Authorization")
            captured["payload"] = json.loads(request.data)
            return _Response(response)

        with patch.dict(os.environ, {"XAI_API_KEY": "secret"}, clear=True), patch(
            "flowfoundry.broker.semantic.urllib.request.urlopen", side_effect=urlopen
        ):
            outcome = broker_goal(
                goal="latest changes",
                relevant_context="bounded",
                capabilities=("web_current", "research"),
                expected_result="three changes",
                verification_hint="official sources",
                requested=True,
            )

        self.assertTrue(outcome.used)
        self.assertEqual(outcome.status, "WORKING")
        self.assertEqual(outcome.decision.execution_instruction, "Use official changelogs.")
        self.assertEqual(captured["authorization"], "Bearer secret")
        self.assertFalse(captured["payload"]["store"])
        self.assertNotIn("secret", json.dumps(captured["payload"]))


if __name__ == "__main__":
    unittest.main()

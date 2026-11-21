"""Legacy team-runtime Grok process adapter.

The default product uses :mod:`flowfoundry.broker.semantic`.  This compatibility
adapter remains only so old persisted team plans do not point at a missing
module; new product code must not import it.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

from .providers import _RESULT_SCHEMA

_ENDPOINT = "https://api.x.ai/v1/responses"
_MAX_RESPONSE_BYTES = 8_000_000


def main() -> int:
    api_key = os.environ.get("XAI_API_KEY")
    prompt = sys.stdin.read()
    if not api_key or not prompt.strip():
        print("legacy Grok executor is not configured", file=sys.stderr)
        return 2
    payload = {
        "model": os.environ.get("FLOWFOUNDRY_GROK_MODEL", "grok-4.6"),
        "input": prompt,
        "store": False,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "flowfoundry_provider_result",
                "schema": _RESULT_SCHEMA,
                "strict": True,
            }
        },
    }
    request = urllib.request.Request(
        _ENDPOINT,
        data=json.dumps(payload, separators=(",", ":")).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=360.0) as response:
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
        if len(raw) > _MAX_RESPONSE_BYTES:
            raise ValueError("response too large")
        value = json.loads(raw)
        structured: dict[str, Any] | None = None
        for item in value.get("output", ()):
            for block in item.get("content", ()) if isinstance(item, dict) else ():
                if isinstance(block, dict) and block.get("type") == "output_text":
                    parsed = json.loads(str(block.get("text", "")))
                    if isinstance(parsed, dict):
                        structured = parsed
                        break
        if structured is None:
            raise ValueError("missing structured output")
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as exc:
        print(f"legacy Grok executor failed: {type(exc).__name__}", file=sys.stderr)
        return 3
    result: dict[str, Any] = {"structured_output": structured}
    if isinstance(value.get("usage"), dict):
        result["usage"] = value["usage"]
    print(json.dumps(result, separators=(",", ":"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

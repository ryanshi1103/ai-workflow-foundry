"""Strip credentials and secret-shaped values from Control Center output."""

from __future__ import annotations

import re
from typing import Any

_SECRET_KEY = re.compile(
    r"(secret|password|authorization|cookie|api[_-]?key|access[_-]?token|"
    r"refresh[_-]?token|id[_-]?token|credential|private[_-]?key|session[_-]?key|"
    r"auth\.json|sk-ant|client[_-]?secret|(^|[_-])token$)",
    re.IGNORECASE,
)
_SECRET_VALUE = re.compile(
    r"(?i)\b(sk-[a-z0-9_-]{8,}|bearer\s+[a-z0-9._~+/=-]{8,}|sk-ant-[a-z0-9_-]+)\b"
)
_REDACTED = "[redacted]"
_USAGE_KEYS = {
    "tokens",
    "input_tokens",
    "output_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "cached_read_tokens",
    "cache_creation_tokens",
    "reasoning_tokens",
    "reasoning_output_tokens",
    "total_tokens",
    "local_tokens",
    "model_calls",
}


def is_secret_key(name: object) -> bool:
    text = str(name or "")
    if text.casefold() in _USAGE_KEYS:
        return False
    return bool(_SECRET_KEY.search(text))


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        if _SECRET_VALUE.search(value):
            return _SECRET_VALUE.sub(_REDACTED, value)
        return value
    if isinstance(value, dict):
        return {
            str(key): _REDACTED if is_secret_key(key) else redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [redact_value(item) for item in value]
    return value


def contains_secret(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_SECRET_VALUE.search(value))
    if isinstance(value, dict):
        return any(is_secret_key(key) or contains_secret(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(contains_secret(item) for item in value)
    return False

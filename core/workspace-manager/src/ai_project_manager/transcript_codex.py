"""Codex transcript parser — handles Codex-specific transcript format.

Codex transcript may differ from Claude's. This parser is designed to be
tolerant of format changes. It tries multiple parsing strategies.
"""

import json
from pathlib import Path
from datetime import datetime, timezone


def parse_codex_transcript(transcript_path: Path) -> list[dict]:
    """Parse a Codex transcript file into structured events.

    Codex transcript may be JSONL or have a different schema.
    This parser tries JSONL first, then falls back to line-by-line.
    """
    events = []
    if not transcript_path.exists():
        return events

    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    except (FileNotFoundError, PermissionError, OSError) as e:
        return [{"type": "error", "error": str(e)}]

    # Try JSONL parsing
    if raw_text.strip().startswith('{'):
        events = _parse_jsonl(raw_text)
        if events:
            return events

    # Try NDJSON / line-by-line
    events = _parse_line_by_line(raw_text)
    if events:
        return events

    # Fallback: store as single raw entry
    return [{
        "type": "unknown_format",
        "raw_length": len(raw_text),
        "raw_preview": raw_text[:500],
    }]


def _parse_jsonl(raw: str) -> list[dict]:
    """Parse as JSONL (one JSON object per line)."""
    decoded = []
    for line_num, line in enumerate(raw.split('\n'), 1):
        line = line.strip()
        if not line:
            continue
        try:
            decoded.append((json.loads(line), line_num))
        except json.JSONDecodeError:
            # Not JSONL — abort this strategy
            return []
    # Codex 0.144.x emits the same conversation twice: canonical event_msg
    # records and response_item records.  Prefer event_msg when present so an
    # injected user-role environment bundle cannot become the first prompt.
    has_event_messages = any(
        (event.get("payload") or {}).get("type") in ("user_message", "agent_message")
        for event, _ in decoded
    )
    events = []
    for event, line_num in decoded:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if has_event_messages and event.get("type") == "response_item" and payload.get("role") in ("user", "assistant"):
            continue
        normalized = _normalize_codex_event(event, line_num)
        if normalized is not None:
            events.append(normalized)
    return events


def _parse_line_by_line(raw: str) -> list[dict]:
    """Parse a simple line-by-line format (role: content)."""
    events = []
    current_role = None
    current_lines = []

    for line_num, line in enumerate(raw.split('\n'), 1):
        # Check for role markers
        stripped = line.strip()
        if stripped.startswith("User:") or stripped.startswith("user:"):
            if current_role and current_lines:
                events.append(_make_event(current_role, current_lines, line_num))
            current_role = "user"
            current_lines = [stripped.split(":", 1)[1].strip() if ":" in stripped else stripped]
        elif stripped.startswith("Assistant:") or stripped.startswith("assistant:") or stripped.startswith("Codex:") or stripped.startswith("codex:"):
            if current_role and current_lines:
                events.append(_make_event(current_role, current_lines, line_num))
            current_role = "assistant"
            current_lines = [stripped.split(":", 1)[1].strip() if ":" in stripped else stripped]
        elif stripped.startswith("System:") or stripped.startswith("system:"):
            if current_role and current_lines:
                events.append(_make_event(current_role, current_lines, line_num))
            current_role = "system"
            current_lines = [stripped.split(":", 1)[1].strip() if ":" in stripped else stripped]
        elif current_role:
            current_lines.append(stripped)

    if current_role and current_lines:
        events.append(_make_event(current_role, current_lines, len(raw.split('\n'))))

    return events if len(events) > 0 else []


def _make_event(role: str, lines: list[str], line_num: int) -> dict:
    """Create a normalized event from role and lines."""
    return {
        "line": line_num,
        "type": role,
        "role": role,
        "content": "\n".join(lines),
    }


def _normalize_codex_event(event: dict, line_num: int) -> dict | None:
    """Normalize a Codex transcript event, tolerating unknown fields."""
    # Current rollout schema wraps useful fields in payload.  Keeping the
    # outer-object fallback below preserves compatibility with older schemas.
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else event
    payload_type = payload.get("type")
    if payload_type == "user_message":
        return _message_event("user", payload.get("message", ""), event, line_num)
    if payload_type == "agent_message":
        result = _message_event("assistant", payload.get("message", ""), event, line_num)
        result["phase"] = payload.get("phase", "")
        return result
    if payload_type == "task_complete" and payload.get("last_agent_message"):
        result = _message_event("assistant", payload["last_agent_message"], event, line_num)
        result["phase"] = "final_answer"
        return result
    if event.get("type") in ("event_msg", "response_item") and payload_type not in ("message",):
        return None

    event = payload
    # Older Codex schemas may use different field names — be flexible.
    event_type = (
        event.get("type")
        or event.get("role")
        or event.get("event")
        or "unknown"
    )

    normalized = {
        "line": line_num,
        "type": event_type,
    }

    # Try multiple possible field names for content
    content = (
        event.get("content")
        or event.get("text")
        or event.get("body")
        or event.get("message")
        or ""
    )

    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict):
                text_parts.append(part.get("text", part.get("content", str(part))))
            elif isinstance(part, str):
                text_parts.append(part)
        content = "\n".join(text_parts)
    elif isinstance(content, dict):
        content = content.get("text", content.get("content", str(content)))

    normalized["content"] = str(content) if content else ""
    normalized["role"] = event_type

    # Timestamp
    normalized["timestamp"] = event.get("timestamp", event.get("created_at", event.get("time", "")))

    # Tool use
    if "tool" in event:
        t = event["tool"]
        if isinstance(t, dict):
            normalized["tool_name"] = t.get("name", t.get("tool_name", ""))
            normalized["tool_input"] = t.get("input", t.get("arguments", {}))
        elif isinstance(t, str):
            normalized["tool_name"] = t

    return normalized


def _message_event(role: str, content: object, outer: dict, line_num: int) -> dict:
    return {
        "line": line_num,
        "type": role,
        "role": role,
        "content": str(content) if content else "",
        "timestamp": outer.get("timestamp", ""),
    }


def extract_conversation_markdown(events: list[dict], tool_name: str = "Codex") -> str:
    """Convert parsed events into a readable conversation.md."""
    lines = [
        f"# {tool_name} Session Conversation",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "---",
        "",
    ]

    for evt in events:
        role = evt.get("role", evt.get("type", "unknown"))
        content = evt.get("content", "")

        if role in ("user", "human"):
            lines.append("## 用户")
            lines.append("")
            lines.append(content)
            lines.append("")

        elif role in ("assistant", "ai", "model", "codex"):
            lines.append("## 助手")
            lines.append("")
            lines.append(content)
            lines.append("")

        elif role == "tool_use":
            tool = evt.get("tool_name", "unknown")
            lines.append(f"### 🔧 工具: {tool}")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(evt.get("tool_input", {}), ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")

        elif role == "error":
            lines.append(f"### ⚠️ 错误: {evt.get('error', '')}")
            lines.append("")

        elif role == "unknown_format":
            lines.append("### ⚠️ Transcript 格式未知")
            lines.append("")
            lines.append(f"原始数据长度: {evt.get('raw_length', 0)} 字符")
            lines.append("")

    return "\n".join(lines)


def extract_first_prompt(events: list[dict]) -> str | None:
    """Extract the first real user prompt from parsed events."""
    for evt in events:
        if evt.get("role") in ("user", "human") and evt.get("content", "").strip():
            content = evt["content"].strip()
            if len(content) > 3:
                return content
    return None


def extract_accomplishments(events: list[dict]) -> list[str]:
    """Extract potential accomplishments from assistant messages."""
    items = []
    for evt in events:
        if evt.get("role") in ("assistant", "ai", "model", "codex"):
            content = evt.get("content", "")
            for line in content.split("\n"):
                if any(marker in line.lower() for marker in
                       ["completed", "done", "finished", "created", "installed",
                        "configured", "set up", "successfully", "✓", "✅"]):
                    items.append(line.strip().lstrip("- *"))
            if any(marker in content for marker in ("已创建", "已完成", "已写入", "成功创建")):
                first_line = content.strip().split("\n", 1)[0]
                if first_line and first_line not in items:
                    items.append(first_line)
    return items[:50]


def extract_decisions(events: list[dict]) -> list[str]:
    """Extract decision statements from assistant messages."""
    items = []
    for evt in events:
        if evt.get("role") in ("assistant", "ai", "model", "codex"):
            content = evt.get("content", "")
            for line in content.split("\n"):
                if any(marker in line.lower() for marker in
                       ["decided", "decision", "choosing", "opted", "will use",
                        "recommend", "should use", "best approach"]):
                    items.append(line.strip().lstrip("- *"))
    return items[:50]

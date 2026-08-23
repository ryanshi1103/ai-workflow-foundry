"""Claude Code transcript parser — parses JSONL transcript format.

Claude Code transcript format (per line, JSON):
{
  "type": "user" | "assistant" | "system" | "hook" | "tool_use" | "tool_result" ...
  "message": {...},
  "session_id": "...",
  ...
}

We parse this into structured conversation records.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


def parse_claude_transcript(transcript_path: Path) -> list[dict]:
    """Parse a Claude Code JSONL transcript file into structured events."""
    events = []
    if not transcript_path.exists():
        return events

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    events.append(_normalize_claude_event(event, line_num))
                except json.JSONDecodeError:
                    events.append(
                        {
                            "line": line_num,
                            "type": "parse_error",
                            "raw": line[:500] if len(line) > 500 else line,
                        }
                    )
    except (FileNotFoundError, PermissionError, OSError) as e:
        events.append({"type": "error", "error": str(e)})

    return events


def _normalize_claude_event(event: dict, line_num: int) -> dict:
    """Normalize a Claude Code transcript event to a standard format."""
    event_type = event.get("type", "unknown")

    normalized = {
        "line": line_num,
        "type": event_type,
    }

    if event_type == "user":
        msg = event.get("message", {})
        content = msg.get("content", [])
        text_parts = []
        for part in content if isinstance(content, list) else [content]:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
            elif isinstance(part, str):
                text_parts.append(part)
        normalized["role"] = "user"
        normalized["content"] = "\n".join(text_parts)
        normalized["timestamp"] = msg.get("timestamp", event.get("timestamp", ""))

    elif event_type == "assistant":
        msg = event.get("message", {})
        content = msg.get("content", [])
        text_parts = []
        for part in content if isinstance(content, list) else [content]:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
            elif isinstance(part, str):
                text_parts.append(part)
        normalized["role"] = "assistant"
        normalized["content"] = "\n".join(text_parts)
        normalized["timestamp"] = msg.get("timestamp", event.get("timestamp", ""))

    elif event_type in ("tool_use", "tool_result"):
        normalized["tool_name"] = event.get("name", event.get("tool_name", ""))
        normalized["tool_input"] = event.get("input", {})
        normalized["timestamp"] = event.get("timestamp", "")

    elif event_type == "hook":
        normalized["hook_event"] = event.get("hook_event", "")
        normalized["timestamp"] = event.get("timestamp", "")

    elif event_type == "system":
        normalized["system_type"] = event.get("system_type", "")
        normalized["content"] = event.get("content", str(event))

    else:
        # Unknown or other types — keep raw data but limit size
        normalized["raw"] = str(event)[:2000]

    return normalized


def extract_conversation_markdown(events: list[dict], tool_name: str = "Claude") -> str:
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
        if evt.get("type") == "user":
            lines.append("## 用户")
            lines.append("")
            lines.append(evt.get("content", ""))
            lines.append("")

        elif evt.get("type") == "assistant":
            lines.append("## 助手")
            lines.append("")
            lines.append(evt.get("content", ""))
            lines.append("")

        elif evt.get("type") == "tool_use":
            tool = evt.get("tool_name", "unknown")
            lines.append(f"### 🔧 工具使用: {tool}")
            lines.append("")
            lines.append("```json")
            lines.append(
                json.dumps(evt.get("tool_input", {}), ensure_ascii=False, indent=2)
            )
            lines.append("```")
            lines.append("")

        elif evt.get("type") == "system":
            lines.append(f"### 系统: {evt.get('system_type', '')}")
            lines.append("")
            lines.append(evt.get("content", ""))
            lines.append("")

        elif evt.get("type") == "error":
            lines.append(f"### ⚠️ 错误: {evt.get('error', '')}")
            lines.append("")

        # Skip raw unknown events in readable output

    return "\n".join(lines)


def extract_first_prompt(events: list[dict]) -> str | None:
    """Extract the first real user prompt from parsed events."""
    for evt in events:
        if evt.get("type") == "user" and evt.get("content", "").strip():
            content = evt["content"].strip()
            # Skip system-level template prompts
            if len(content) > 3 and not content.startswith("SYSTEM"):
                return content
    return None


def extract_accomplishments(events: list[dict]) -> list[str]:
    """Extract potential accomplishments from assistant messages."""
    items = []
    for evt in events:
        if evt.get("type") == "assistant":
            content = evt.get("content", "")
            # Look for completed task markers
            for line in content.split("\n"):
                if any(
                    marker in line.lower()
                    for marker in [
                        "completed",
                        "done",
                        "finished",
                        "created",
                        "installed",
                        "configured",
                        "set up",
                        "successfully",
                        "✓",
                        "✅",
                    ]
                ):
                    items.append(line.strip().lstrip("- *"))
    return items[:50]  # limit


def extract_decisions(events: list[dict]) -> list[str]:
    """Extract decision statements from assistant messages."""
    items = []
    for evt in events:
        if evt.get("type") == "assistant":
            content = evt.get("content", "")
            for line in content.split("\n"):
                if any(
                    marker in line.lower()
                    for marker in [
                        "decided",
                        "decision",
                        "choosing",
                        "opted",
                        "will use",
                        "recommend",
                        "should use",
                        "best approach",
                    ]
                ):
                    items.append(line.strip().lstrip("- *"))
    return items[:50]

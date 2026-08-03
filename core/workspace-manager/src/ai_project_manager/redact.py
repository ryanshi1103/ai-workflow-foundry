"""Sensitive information redaction for transcripts and conversation files."""

import re
import json
from pathlib import Path

# ─── Redaction patterns ─────────────────────────────────────────────────────

REDACTION_RULES = [
    # API keys (various formats)
    (re.compile(r'(?:api[_-]?key|apikey)\s*[:=]\s*["\']?([\w\-_\.]{16,})["\']?', re.IGNORECASE),
     lambda m: m.group(0).replace(m.group(1), '[REDACTED_API_KEY]')),

    # OpenAI sk- keys
    (re.compile(r'\b(sk-(?:proj-)?[A-Za-z0-9_\-]{20,})\b'),
     '[REDACTED_API_KEY]'),

    # Anthropic API keys (sk-ant-)
    (re.compile(r'\b(sk-ant-[A-Za-z0-9_\-]{20,})\b'),
     '[REDACTED_API_KEY]'),

    # DeepSeek API keys
    (re.compile(r'\b(ds-[A-Za-z0-9_\-]{16,})\b'),
     '[REDACTED_API_KEY]'),

    # Bearer tokens in Authorization headers
    (re.compile(r'(Authorization\s*:\s*Bearer\s+)([\w\-_\.=]{16,})', re.IGNORECASE),
     lambda m: m.group(1) + '[REDACTED_TOKEN]'),

    # Generic bearer tokens
    (re.compile(r'(bearer\s+)([\w\-_\.=]{16,})', re.IGNORECASE),
     lambda m: m.group(1) + '[REDACTED_TOKEN]'),

    # Passwords in assignments
    (re.compile(r'(password|passwd|pwd)\s*[:=]\s*["\'][^"\']{4,}["\']', re.IGNORECASE),
     lambda m: m.group(1) + '=[REDACTED_PASSWORD]'),

    # Password in key=value context
    (re.compile(r'(password|passwd|pwd)=[^\s&]{4,}', re.IGNORECASE),
     lambda m: m.group(1) + '=[REDACTED_PASSWORD]'),

    # Private keys (any length between BEGIN/END markers)
    (re.compile(r'-----BEGIN\s+(?:RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY-----'),
     '[REDACTED_PRIVATE_KEY]'),

    # SOCKS/http proxy with embedded credentials
    (re.compile(r'(socks5?|https?)://[^:@\s]+:[^:@\s]+@([^\s]+)'),
     lambda m: f'{m.group(1)}://[REDACTED_PROXY_URL]@{m.group(2)}'),

    # Generic URL user:pass@host
    (re.compile(r'://[^:@/\s]+:[^:@/\s]+@'),
     '://[REDACTED_CREDENTIALS]@'),

    # Connection strings with passwords
    (re.compile(r'(mongodb|mysql|postgresql|redis|jdbc)://[^:@\s]+:[^:@\s]+@([^\s]+)'),
     lambda m: f'{m.group(1)}://[REDACTED_CREDENTIALS]@{m.group(2)}'),

    # ENV var assignments with obvious keys
    (re.compile(r'(ANTHROPIC_API_KEY|OPENAI_API_KEY|DEEPSEEK_API_KEY|API_KEY|AUTH_TOKEN|SECRET_KEY)\s*=\s*["\']?([\w\-_\.]{12,})["\']?'),
     lambda m: f'{m.group(1)}=[REDACTED_API_KEY]'),

    # Cookie strings with potential session tokens
    (re.compile(r'(cookie|session)\s*[:=]\s*["\']([\w\-_\.=]{20,})["\']', re.IGNORECASE),
     lambda m: f'{m.group(1)}=[REDACTED_TOKEN]'),

    # Access tokens (various)
    (re.compile(r'(access[_-]?token|auth[_-]?token|refresh[_-]?token)\s*[:=]\s*["\']?([\w\-_\.]{16,})["\']?', re.IGNORECASE),
     lambda m: f'{m.group(1)}=[REDACTED_TOKEN]'),
]


def redact_text(text: str) -> tuple[str, bool]:
    """Apply all redaction rules to text. Returns (redacted_text, had_sensitive).

    Does NOT print or log the original text containing secrets.
    """
    had_sensitive = False
    result = text

    for pattern, replacement in REDACTION_RULES:
        new_result = pattern.sub(replacement, result)
        if new_result != result:
            had_sensitive = True
            result = new_result

    return result, had_sensitive


def redact_jsonl(input_path: Path, output_path: Path) -> tuple[int, bool]:
    """Read JSONL transcript, redact each line, write to output.
    Returns (line_count, had_sensitive).
    """
    line_count = 0
    had_sensitive = False

    if not input_path.exists():
        return 0, False

    try:
        with open(input_path, 'r', encoding='utf-8') as fin:
            with open(output_path, 'w', encoding='utf-8') as fout:
                for line in fin:
                    line_count += 1
                    redacted, sensitive = redact_text(line)
                    if sensitive:
                        had_sensitive = True
                    fout.write(redacted)
                    if not redacted.endswith('\n'):
                        fout.write('\n')
                fout.flush()
    except (FileNotFoundError, PermissionError, OSError):
        return line_count, had_sensitive

    return line_count, had_sensitive


def redact_file(input_path: Path, output_path: Path) -> tuple[bool, bool]:
    """Redact a generic text file. Returns (success, had_sensitive)."""
    try:
        text = input_path.read_text(encoding='utf-8')
        redacted, had_sensitive = redact_text(text)
        output_path.write_text(redacted, encoding='utf-8')
        return True, had_sensitive
    except (FileNotFoundError, PermissionError, OSError):
        return False, False


def scan_for_secrets(text: str) -> list[str]:
    """Scan text for potential secrets. Returns list of issue descriptions
    WITHOUT including the secret content itself.
    """
    issues = []

    # Check for common secret patterns and report categories
    checks = [
        (re.compile(r'(?:api[_-]?key|apikey)\s*[:=]\s*["\']?[\w\-_\.]{16,}["\']?', re.IGNORECASE),
         "Possible API key assignment found"),
        (re.compile(r'\b(sk-(?:proj-)?[A-Za-z0-9_\-]{20,})\b'),
         "Possible OpenAI API key found"),
        (re.compile(r'\b(sk-ant-[A-Za-z0-9_\-]{20,})\b'),
         "Possible Anthropic API key found"),
        (re.compile(r'(Authorization\s*:\s*Bearer\s+)[\w\-_\.=]{16,}', re.IGNORECASE),
         "Authorization Bearer token found"),
        (re.compile(r'-----BEGIN\s+(?:RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY-----'),
         "Private key found"),
        (re.compile(r'(password|passwd|pwd)\s*[:=]\s*["\'][^"\']{4,}["\']', re.IGNORECASE),
         "Password assignment found"),
        (re.compile(r'://[^:@/\s]+:[^:@/\s]+@'),
         "URL with embedded credentials found"),
    ]

    for pattern, description in checks:
        if pattern.search(text):
            issues.append(description)

    return issues

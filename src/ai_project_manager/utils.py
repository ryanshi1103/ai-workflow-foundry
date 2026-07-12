"""Shared utilities: file locks, atomic writes, JSON handling, ID generation, logging."""

import os
import sys
import json
import fcntl
import hashlib
import secrets
import shutil
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager

PROJECTS_ROOT = Path.home() / "Projects"
STATE_DIR = Path.home() / ".local" / "state" / "ai-project-manager"
CONFIG_DIR = Path.home() / ".config" / "ai-project-manager"
INSTALL_DIR = Path.home() / ".local" / "share" / "ai-project-manager"
BIN_DIR = Path.home() / ".local" / "bin"
GLOBAL_LOCK_FILE = STATE_DIR / "global.lock"
PROJECT_INDEX_FILE = STATE_DIR / "project-index.json"

# Internal env var to prevent recursion
INTERNAL_ENV_VAR = "AI_PROJECT_MANAGER_INTERNAL"

# Sensitive patterns for redaction
SENSITIVE_PATTERNS = [
    (r'(api_key|apikey|api-key)\s*[:=]\s*["\']?[\w\-_\.]{20,}["\']?', '[REDACTED_API_KEY]'),
    (r'(Bearer\s+)[\w\-_\.=]{20,}', r'\1[REDACTED_TOKEN]'),
    (r'(Authorization:\s*Bearer\s+)[\w\-_\.=]{20,}', r'\1[REDACTED_TOKEN]'),
    (r'(ANTHROPIC_API_KEY|OPENAI_API_KEY|DEEPSEEK_API_KEY)\s*=\s*["\']?[\w\-_\.]{20,}["\']?', r'\1=[REDACTED_API_KEY]'),
    (r'(password|passwd)\s*[:=]\s*["\'][^"\']+["\']', r'\1=[REDACTED_PASSWORD]'),
    (r'-----BEGIN\s+(RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY-----[\s\S]*?-----END\s+\1\s+PRIVATE\s+KEY-----', '[REDACTED_PRIVATE_KEY]'),
    (r'(socks5?|https?)://[^:]+:[^@]+@', '[REDACTED_PROXY_URL]'),
    (r'(sk-[A-Za-z0-9_\-]{20,})', '[REDACTED_API_KEY]'),
    (r'(api\.deepseek\.com/anthropic)', r'\1'),
]


def generate_short_id(length: int = 6) -> str:
    """Generate a short random hex ID."""
    return secrets.token_hex(length // 2 + 1)[:length]


def generate_session_id(tool: str) -> str:
    """Generate a unique session ID: YYYYMMDD-HHMMSS-tool-shortid."""
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d-%H%M%S")
    short = generate_short_id(6)
    return f"{ts}-{tool}-{short}"


def generate_project_temp_name(tool: str) -> str:
    """Generate a temporary project name: YYYYMMDD-HHMMSS-tool-shortid."""
    return generate_session_id(tool)


def timestamp_iso() -> str:
    """Return current time in ISO 8601 with timezone."""
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: Path, mode: int = 0o755) -> Path:
    """Ensure directory exists, create if not."""
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(mode)
    except OSError:
        pass  # Read-only filesystem — ignore
    return path


def atomic_write_json(filepath: Path, data: dict | list) -> None:
    """Write JSON atomically: temp file → fsync → os.replace."""
    filepath = Path(filepath)
    ensure_dir(filepath.parent)
    tmp_path = filepath.with_suffix(filepath.suffix + ".tmp." + generate_short_id(4))
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, filepath)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def atomic_copy(src: Path, dst: Path) -> None:
    """Copy file atomically."""
    ensure_dir(dst.parent)
    tmp_path = dst.with_suffix(dst.suffix + ".tmp." + generate_short_id(4))
    try:
        shutil.copy2(src, tmp_path)
        os.replace(tmp_path, dst)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def read_json(filepath: Path) -> dict | list | None:
    """Read JSON file, return None on error."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        return None


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha.update(chunk)
    except FileNotFoundError:
        return ""
    return sha.hexdigest()


def compute_text_hash(text: str) -> str:
    """Compute SHA-256 hash of text."""
    return hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()


def sanitize_project_title(title: str, max_len: int = 48) -> str:
    """Sanitize a string for use as a directory name."""
    import re
    # Remove control characters
    title = re.sub(r'[\x00-\x1f\x7f]', '', title)
    # Replace problematic chars with space
    title = re.sub(r'[/\\:*?"<>|\n\r\t]', ' ', title)
    # Collapse whitespace and hyphens
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'-+', '-', title)
    title = title.strip().strip('-').strip()
    # Truncate
    if len(title) > max_len:
        # Try to cut at word boundary
        truncated = title[:max_len]
        last_space = truncated.rfind(' ')
        if last_space > max_len // 2:
            truncated = truncated[:last_space]
        title = truncated.strip().strip('-').strip()
    return title


@contextmanager
def file_lock(lock_path: Path, timeout: float = 30.0):
    """Context manager for file-based locking using fcntl.flock."""
    ensure_dir(lock_path.parent)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
    deadline = time.time() + timeout
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.time() >= deadline:
                    raise TimeoutError(f"Lock timeout on {lock_path}")
                time.sleep(0.1)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            logging.getLogger("ai-project-manager").warning("Failed to unlock %s",lock_path)
        os.close(fd)


def find_real_executable(name: str, exclude_paths: set | None = None) -> str | None:
    """Find real executable, skipping shell functions and specified paths."""
    exclude_paths = exclude_paths or set()
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    for d in path_dirs:
        candidate = Path(d) / name
        if str(candidate) in exclude_paths:
            continue
        if candidate.is_file() and os.access(candidate, os.X_OK):
            # Make sure it's not a shell script that wraps itself
            try:
                with open(candidate, 'r') as f:
                    first_line = f.readline()
                if 'shell-integration.sh' in first_line or 'ai-project-manager' in first_line:
                    continue
            except (OSError,UnicodeError):first_line=""
            return str(candidate)
    return None


def setup_logging(level: str = "WARNING") -> logging.Logger:
    """Set up logging for the project manager."""
    logger = logging.getLogger("ai-project-manager")
    logger.setLevel(getattr(logging, level.upper(), logging.WARNING))
    if not logger.handlers:
        log_dir = STATE_DIR / "logs"
        ensure_dir(log_dir)
        handler = logging.FileHandler(log_dir / "manager.log")
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        ))
        logger.addHandler(handler)
    return logger


def is_internal_call() -> bool:
    """Check if this is an internal (non-recursive) call."""
    return os.environ.get(INTERNAL_ENV_VAR, '') == '1'

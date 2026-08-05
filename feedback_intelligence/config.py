"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("true", "1", "yes", "on")


def _int(v: str | None, default: int) -> int:
    try:
        return int(v) if v is not None else default
    except ValueError:
        return default


def _float(v: str | None, default: float) -> float:
    try:
        return float(v) if v is not None else default
    except ValueError:
        return default


# ── Project paths ──────────────────────────────────────────────
PROJECT_ROOT = _PROJECT_ROOT
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── DeepSeek ───────────────────────────────────────────────────
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEEPSEEK_THINKING: bool = _bool(os.getenv("DEEPSEEK_THINKING"), default=False)
DEEPSEEK_MAX_CONCURRENCY: int = _int(os.getenv("DEEPSEEK_MAX_CONCURRENCY"), 3)
DEEPSEEK_TIMEOUT_SECONDS: int = _int(os.getenv("DEEPSEEK_TIMEOUT_SECONDS"), 60)
DEEPSEEK_BATCH_SIZE: int = _int(os.getenv("DEEPSEEK_BATCH_SIZE"), 10)
DEEPSEEK_MAX_CONTENT_LENGTH: int = 4000

# ── Apify ──────────────────────────────────────────────────────
APIFY_TOKEN: str = os.getenv("APIFY_TOKEN", "")
APIFY_ACTOR_ID: str = os.getenv("APIFY_ACTOR_ID", "")
APIFY_MAX_ITEMS: int = _int(os.getenv("APIFY_MAX_ITEMS"), 100)

# ── Application ────────────────────────────────────────────────
# ``APP_DB_URL`` remains the supported legacy variable.  The canonical name is
# additive so existing deployments continue to select the same database.
APP_DB_URL: str = os.getenv(
    "FEEDBACK_DB_URL",
    os.getenv("APP_DB_URL", "sqlite:///data/social_monitor.db"),
)
APP_MOCK_MODE: bool = _bool(os.getenv("APP_MOCK_MODE"), default=True)
APP_LOG_LEVEL: str = os.getenv("APP_LOG_LEVEL", "INFO")
APP_HOST: str = "127.0.0.1"
APP_PORT: int = _int(os.getenv("APP_PORT"), 8501)

# ── Thresholds ─────────────────────────────────────────────────
SEVERITY_WARNING_THRESHOLD: int = 75
CONFIDENCE_HUMAN_REVIEW_THRESHOLD: float = 0.65
MAX_UPLOAD_FILE_SIZE_MB: int = 10

# ── Derived helpers ─────────────────────────────────────────────
DEEPSEEK_CONFIGURED: bool = bool(DEEPSEEK_API_KEY)
APIFY_CONFIGURED: bool = bool(APIFY_TOKEN and APIFY_ACTOR_ID)

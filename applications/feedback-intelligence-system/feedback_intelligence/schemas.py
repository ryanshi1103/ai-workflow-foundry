"""Pydantic schemas for data validation, API responses, and import/export."""

import hashlib
import re
import unicodedata
from enum import Enum
from urllib.parse import urlparse, urlunparse

from pydantic import BaseModel, Field, field_validator

# ── Enums ──────────────────────────────────────────────────────


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    mixed = "mixed"
    negative = "negative"
    unknown = "unknown"


class ComplaintCategory(str, Enum):
    product_quality = "product_quality"
    service_attitude = "service_attitude"
    delivery = "delivery"
    price = "price"
    refund = "refund"
    privacy = "privacy"
    security = "security"
    usability = "usability"
    performance = "performance"
    advertising = "advertising"
    account = "account"
    policy = "policy"
    misinformation = "misinformation"
    other = "other"
    none = "none"


class AnalysisStatus(str, Enum):
    pending = "pending"
    analyzing = "analyzing"
    completed = "completed"
    error = "error"
    skipped = "skipped"


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class FeedbackType(str, Enum):
    problem_feedback = "problem_feedback"
    experience_feedback = "experience_feedback"
    unknown = "unknown"


class ActionPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ActionStatus(str, Enum):
    new = "new"
    reviewing = "reviewing"
    processing = "processing"
    resolved = "resolved"
    ignored = "ignored"


# ── Content normalization ──────────────────────────────────────


def normalize_content(
    content: str,
    platform: str = "",
    source_url: str = "",
    external_id: str = "",
) -> str:
    """Normalize content for hashing without modifying the original."""

    # Unicode normalization (NFC)
    text = unicodedata.normalize("NFC", content)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Collapse consecutive whitespace (space, tab, newline) into single space
    text = re.sub(r"\s+", " ", text)

    # Lowercase for English (only ASCII letters)
    text_lower = text.lower()

    # Normalize URLs in the content
    def _norm_url(u: str) -> str:
        try:
            p = urlparse(u)
            netloc = p.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            path = p.path.rstrip("/") or "/"
            return urlunparse((p.scheme, netloc, path, "", "", ""))
        except Exception:
            return u.lower()

    # Find URLs in text and normalize them
    url_pattern = re.compile(r"https?://\S+")
    for u in url_pattern.findall(text_lower):
        text_lower = text_lower.replace(u, _norm_url(u))

    # Build the hash input: include platform, source_url, external_id
    hash_input_parts = [platform.strip().lower(), source_url.strip(), external_id.strip(), text_lower]
    hash_input = "|".join(hash_input_parts)

    return hash_input


def compute_content_hash(
    content: str,
    platform: str = "",
    source_url: str = "",
    external_id: str = "",
) -> str:
    """Compute SHA-256 hash of normalized content."""
    normalized = normalize_content(content, platform, source_url, external_id)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# ── DeepSeek Analysis Result ───────────────────────────────────


class DeepSeekAnalysisResult(BaseModel):
    """Schema for the JSON that DeepSeek must return."""

    is_relevant: bool
    feedback_type: FeedbackType = FeedbackType.unknown
    sentiment: Sentiment = Sentiment.unknown
    sentiment_score: float
    is_negative: bool
    complaint_category: ComplaintCategory = ComplaintCategory.none
    complaint_subcategory: str = ""
    target: str = ""
    severity: int = Field(ge=0, le=100)
    urgency: Urgency = Urgency.low
    requires_action: bool = False
    action_priority: ActionPriority = ActionPriority.low
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = ""
    evidence: str = ""
    suggested_action: str = ""
    needs_human_review: bool = False

    @field_validator("severity")
    @classmethod
    def check_severity_range(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError(f"severity must be 0-100, got {v}")
        return v

    @field_validator("sentiment_score")
    @classmethod
    def check_sentiment_score_range(cls, v: float) -> float:
        if v < -1.0 or v > 1.0:
            raise ValueError(f"sentiment_score must be -1.0 to 1.0, got {v}")
        return v

    @field_validator("confidence")
    @classmethod
    def check_confidence_range(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {v}")
        return v


# ── Import schemas ─────────────────────────────────────────────


class ImportRow(BaseModel):
    """A single row of data to import."""

    platform: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=10000)
    source_url: str | None = Field(default=None, max_length=2048)
    external_id: str | None = Field(default=None, max_length=500)
    author_display_name: str | None = Field(default=None, max_length=200)
    published_at: str | None = None
    engagement_count: int | None = None
    brand: str | None = Field(default=None, max_length=200)
    product: str | None = Field(default=None, max_length=200)
    search_keyword: str | None = Field(default=None, max_length=500)
    language: str | None = Field(default=None, max_length=20)
    source_type: str = "import"

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("platform 字段不能为空")
        return v.strip()

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content 字段不能为空")
        if len(v) > 10000:
            raise ValueError("content 字段超过最大长度 10000 字符")
        return v


class ImportResult(BaseModel):
    """Result of an import operation."""

    total: int = 0
    new: int = 0
    duplicates: int = 0
    invalid: int = 0
    errors: int = 0
    error_details: list[str] = Field(default_factory=list)


# ── Export schemas ─────────────────────────────────────────────


class ExportRow(BaseModel):
    """A row for CSV/JSON export."""

    id: int
    platform: str
    source_url: str | None
    external_id: str | None
    author_display_name: str | None
    content: str
    language: str | None
    published_at: str | None
    collected_at: str | None
    analysis_status: str
    is_relevant: bool | None
    feedback_type: str | None
    sentiment: str | None
    sentiment_score: float | None
    is_negative: bool | None
    complaint_category: str | None
    complaint_subcategory: str | None
    target: str | None
    severity: int | None
    urgency: str | None
    confidence: float | None
    summary: str | None
    evidence: str | None
    suggested_action: str | None
    requires_action: bool | None
    action_priority: str | None
    action_status: str | None
    model_name: str | None
    analyzed_at: str | None
    needs_human_review: bool | None
    corrected_sentiment: str | None
    corrected_category: str | None
    corrected_severity: int | None
    corrected_feedback_type: str | None
    corrected_requires_action: bool | None
    corrected_action_priority: str | None
    corrected_action_status: str | None
    is_misjudged: bool | None
    review_notes: str | None
    review_status: str | None
    reviewed_at: str | None


# ── Filter schema ──────────────────────────────────────────────


class FeedbackFilter(BaseModel):
    """Filters for the feedback list page."""

    platform: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    brand: str | None = None
    product: str | None = None
    keyword: str | None = None
    feedback_type: str | None = None
    sentiment: str | None = None
    is_negative: bool | None = None
    complaint_category: str | None = None
    severity_min: int | None = None
    severity_max: int | None = None
    needs_human_review: bool | None = None
    requires_action: bool | None = None
    action_priority: str | None = None
    action_status: str | None = None
    analysis_status: str | None = None
    limit: int = 100
    offset: int = 0


# ── Apify field mapping ────────────────────────────────────────


class ApifyFieldMapping(BaseModel):
    """Mapping from Apify Actor output fields to FeedbackItem fields."""

    platform: str = "platform"
    content: str = "content"
    source_url: str = "url"
    external_id: str = "id"
    author_display_name: str = "author.name"
    published_at: str = "published_at"
    engagement_count: str = "engagement_count"
    brand: str = "brand"
    product: str = "product"
    search_keyword: str = "search_keyword"
    language: str = "language"


# ── App settings schema ────────────────────────────────────────


class AppSettings(BaseModel):
    """Application settings for display in the settings page."""

    deepseek_configured: bool
    apify_configured: bool
    deepseek_model: str
    mock_mode: bool
    db_path: str
    batch_size: int
    max_concurrency: int
    timeout_seconds: int
    severity_threshold: int

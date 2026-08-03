"""SQLAlchemy ORM models for feedback items, analysis results, and human reviews."""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class FeedbackItem(Base):
    """Raw feedback item imported from any platform."""

    __tablename__ = "feedback_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unknown"
    )
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author_display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    engagement_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    search_keyword: Mapped[str | None] = mapped_column(String(500), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    product: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    raw_data_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationship
    analysis: Mapped["FeedbackAnalysis | None"] = relationship(
        "FeedbackAnalysis", back_populates="feedback_item", uselist=False,
        lazy="selectin", cascade="all, delete-orphan"
    )
    human_review: Mapped["HumanReview | None"] = relationship(
        "HumanReview", back_populates="feedback_item", uselist=False,
        lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FeedbackItem id={self.id} platform={self.platform} status={self.analysis_status}>"


class FeedbackAnalysis(Base):
    """AI analysis result for a feedback item."""

    __tablename__ = "feedback_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feedback_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("feedback_items.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    is_relevant: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    feedback_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unknown", index=True
    )
    sentiment: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unknown"
    )
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_negative: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    complaint_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    complaint_subcategory: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target: Mapped[str | None] = mapped_column(String(500), nullable=True)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    requires_action: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    action_priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    action_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="new"
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    needs_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationship
    feedback_item: Mapped["FeedbackItem"] = relationship(
        "FeedbackItem", back_populates="analysis"
    )

    def __repr__(self) -> str:
        return (
            f"<FeedbackAnalysis id={self.id} item_id={self.feedback_item_id}"
            f" type={self.feedback_type} sentiment={self.sentiment}>"
        )


class HumanReview(Base):
    """Human review record, preserving audit trail. Never overwrites AI results."""

    __tablename__ = "human_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feedback_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("feedback_items.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True, default="human")
    corrected_feedback_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    corrected_sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    corrected_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    corrected_severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    corrected_requires_action: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    corrected_action_priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    corrected_action_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_misjudged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    # Relationship
    feedback_item: Mapped["FeedbackItem"] = relationship(
        "FeedbackItem", back_populates="human_review"
    )

    def __repr__(self) -> str:
        return f"<HumanReview id={self.id} item_id={self.feedback_item_id}>"

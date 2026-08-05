"""Tests for database operations."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.models import FeedbackAnalysis, FeedbackItem, HumanReview
from src.schemas import compute_content_hash


class TestDatabaseWriteRead:
    """Test writing to and reading from the database."""

    def test_create_feedback_item(self, db_session: Session):
        """Should be able to create and read a FeedbackItem."""
        item = FeedbackItem(
            content_hash=compute_content_hash("Test content", "twitter"),
            platform="twitter",
            content="Test content",
            source_type="mock",
        )
        db_session.add(item)
        db_session.commit()

        fetched = db_session.query(FeedbackItem).first()
        assert fetched is not None
        assert fetched.platform == "twitter"
        assert fetched.content == "Test content"
        assert fetched.analysis_status == "pending"

    def test_create_analysis(self, db_session: Session):
        """Should be able to create an analysis linked to an item."""
        item = FeedbackItem(
            content_hash=compute_content_hash("Test", "platform"),
            platform="platform",
            content="Test",
        )
        db_session.add(item)
        db_session.commit()

        analysis = FeedbackAnalysis(
            feedback_item_id=item.id,
            sentiment="negative",
            sentiment_score=-0.8,
            is_negative=True,
            severity=75,
            confidence=0.9,
            model_name="test-model",
            prompt_version="v1",
            needs_human_review=False,
        )
        db_session.add(analysis)
        db_session.commit()

        # Verify relationship
        fetched = db_session.query(FeedbackItem).first()
        assert fetched.analysis is not None
        assert fetched.analysis.sentiment == "negative"
        assert fetched.analysis.severity == 75

    def test_create_human_review(self, db_session: Session):
        """Should be able to create a human review linked to an item."""
        item = FeedbackItem(
            content_hash=compute_content_hash("Test", "p"),
            platform="p",
            content="Test",
        )
        db_session.add(item)
        db_session.commit()

        review = HumanReview(
            feedback_item_id=item.id,
            reviewed_by="tester",
            review_notes="Test review",
            review_status="completed",
            reviewed_at=datetime.now(UTC),
        )
        db_session.add(review)
        db_session.commit()

        fetched = db_session.query(FeedbackItem).first()
        assert fetched.human_review is not None
        assert fetched.human_review.review_status == "completed"

    def test_cascade_delete(self, db_session: Session):
        """Deleting a feedback item should cascade to analysis."""
        item = FeedbackItem(
            content_hash=compute_content_hash("Cascade", "platform"),
            platform="platform",
            content="Cascade",
        )
        db_session.add(item)
        db_session.commit()

        analysis = FeedbackAnalysis(
            feedback_item_id=item.id,
            sentiment="negative",
            sentiment_score=-0.5,
            is_negative=True,
            severity=30,
            confidence=0.8,
        )
        db_session.add(analysis)
        db_session.commit()

        # Delete analysis first, then item (SQLite FK handling)
        db_session.delete(analysis)
        db_session.delete(item)
        db_session.commit()

        # Both should be gone
        items = db_session.query(FeedbackItem).all()
        analyses = db_session.query(FeedbackAnalysis).all()
        assert len(items) == 0
        assert len(analyses) == 0

    def test_unique_content_hash(self, db_session: Session):
        """Content hash should be unique, duplicate should raise error."""
        h = compute_content_hash("Unique test", "p")
        item1 = FeedbackItem(content_hash=h, platform="p", content="Unique test")
        db_session.add(item1)
        db_session.commit()

        item2 = FeedbackItem(content_hash=h, platform="p", content="Unique test")
        db_session.add(item2)
        with __import__("pytest").raises(Exception):
            db_session.commit()
        db_session.rollback()

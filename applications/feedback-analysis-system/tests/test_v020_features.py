"""Tests for new v0.2.0 features: feedback classification, migration, new filters."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.models import FeedbackAnalysis, FeedbackItem, HumanReview
from src.schemas import (
    ActionPriority,
    ActionStatus,
    DeepSeekAnalysisResult,
    FeedbackType,
    Sentiment,
    compute_content_hash,
)
from src.services.deepseek_service import DeepSeekService


class TestFeedbackTypeEnums:
    """Test new enums for feedback classification."""

    def test_feedback_type_values(self):
        """FeedbackType should have correct values."""
        assert FeedbackType.problem_feedback.value == "problem_feedback"
        assert FeedbackType.experience_feedback.value == "experience_feedback"
        assert FeedbackType.unknown.value == "unknown"

    def test_action_priority_values(self):
        """ActionPriority should match urgency levels."""
        assert ActionPriority.low.value == "low"
        assert ActionPriority.medium.value == "medium"
        assert ActionPriority.high.value == "high"
        assert ActionPriority.critical.value == "critical"

    def test_action_status_values(self):
        """ActionStatus should have workflow states."""
        assert ActionStatus.new.value == "new"
        assert ActionStatus.reviewing.value == "reviewing"
        assert ActionStatus.processing.value == "processing"
        assert ActionStatus.resolved.value == "resolved"
        assert ActionStatus.ignored.value == "ignored"


class TestDeepSeekResultNewFields:
    """Test DeepSeekAnalysisResult with new v0.2.0 fields."""

    def test_result_has_feedback_type(self):
        """Result should accept and validate feedback_type."""
        result = DeepSeekAnalysisResult(
            is_relevant=True,
            feedback_type=FeedbackType.problem_feedback,
            sentiment=Sentiment.negative,
            sentiment_score=-0.8,
            is_negative=True,
            severity=70,
            confidence=0.9,
        )
        assert result.feedback_type == FeedbackType.problem_feedback

    def test_result_has_action_fields(self):
        """Result should accept requires_action and action_priority."""
        result = DeepSeekAnalysisResult(
            is_relevant=True,
            feedback_type=FeedbackType.problem_feedback,
            sentiment=Sentiment.negative,
            sentiment_score=-0.9,
            is_negative=True,
            severity=85,
            requires_action=True,
            action_priority=ActionPriority.high,
            confidence=0.92,
        )
        assert result.requires_action is True
        assert result.action_priority == ActionPriority.high

    def test_result_default_feedback_type(self):
        """Result should default feedback_type to unknown."""
        result = DeepSeekAnalysisResult(
            is_relevant=False,
            sentiment=Sentiment.unknown,
            sentiment_score=0.0,
            is_negative=False,
            severity=0,
            confidence=0.95,
        )
        assert result.feedback_type == FeedbackType.unknown

    def test_result_default_requires_action(self):
        """Result should default requires_action to False."""
        result = DeepSeekAnalysisResult(
            is_relevant=True,
            sentiment=Sentiment.positive,
            sentiment_score=0.7,
            is_negative=False,
            severity=0,
            confidence=0.9,
        )
        assert result.requires_action is False


class TestDatabaseMigration:
    """Test idempotent migration for new columns."""

    def test_migration_adds_new_columns(self, db_session: Session):
        """Migration should add new columns to existing tables."""
        from src.database import run_migrations

        # Run migration on test DB (already has tables from conftest)
        run_migrations()

        # Create an item and analysis with new fields
        item = FeedbackItem(
            content_hash=compute_content_hash("migration test", "test"),
            platform="test",
            content="migration test",
        )
        db_session.add(item)
        db_session.commit()

        analysis = FeedbackAnalysis(
            feedback_item_id=item.id,
            feedback_type="problem_feedback",
            sentiment="negative",
            sentiment_score=-0.7,
            is_negative=True,
            severity=55,
            confidence=0.85,
            requires_action=True,
            action_priority="high",
            action_status="new",
        )
        db_session.add(analysis)
        db_session.commit()

        # Verify new fields were stored
        fetched = db_session.query(FeedbackAnalysis).filter_by(
            feedback_item_id=item.id
        ).first()
        assert fetched is not None
        assert fetched.feedback_type == "problem_feedback"
        assert fetched.requires_action is True
        assert fetched.action_priority == "high"
        assert fetched.action_status == "new"

    def test_migration_is_idempotent(self, db_session: Session):
        """Running migration multiple times should not error."""
        from src.database import run_migrations

        # Run twice
        run_migrations()
        run_migrations()

        # Should still be able to create items
        item = FeedbackItem(
            content_hash=compute_content_hash("idempotent test", "test"),
            platform="test",
            content="idempotent test",
        )
        db_session.add(item)
        db_session.commit()

        analysis = FeedbackAnalysis(
            feedback_item_id=item.id,
            feedback_type="experience_feedback",
            sentiment="positive",
            sentiment_score=0.8,
            is_negative=False,
            severity=0,
            confidence=0.9,
        )
        db_session.add(analysis)
        db_session.commit()
        # If we got here without error, migration is idempotent

    def test_migration_defaults_on_existing_data(self, db_session: Session):
        """Existing data without new columns should get safe defaults."""
        from src.database import run_migrations

        # Create item via ORM (uses new model with all columns)
        item = FeedbackItem(
            content_hash=compute_content_hash("defaults test", "test"),
            platform="test",
            content="defaults test",
        )
        db_session.add(item)
        db_session.commit()

        # Create analysis with explicit old-style fields only
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

        # Run migration (idempotent — should not fail)
        run_migrations()

        # Verify columns exist in table schema
        from sqlalchemy import text
        result = db_session.execute(
            text("PRAGMA table_info(feedback_analyses)")
        ).fetchall()
        columns = {row[1] for row in result}
        assert "feedback_type" in columns
        assert "requires_action" in columns
        assert "action_priority" in columns
        assert "action_status" in columns

        # Verify existing row got default values
        fetched = db_session.query(FeedbackAnalysis).filter_by(
            feedback_item_id=item.id
        ).first()
        assert fetched is not None
        # ORM-created rows get ORM defaults, so these should be safe
        assert fetched.feedback_type in ("unknown", "problem_feedback", "experience_feedback")


class TestHumanReviewNewFields:
    """Test human review with new correction fields."""

    def test_review_can_correct_feedback_type(self, db_session: Session):
        """Human review should support correcting feedback_type."""
        item = FeedbackItem(
            content_hash=compute_content_hash("review type test", "test"),
            platform="test",
            content="review type test",
        )
        db_session.add(item)
        db_session.commit()

        review = HumanReview(
            feedback_item_id=item.id,
            reviewed_by="tester",
            corrected_feedback_type="problem_feedback",
            corrected_requires_action=True,
            corrected_action_priority="high",
            corrected_action_status="new",
            review_status="completed",
            reviewed_at=datetime.now(UTC),
        )
        db_session.add(review)
        db_session.commit()

        fetched = db_session.query(HumanReview).filter_by(
            feedback_item_id=item.id
        ).first()
        assert fetched is not None
        assert fetched.corrected_feedback_type == "problem_feedback"
        assert fetched.corrected_requires_action is True
        assert fetched.corrected_action_priority == "high"
        assert fetched.corrected_action_status == "new"


class TestMockAnalysisClassification:
    """Test mock analysis returns proper feedback types."""

    def test_problem_feedback_detection(self):
        """Content with clear problems should be classified as problem_feedback."""
        service = DeepSeekService()
        # This matches the "坏"/"broken" keywords → mock idx 0
        result = service.analyze_single("这个产品坏了，质量太差了")
        assert result.feedback_type == FeedbackType.problem_feedback
        assert result.requires_action is True
        assert result.action_priority in (
            ActionPriority.high, ActionPriority.medium,
            ActionPriority.critical,
        )

    def test_experience_feedback_detection(self):
        """Positive content should be classified as experience_feedback."""
        service = DeepSeekService()
        # This matches positive keywords → mock idx 4
        result = service.analyze_single("这个产品很好用，推荐大家购买")
        assert result.feedback_type == FeedbackType.experience_feedback
        assert result.requires_action is False
        assert result.action_priority == ActionPriority.low

    def test_suggestion_is_experience_feedback(self):
        """Product suggestions should be experience_feedback."""
        service = DeepSeekService()
        # Matches suggestion keywords → mock idx 10
        result = service.analyze_single("建议增加深色模式和自定义主题功能")
        assert result.feedback_type == FeedbackType.experience_feedback
        assert result.requires_action is False

    def test_ad_is_not_relevant(self):
        """Ads should be marked as not relevant."""
        service = DeepSeekService()
        result = service.analyze_single("限时优惠！全场五折！快来抢购！")
        assert result.is_relevant is False
        assert result.feedback_type == FeedbackType.unknown

    def test_security_issue_is_critical(self):
        """Security issues should have critical priority."""
        service = DeepSeekService()
        result = service.analyze_single("我的账号密码被泄露了，安全漏洞严重")
        assert result.feedback_type == FeedbackType.problem_feedback
        assert result.is_relevant is True
        assert result.severity >= 80

    def test_mock_returns_all_required_fields(self):
        """Every mock result should populate all new fields."""
        service = DeepSeekService()
        test_contents = [
            "产品质量太差了",
            "客服态度很好，产品也不错",
            "我的退款还没到账",
            "建议增加新功能",
            "这是广告内容快来买",
        ]
        for content in test_contents:
            result = service.analyze_single(content)
            assert result.feedback_type is not None
            assert result.feedback_type in (
                FeedbackType.problem_feedback,
                FeedbackType.experience_feedback,
                FeedbackType.unknown,
            )
            assert isinstance(result.requires_action, bool)
            assert result.action_priority is not None
            assert result.complaint_category is not None


class TestFeedbackRepoNewFilters:
    """Test repository with new filter fields."""

    def _create_items(self, db_session: Session):
        """Create test items with different feedback types."""
        configs = [
            ("problem_feedback", "product_quality", True, "high", "new"),
            ("problem_feedback", "security", True, "critical", "new"),
            ("experience_feedback", "none", False, "low", "ignored"),
            ("experience_feedback", "none", False, "low", "ignored"),
        ]
        for i, (fb_type, cat, req_act, priority, status) in enumerate(configs):
            content = f"test content {i} for {fb_type}"
            item = FeedbackItem(
                content_hash=compute_content_hash(content, f"platform{i}"),
                platform=f"platform{i}",
                content=content,
                brand="test",
            )
            db_session.add(item)
            db_session.flush()

            is_problem = (fb_type == "problem_feedback")
            analysis = FeedbackAnalysis(
                feedback_item_id=item.id,
                feedback_type=fb_type,
                sentiment="negative" if is_problem else "positive",
                sentiment_score=-0.7 if is_problem else 0.7,
                is_negative=is_problem,
                complaint_category=cat,
                severity=80 if is_problem else 5,
                confidence=0.9,
                requires_action=req_act,
                action_priority=priority,
                action_status=status,
            )
            db_session.add(analysis)
        db_session.commit()
        return configs

    def test_filter_by_feedback_type(self, db_session: Session):
        """Should filter by feedback_type."""
        self._create_items(db_session)
        from src.repositories.feedback_repo import search_items

        items, total = search_items(db_session, {"feedback_type": "problem_feedback"})
        assert total == 2
        for item in items:
            assert item.analysis.feedback_type == "problem_feedback"

    def test_filter_by_requires_action(self, db_session: Session):
        """Should filter by requires_action."""
        self._create_items(db_session)
        from src.repositories.feedback_repo import search_items

        items, total = search_items(db_session, {"requires_action": True})
        assert total == 2
        for item in items:
            assert item.analysis.requires_action is True

    def test_filter_by_action_priority(self, db_session: Session):
        """Should filter by action_priority."""
        self._create_items(db_session)
        from src.repositories.feedback_repo import search_items

        items, total = search_items(db_session, {"action_priority": "critical"})
        assert total == 1
        assert items[0].analysis.action_priority == "critical"

    def test_filter_by_action_status(self, db_session: Session):
        """Should filter by action_status."""
        self._create_items(db_session)
        from src.repositories.feedback_repo import search_items

        items, total = search_items(db_session, {"action_status": "new"})
        assert total == 2

    def test_stats_include_new_metrics(self, db_session: Session):
        """Stats should include problem/experience counts."""
        self._create_items(db_session)
        from src.repositories.feedback_repo import get_stats

        stats = get_stats(db_session)
        assert stats["problem_count"] == 2
        assert stats["experience_count"] == 2
        assert stats["high_priority"] >= 1
        assert "type_distribution" in stats
        assert len(stats["type_distribution"]) >= 2
        assert "action_statuses" in stats

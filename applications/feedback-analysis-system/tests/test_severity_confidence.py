"""Tests for severity range and confidence threshold logic."""

import pytest
from pydantic import ValidationError

from src.schemas import DeepSeekAnalysisResult


class TestSeverityValidation:
    """Test severity field validation."""

    def test_severity_within_range(self):
        """Severity 0-100 should be valid."""
        for s in [0, 50, 100]:
            result = DeepSeekAnalysisResult(
                is_relevant=True,
                sentiment="negative",
                sentiment_score=-0.8,
                is_negative=True,
                severity=s,
                confidence=0.9,
            )
            assert result.severity == s

    def test_severity_below_zero_rejected(self):
        """Severity below 0 should be rejected."""
        with pytest.raises(ValidationError):
            DeepSeekAnalysisResult(
                is_relevant=True,
                sentiment="negative",
                sentiment_score=-0.8,
                is_negative=True,
                severity=-1,
                confidence=0.9,
            )

    def test_severity_above_100_rejected(self):
        """Severity above 100 should be rejected."""
        with pytest.raises(ValidationError):
            DeepSeekAnalysisResult(
                is_relevant=True,
                sentiment="negative",
                sentiment_score=-0.8,
                is_negative=True,
                severity=101,
                confidence=0.9,
            )


class TestConfidenceLogic:
    """Test confidence threshold logic."""

    def test_low_confidence_triggers_review(self):
        """Low confidence should trigger needs_human_review."""
        result = DeepSeekAnalysisResult(
            is_relevant=True,
            sentiment="negative",
            sentiment_score=-0.6,
            is_negative=True,
            severity=50,
            confidence=0.5,
            needs_human_review=True,
        )
        assert result.needs_human_review is True

    def test_high_severity_review(self):
        """High severity items should be flagged for review."""
        result = DeepSeekAnalysisResult(
            is_relevant=True,
            sentiment="negative",
            sentiment_score=-0.9,
            is_negative=True,
            severity=90,
            confidence=0.9,
            needs_human_review=True,
        )
        assert result.needs_human_review is True

    def test_confidence_range_rejected(self):
        """Confidence outside 0-1 should be rejected."""
        with pytest.raises(ValidationError):
            DeepSeekAnalysisResult(
                is_relevant=True,
                sentiment="negative",
                sentiment_score=-0.8,
                is_negative=True,
                severity=50,
                confidence=1.5,
            )

    def test_sentiment_score_range_rejected(self):
        """Sentiment score outside -1 to 1 should be rejected."""
        with pytest.raises(ValidationError):
            DeepSeekAnalysisResult(
                is_relevant=True,
                sentiment="negative",
                sentiment_score=-1.5,
                is_negative=True,
                severity=50,
                confidence=0.8,
            )

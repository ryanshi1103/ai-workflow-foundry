"""Tests for DeepSeek service in mock mode."""

from src.schemas import DeepSeekAnalysisResult
from src.services.deepseek_service import DeepSeekService


class TestDeepSeekMock:
    """Test DeepSeek service with mock mode enabled."""

    def test_mock_mode_returns_valid_result(self):
        """Mock mode should return a valid DeepSeekAnalysisResult."""
        service = DeepSeekService()
        result = service.analyze_single("这个产品质量太差了")
        assert result is not None
        assert isinstance(result, DeepSeekAnalysisResult)

    def test_mock_result_has_required_fields(self):
        """Mock result should have all required fields populated."""
        service = DeepSeekService()
        result = service.analyze_single("Test content")
        assert result.sentiment is not None
        assert result.sentiment_score is not None
        assert result.is_negative is not None
        assert result.confidence is not None
        assert 0.0 <= result.confidence <= 1.0
        assert -1.0 <= result.sentiment_score <= 1.0
        assert 0 <= result.severity <= 100

    def test_mock_cache_works(self):
        """Same content should hit cache on second call."""
        service = DeepSeekService()
        service.clear_cache()
        r1 = service.analyze_single("Unique cache test content 12345")
        r2 = service.analyze_single("Unique cache test content 12345")
        # Results should be identical (from cache)
        assert r1.sentiment == r2.sentiment
        assert r1.severity == r2.severity

    def test_batch_analysis(self):
        """Batch analysis should return results for all items."""
        service = DeepSeekService()
        items = [
            {"content": "Product is bad", "platform": "twitter"},
            {"content": "Great product!", "platform": "facebook"},
            {"content": "Where is my order?", "platform": "amazon"},
        ]
        results = service.analyze_batch(items)
        assert len(results) == 3
        for _idx, result, error in results:
            assert error is None
            assert result is not None

    def test_negative_content_detected(self):
        """Mock should detect negative content about battery/product issues."""
        service = DeepSeekService()
        result = service.analyze_single("用了不到一个月电池就完全充不进去了")
        assert result.is_negative is True
        assert result.severity > 50

    def test_spam_content_detected(self):
        """Mock should detect spam/ad content."""
        service = DeepSeekService()
        result = service.analyze_single("限时优惠！！！全场5折起，点击链接购买")
        assert result.is_relevant is False

    def test_positive_content_not_negative(self):
        """Positive content should not be classified as negative."""
        service = DeepSeekService()
        result = service.analyze_single("这个产品真心不错，推荐给大家")
        assert result.is_negative is False
        assert result.sentiment == "positive"

    def test_severity_range_coerced(self):
        """Service should coerce severity to 0-100 range."""
        service = DeepSeekService()
        result = service.analyze_single("Test content")
        assert 0 <= result.severity <= 100

    def test_confidence_range_coerced(self):
        """Service should coerce confidence to 0.0-1.0 range."""
        service = DeepSeekService()
        result = service.analyze_single("Test content")
        assert 0.0 <= result.confidence <= 1.0

    def test_clear_cache(self):
        """Clear cache should work."""
        service = DeepSeekService()
        service.analyze_single("Cache clear test")
        service.clear_cache()
        # Should not error

    def test_mock_security_content_high_severity(self):
        """Security-related content should have high severity in mock."""
        service = DeepSeekService()
        result = service.analyze_single("账号被异地登录，密码泄露了，安全问题严重")
        assert result.severity >= 75
        assert result.needs_human_review is True

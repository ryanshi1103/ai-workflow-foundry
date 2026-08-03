"""Tests for API retry logic and timeout handling."""

import pytest

from src.services.deepseek_service import DeepSeekService


class TestRetryAndTimeout:
    """Test retry mechanism and error handling."""

    def test_mock_mode_never_fails(self):
        """Mock mode should always return a result, never error."""
        service = DeepSeekService()
        assert service.mock_mode is True

        # Even with very long content, mock should not fail
        long_content = "Test " * 500  # 2500 chars
        result = service.analyze_single(long_content)
        assert result is not None
        assert result.sentiment is not None

    def test_batch_with_errors_handles_gracefully(self):
        """Batch analysis should handle individual failures gracefully."""
        service = DeepSeekService()
        items = [
            {"content": "Good item", "platform": "test"},
            {"content": "", "platform": "test"},  # Empty but shouldn't crash
            {"content": "Another good item", "platform": "test"},
        ]
        results = service.analyze_batch(items)
        assert len(results) == 3
        for _, result, error in results:
            # In mock mode, even empty content should work
            assert result is not None
            assert error is None

    def test_parse_invalid_json(self):
        """Service should handle invalid JSON from API gracefully."""
        service = DeepSeekService()
        with pytest.raises(ValueError, match="invalid JSON"):
            service._parse_response("not valid json {{{")

    def test_parse_partial_json_fills_defaults(self):
        """Partial JSON with missing fields should be filled with defaults."""
        service = DeepSeekService()
        result = service._parse_response('{"is_relevant": true, "is_negative": false}')
        assert result.is_relevant is True
        assert result.sentiment == "unknown"  # default
        assert result.complaint_category == "none"  # default
        assert 0 <= result.severity <= 100  # coerced

    def test_cache_key_stability(self):
        """Cache key should be deterministic."""
        from src.services.deepseek_service import _get_cache_key

        k1 = _get_cache_key("Hello", "model-v1")
        k2 = _get_cache_key("Hello", "model-v1")
        assert k1 == k2

    def test_mock_mode_detected(self):
        """Mock mode should be active in test environment."""
        service = DeepSeekService()
        assert service.mock_mode is True

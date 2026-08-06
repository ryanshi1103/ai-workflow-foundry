"""Tests for CSV import and validation."""

import pytest

from src.schemas import ImportRow


class TestImportRowValidation:
    """Test ImportRow Pydantic validation."""

    def test_valid_row(self):
        """A valid row should pass validation."""
        row = ImportRow(platform="twitter", content="Hello world")
        assert row.platform == "twitter"
        assert row.content == "Hello world"

    def test_empty_platform(self):
        """Empty platform should raise validation error."""
        with pytest.raises(ValueError, match="platform"):
            ImportRow(platform="", content="Hello")

    def test_empty_content(self):
        """Empty content should raise validation error."""
        with pytest.raises(ValueError, match="content"):
            ImportRow(platform="twitter", content="")

    def test_whitespace_only_platform(self):
        """Whitespace-only platform should raise error."""
        with pytest.raises(ValueError, match="platform"):
            ImportRow(platform="   ", content="Hello")

    def test_content_length_limit(self):
        """Content exceeding max length should raise error."""
        long_content = "x" * 10001
        with pytest.raises(ValueError, match="10000"):
            ImportRow(platform="twitter", content=long_content)

    def test_optional_fields_default_none(self):
        """Optional fields should default to None."""
        row = ImportRow(platform="twitter", content="Hello")
        assert row.source_url is None
        assert row.brand is None
        assert row.language is None

    def test_platform_stripped(self):
        """Platform should be stripped of whitespace."""
        row = ImportRow(platform="  twitter  ", content="Hello")
        assert row.platform == "twitter"

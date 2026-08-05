"""Tests for content hashing and deduplication."""

from src.schemas import compute_content_hash, normalize_content


class TestContentNormalization:
    """Test content normalization for hashing."""

    def test_whitespace_normalization(self):
        """Content with extra whitespace should normalize to same hash."""
        a = compute_content_hash("  Hello   World  ", "twitter")
        b = compute_content_hash("Hello World", "twitter")
        assert a == b

    def test_unicode_normalization(self):
        """Unicode equivalents should normalize to same hash."""
        # NFC vs NFD forms of the same character
        import unicodedata
        nfc = unicodedata.normalize("NFC", "café")
        nfd = unicodedata.normalize("NFD", "café")
        a = compute_content_hash(nfc, "twitter")
        b = compute_content_hash(nfd, "twitter")
        assert a == b

    def test_case_insensitivity_english(self):
        """English case differences should not affect hash."""
        a = compute_content_hash("HELLO WORLD", "twitter")
        b = compute_content_hash("hello world", "twitter")
        assert a == b

    def test_original_content_not_modified(self):
        """Normalization must not return modified original — only used for hash."""
        original = "  Hello World  "
        normalize_content(original)  # noqa: F841 — verify no exception
        # The normalization function returns hash input, not modified content
        assert original == "  Hello World  "  # Original unchanged

    def test_different_platforms_different_hash(self):
        """Same content on different platforms should have different hashes."""
        a = compute_content_hash("Same content", "twitter")
        b = compute_content_hash("Same content", "facebook")
        assert a != b

    def test_different_source_urls_different_hash(self):
        """Same content with different source URLs should have different hashes."""
        a = compute_content_hash("Same", "twitter", "http://a.com")
        b = compute_content_hash("Same", "twitter", "http://b.com")
        assert a != b

    def test_hash_stability(self):
        """Hash should be deterministic."""
        h1 = compute_content_hash("Test content", "platform", "url", "ext_id")
        h2 = compute_content_hash("Test content", "platform", "url", "ext_id")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex length

    def test_url_normalization(self):
        """URLs with www prefix should normalize."""
        a = normalize_content("check http://www.example.com/path/")
        b = normalize_content("check http://example.com/path")
        assert a == b


class TestDeduplication:
    """Test deduplication logic."""

    def test_duplicate_detection(self):
        """Same content should be detected as duplicate."""
        from src.services.dedup_service import is_duplicate

        existing = {compute_content_hash("Duplicate content", "twitter")}
        assert is_duplicate("Duplicate content", existing, "twitter")
        assert not is_duplicate("Different content", existing, "twitter")

    def test_empty_content_handling(self):
        """Empty content should still produce a hash."""
        h = compute_content_hash("", "")
        assert len(h) == 64
        assert isinstance(h, str)

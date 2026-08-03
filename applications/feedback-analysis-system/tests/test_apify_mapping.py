"""Tests for Apify field mapping."""

from src.connectors.apify_connector import ApifyConnector
from src.schemas import ApifyFieldMapping


class TestApifyFieldMapping:
    """Test Apify connector field mapping."""

    def test_basic_mapping(self):
        """Should map fields correctly."""
        connector = ApifyConnector()
        actor_output = {
            "platform": "twitter",
            "content": "Hello world",
            "url": "https://twitter.com/post/1",
            "id": "12345",
            "author": {"name": "testuser"},
            "engagement_count": 42,
        }

        row = connector.map_item(actor_output)
        assert row.platform == "twitter"
        assert row.content == "Hello world"
        assert row.source_url == "https://twitter.com/post/1"
        assert row.external_id == "12345"
        assert row.author_display_name == "testuser"
        assert row.engagement_count == 42

    def test_nested_field_mapping(self):
        """Should handle nested field paths like author.name."""
        connector = ApifyConnector()
        actor_output = {
            "platform": "reddit",
            "content": "Post",
            "author": {"name": "nested_user"},
        }
        row = connector.map_item(actor_output)
        assert row.author_display_name == "nested_user"

    def test_missing_fields_default(self):
        """Missing fields should use defaults."""
        connector = ApifyConnector()
        actor_output = {
            "platform": "test",
            "content": "Minimal post",
        }
        row = connector.map_item(actor_output)
        assert row.platform == "test"
        assert row.content == "Minimal post"
        assert row.source_url is None

    def test_custom_mapping(self):
        """Custom field mapping should be respected."""
        custom = ApifyFieldMapping(
            platform="source",
            content="text",
            source_url="link",
        )
        connector = ApifyConnector(mapping=custom)
        actor_output = {
            "source": "custom_platform",
            "text": "Custom content",
            "link": "https://example.com",
        }
        row = connector.map_item(actor_output)
        assert row.platform == "custom_platform"
        assert row.content == "Custom content"
        assert row.source_url == "https://example.com"

    def test_mock_run_returns_data(self):
        """Mock Apify run should return mock data."""
        connector = ApifyConnector()
        result = connector.run_actor({"searchTerms": ["test"]})
        assert result["status"] == "mock"
        assert len(result["items"]) > 0
        assert result["success_count"] > 0

    def test_apify_not_configured_by_default(self):
        """Apify should not be configured without token."""
        connector = ApifyConnector()
        assert connector.is_configured is False, "Expected unconfigured in test environment"

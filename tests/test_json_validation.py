"""Tests for JSON import validation."""

import json

from sqlalchemy.orm import Session

from src.services.import_service import import_json_string


class TestJsonImport:
    """Test JSON import functionality."""

    def test_import_valid_json_array(self, db_session: Session):
        """Valid JSON array should import successfully."""
        data = json.dumps([
            {"platform": "twitter", "content": "Hello world"},
            {"platform": "facebook", "content": "Another post"},
        ])
        result = import_json_string(db_session, data)
        assert result.new == 2
        assert result.total == 2
        assert result.errors == 0

    def test_import_single_object(self, db_session: Session):
        """Single JSON object should be wrapped and imported."""
        data = json.dumps({"platform": "twitter", "content": "Single post"})
        result = import_json_string(db_session, data)
        assert result.new == 1

    def test_import_missing_required_fields(self, db_session: Session):
        """Rows missing required fields should be marked invalid."""
        data = json.dumps([
            {"content": "Missing platform"},
            {"platform": "Missing content"},
        ])
        result = import_json_string(db_session, data)
        assert result.invalid == 2
        assert result.new == 0

    def test_import_invalid_json(self, db_session: Session):
        """Invalid JSON should produce an error."""
        result = import_json_string(db_session, "not valid json at all")
        assert result.errors == 1
        assert "JSON 解析失败" in result.error_details[0]

    def test_import_not_array_or_object(self, db_session: Session):
        """Non-array/non-object JSON should error."""
        result = import_json_string(db_session, '"just a string"')
        assert result.errors == 1

    def test_import_empty_string_content(self, db_session: Session):
        """Empty content field should be invalid."""
        data = json.dumps([{"platform": "twitter", "content": ""}])
        result = import_json_string(db_session, data)
        assert result.invalid >= 1 or result.new == 0

    def test_duplicate_import(self, db_session: Session):
        """Duplicate content should not be re-imported."""
        data = json.dumps([
            {"platform": "twitter", "content": "Same content"},
        ])
        result1 = import_json_string(db_session, data)
        assert result1.new == 1

        result2 = import_json_string(db_session, data)
        assert result2.duplicates == 1
        assert result2.new == 0

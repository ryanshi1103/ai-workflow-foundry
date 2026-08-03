"""Tests for CSV and JSON export."""

from sqlalchemy.orm import Session

from src.models import FeedbackAnalysis, FeedbackItem
from src.schemas import compute_content_hash
from src.services.export_service import export_csv, export_json_str


class TestExport:
    """Test export functionality."""

    def _create_test_data(self, db_session: Session):
        """Helper to create test data."""
        items = []
        for i in range(3):
            content = f"测试内容 {i} — 中文测试"
            item = FeedbackItem(
                content_hash=compute_content_hash(content, "weibo"),
                platform="weibo",
                content=content,
                language="zh",
                brand="测试品牌",
            )
            db_session.add(item)
            db_session.flush()

            analysis = FeedbackAnalysis(
                feedback_item_id=item.id,
                sentiment="negative" if i < 2 else "positive",
                sentiment_score=-0.7 if i < 2 else 0.8,
                is_negative=(i < 2),
                severity=60 if i < 2 else 5,
                confidence=0.85,
                summary=f"摘要 {i}",
                model_name="test-model",
            )
            db_session.add(analysis)
            items.append(item)
        db_session.commit()
        return items

    def test_export_csv_utf8_sig(self, db_session: Session):
        """CSV export should have UTF-8 BOM for Excel compatibility."""
        self._create_test_data(db_session)
        csv_data = export_csv(db_session)
        assert csv_data.startswith("﻿")  # BOM
        assert "测试内容" in csv_data

    def test_export_csv_has_all_rows(self, db_session: Session):
        """CSV should contain all test rows."""
        self._create_test_data(db_session)
        csv_data = export_csv(db_session)
        lines = csv_data.strip().split("\n")
        # header + 3 data rows
        assert len(lines) >= 4, f"Expected 4+ lines, got {len(lines)}"

    def test_export_json(self, db_session: Session):
        """JSON export should produce valid JSON."""
        self._create_test_data(db_session)
        json_data = export_json_str(db_session)
        import json
        parsed = json.loads(json_data)
        assert isinstance(parsed, list)
        assert len(parsed) == 3

    def test_export_empty_db(self, db_session: Session):
        """Export should handle empty database gracefully."""
        csv_data = export_csv(db_session)
        assert csv_data.startswith("﻿")

        json_data = export_json_str(db_session)
        assert json_data == "[]"

    def test_export_json_contains_chinese(self, db_session: Session):
        """JSON export should preserve Chinese characters."""
        self._create_test_data(db_session)
        json_data = export_json_str(db_session)
        assert "中文测试" in json_data
        assert "测试内容" in json_data

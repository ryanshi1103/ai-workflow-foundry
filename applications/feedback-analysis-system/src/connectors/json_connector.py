"""JSON file connector for data import."""

import json
from pathlib import Path

from src.connectors.base import BaseConnector
from src.schemas import ImportRow


class JsonConnector(BaseConnector):
    """Read ImportRow data from a JSON file (array of objects)."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def fetch(self) -> list[ImportRow]:
        """Parse JSON file and return ImportRow list."""
        with open(self.file_path, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            data = [data]

        rows: list[ImportRow] = []
        for raw_obj in data:
            if not isinstance(raw_obj, dict):
                continue
            try:
                row = ImportRow(
                    platform=str(raw_obj.get("platform", "")),
                    content=str(raw_obj.get("content", "")),
                    source_url=raw_obj.get("source_url") or None,
                    external_id=raw_obj.get("external_id") or None,
                    author_display_name=raw_obj.get("author_display_name") or None,
                    published_at=raw_obj.get("published_at") or None,
                    engagement_count=_safe_int(raw_obj.get("engagement_count")),
                    brand=raw_obj.get("brand") or None,
                    product=raw_obj.get("product") or None,
                    search_keyword=raw_obj.get("search_keyword") or None,
                    language=raw_obj.get("language") or None,
                )
                rows.append(row)
            except ValueError:
                continue
        return rows


def _safe_int(val) -> int | None:
    try:
        return int(val) if val is not None else None
    except (ValueError, TypeError):
        return None

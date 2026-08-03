"""CSV file connector for data import."""

from pathlib import Path

from src.connectors.base import BaseConnector
from src.schemas import ImportRow


class CsvConnector(BaseConnector):
    """Read ImportRow data from a CSV file."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def fetch(self) -> list[ImportRow]:
        """Parse CSV file and return ImportRow list."""
        import csv

        rows: list[ImportRow] = []
        with open(self.file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for raw in reader:
                normalized = {k.strip().lower(): v.strip() if isinstance(v, str) else v
                              for k, v in raw.items()}
                try:
                    row = ImportRow(
                        platform=normalized.get("platform", ""),
                        content=normalized.get("content", ""),
                        source_url=normalized.get("source_url") or None,
                        external_id=normalized.get("external_id") or None,
                        author_display_name=normalized.get("author_display_name") or None,
                        published_at=normalized.get("published_at") or None,
                        engagement_count=_safe_int(normalized.get("engagement_count")),
                        brand=normalized.get("brand") or None,
                        product=normalized.get("product") or None,
                        search_keyword=normalized.get("search_keyword") or None,
                        language=normalized.get("language") or None,
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

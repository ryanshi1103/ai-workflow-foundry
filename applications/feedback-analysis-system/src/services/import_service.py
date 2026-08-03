"""Import service for CSV, JSON, and example data."""

import csv
import io
import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from src.models import FeedbackItem
from src.schemas import ImportResult, ImportRow, compute_content_hash

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _get_existing_hashes(db: Session) -> set[str]:
    """Get all existing content hashes from the database."""
    results = db.query(FeedbackItem.content_hash).all()
    return {r[0] for r in results}


def import_rows(db: Session, rows: list[ImportRow]) -> ImportResult:
    """Import a list of validated ImportRow objects."""
    result = ImportResult(total=len(rows))
    existing_hashes = _get_existing_hashes(db)

    new_items: list[FeedbackItem] = []

    for row in rows:
        h = compute_content_hash(
            row.content, row.platform, row.source_url or "", row.external_id or ""
        )

        if h in existing_hashes:
            result.duplicates += 1
            continue

        existing_hashes.add(h)

        # Parse published_at
        pub_at = None
        if row.published_at:
            try:
                pub_at = datetime.fromisoformat(row.published_at.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pub_at = None

        item = FeedbackItem(
            content_hash=h,
            platform=row.platform,
            source_type=row.source_type,
            source_url=row.source_url,
            external_id=row.external_id,
            author_display_name=row.author_display_name,
            content=row.content,
            language=row.language,
            published_at=pub_at,
            collected_at=datetime.now(UTC),
            engagement_count=row.engagement_count,
            search_keyword=row.search_keyword,
            brand=row.brand,
            product=row.product,
            analysis_status="pending",
        )
        new_items.append(item)
        result.new += 1

    if new_items:
        db.add_all(new_items)
        db.commit()

    return result


def import_csv_string(db: Session, csv_content: str) -> ImportResult:
    """Import data from a CSV string. Returns ImportResult with error details."""
    result = ImportResult()
    rows: list[ImportRow] = []

    try:
        reader = csv.DictReader(io.StringIO(csv_content))
    except Exception as e:
        result.errors = 1
        result.error_details.append(f"CSV 解析失败: {e}")
        return result

    if reader.fieldnames is None:
        result.errors = 1
        result.error_details.append("CSV 文件为空或缺少表头")
        return result

    for line_num, raw_row in enumerate(reader, start=2):
        result.total += 1
        try:
            # Normalize keys to lowercase
            normalized = {k.strip().lower(): v.strip() if isinstance(v, str) else v
                          for k, v in raw_row.items()}
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
        except ValueError as e:
            result.invalid += 1
            result.error_details.append(f"第 {line_num} 行: {e}")
        except Exception as e:
            result.errors += 1
            result.error_details.append(f"第 {line_num} 行未知错误: {e}")

    # Import valid rows
    if rows:
        sub_result = import_rows(db, rows)
        result.new = sub_result.new
        result.duplicates = sub_result.duplicates
        # Don't double-count; import_rows already excludes invalid
        # Note: invalid rows from validation never reached import_rows

    return result


def import_json_string(db: Session, json_content: str) -> ImportResult:
    """Import data from a JSON string (array of objects or single object)."""
    result = ImportResult()

    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        result.errors = 1
        result.error_details.append(f"JSON 解析失败: {e}")
        return result

    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        result.errors = 1
        result.error_details.append("JSON 必须是对象数组或单个对象")
        return result

    rows: list[ImportRow] = []
    for i, raw_obj in enumerate(data):
        result.total += 1
        if not isinstance(raw_obj, dict):
            result.invalid += 1
            result.error_details.append(f"第 {i + 1} 条: 不是有效的 JSON 对象")
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
        except ValueError as e:
            result.invalid += 1
            result.error_details.append(f"第 {i + 1} 条: {e}")
        except Exception as e:
            result.errors += 1
            result.error_details.append(f"第 {i + 1} 条未知错误: {e}")

    if rows:
        sub_result = import_rows(db, rows)
        result.new = sub_result.new
        result.duplicates = sub_result.duplicates

    return result


def _safe_int(val: Any) -> int | None:
    """Safely convert a value to int, returning None on failure."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

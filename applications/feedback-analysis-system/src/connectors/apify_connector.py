"""Generic Apify connector — actor-agnostic with field mapping.

Hides real-collection UI when APIFY_TOKEN is not configured.
Provides mock data for demo.
"""

import logging
from typing import Any

from src.config import APIFY_ACTOR_ID, APIFY_MAX_ITEMS, APIFY_TOKEN, APP_MOCK_MODE
from src.schemas import ApifyFieldMapping, ImportRow

logger = logging.getLogger(__name__)


def _get_nested(obj: dict[str, Any], path: str) -> Any:
    """Get a nested value by dot-separated path, e.g. 'author.name'."""
    parts = path.split(".")
    current: Any = obj
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


class ApifyConnector:
    """Generic Apify connector that works with any Actor via field mapping."""

    def __init__(self, mapping: ApifyFieldMapping | None = None):
        self.mapping = mapping or ApifyFieldMapping()

    @property
    def is_configured(self) -> bool:
        return bool(APIFY_TOKEN and APIFY_ACTOR_ID)

    def map_item(self, actor_output: dict[str, Any]) -> ImportRow:
        """Map an Actor output record to ImportRow using field mappings."""
        m = self.mapping

        def _str_val(path: str) -> str:
            v = _get_nested(actor_output, path)
            return str(v) if v is not None else ""

        def _opt_str(path: str) -> str | None:
            v = _get_nested(actor_output, path)
            return str(v) if v is not None else None

        def _opt_int(path: str) -> int | None:
            v = _get_nested(actor_output, path)
            try:
                return int(v) if v is not None else None
            except (ValueError, TypeError):
                return None

        platform = _str_val(m.platform) or "apify_import"

        return ImportRow(
            platform=platform,
            content=_str_val(m.content),
            source_url=_opt_str(m.source_url),
            external_id=_opt_str(m.external_id),
            author_display_name=_opt_str(m.author_display_name),
            published_at=_opt_str(m.published_at),
            engagement_count=_opt_int(m.engagement_count),
            brand=_opt_str(m.brand),
            product=_opt_str(m.product),
            search_keyword=_opt_str(m.search_keyword),
            language=_opt_str(m.language),
            source_type="apify",
        )

    def run_actor(self, actor_input: dict[str, Any]) -> dict[str, Any]:
        """Start an Apify Actor run, wait for completion, fetch dataset.

        Returns:
            {
                "status": "success" | "error" | "mock",
                "items": list of ImportRow,
                "total_count": int,
                "success_count": int,
                "error_count": int,
                "errors": list of str,
            }
        """
        if APP_MOCK_MODE or not self.is_configured:
            return self._mock_run()

        try:
            from apify_client import ApifyClient

            client = ApifyClient(token=APIFY_TOKEN)
        except ImportError:
            return {
                "status": "error",
                "items": [],
                "total_count": 0,
                "success_count": 0,
                "error_count": 1,
                "errors": ["apify-client 未安装"],
            }

        try:
            actor = client.actor(APIFY_ACTOR_ID)
            run = actor.start(run_input=actor_input)
            run_info = client.run(run["id"]).wait_for_finish()

            if run_info is None:
                return {
                    "status": "error",
                    "items": [],
                    "total_count": 0,
                    "success_count": 0,
                    "error_count": 1,
                    "errors": ["Actor 运行失败，未获取到结果"],
                }

            # Fetch dataset
            dataset = client.dataset(run_info["defaultDatasetId"])
            items_page = dataset.list_items(limit=APIFY_MAX_ITEMS)

            items: list[ImportRow] = []
            errors: list[str] = []
            success = 0
            error_count = 0

            for raw_item in items_page.items:
                try:
                    row = self.map_item(raw_item)
                    items.append(row)
                    success += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"字段映射失败: {e}")

            return {
                "status": "success",
                "items": items,
                "total_count": len(items_page.items),
                "success_count": success,
                "error_count": error_count,
                "errors": errors,
            }

        except Exception as e:
            logger.exception("Apify actor run failed")
            return {
                "status": "error",
                "items": [],
                "total_count": 0,
                "success_count": 0,
                "error_count": 1,
                "errors": [str(e)],
            }

    def _mock_run(self) -> dict[str, Any]:
        """Return mock Apify data for demo."""
        from src.connectors.mock_connector import MOCK_DATA

        mock_items = MOCK_DATA[:10]
        items = []
        for raw in mock_items:
            row = ImportRow(
                platform=raw["platform"],
                content=raw["content"],
                source_url=None,
                external_id=f"apify-mock-{raw['external_id']}",
                author_display_name=raw.get("author_display_name"),
                language=raw.get("language"),
                brand=raw.get("brand") or None,
                product=raw.get("product") or None,
                search_keyword=raw.get("search_keyword") or None,
            )
            items.append(row)

        return {
            "status": "mock",
            "items": items,
            "total_count": len(items),
            "success_count": len(items),
            "error_count": 0,
            "errors": [],
        }

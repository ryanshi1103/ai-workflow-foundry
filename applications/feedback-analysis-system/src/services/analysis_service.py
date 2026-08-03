"""Orchestration service for running batch analysis and persisting results."""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from src.models import FeedbackAnalysis, FeedbackItem
from src.schemas import DeepSeekAnalysisResult
from src.services.deepseek_service import deepseek_service

logger = logging.getLogger(__name__)

PROMPT_VERSION = "sentiment_v1"


def run_analysis(
    db: Session,
    item_ids: list[int],
    max_concurrency: int | None = None,
    on_progress: Any = None,
) -> dict[str, int]:
    """Run analysis on a list of feedback items.

    Args:
        db: Database session
        item_ids: List of FeedbackItem IDs to analyze
        max_concurrency: Max parallel API calls
        on_progress: Optional callback(completed, total)

    Returns:
        Dict with counts: completed, error, total
    """
    # Fetch items
    items = db.query(FeedbackItem).filter(FeedbackItem.id.in_(item_ids)).all()

    if not items:
        return {"completed": 0, "error": 0, "total": 0}

    # Mark all as analyzing
    for item in items:
        item.analysis_status = "analyzing"
    db.commit()

    # Prepare item dicts for the batch analyzer
    item_dicts = [
        {
            "id": item.id,
            "content": item.content,
            "platform": item.platform,
            "author_display_name": item.author_display_name,
            "published_at": item.published_at.isoformat() if item.published_at else "",
            "engagement_count": str(item.engagement_count or 0),
            "brand": item.brand,
            "product": item.product,
        }
        for item in items
    ]

    results = deepseek_service.analyze_batch(
        items=item_dicts,
        max_concurrency=max_concurrency,
        on_progress=on_progress,
    )

    completed = 0
    errors = 0

    for idx, result, error_msg in results:
        item_dict = item_dicts[idx]
        item_id = item_dict["id"]
        item = db.query(FeedbackItem).filter(FeedbackItem.id == item_id).first()
        if not item:
            continue

        if result is not None and error_msg is None:
            _save_analysis(db, item, result)
            item.analysis_status = "completed"
            completed += 1
        else:
            item.analysis_status = "error"
            logger.error("Item %d analysis error: %s", item_id, error_msg)
            errors += 1

    db.commit()
    return {"completed": completed, "error": errors, "total": len(items)}


def _save_analysis(
    db: Session,
    item: FeedbackItem,
    result: DeepSeekAnalysisResult,
):
    """Save analysis result to database."""
    existing = (
        db.query(FeedbackAnalysis)
        .filter(FeedbackAnalysis.feedback_item_id == item.id)
        .first()
    )

    if existing:
        # Update existing analysis
        existing.is_relevant = result.is_relevant
        existing.feedback_type = result.feedback_type.value
        existing.sentiment = result.sentiment.value
        existing.sentiment_score = result.sentiment_score
        existing.is_negative = result.is_negative
        existing.complaint_category = result.complaint_category.value
        existing.complaint_subcategory = result.complaint_subcategory
        existing.target = result.target
        existing.severity = result.severity
        existing.urgency = result.urgency.value
        existing.requires_action = result.requires_action
        existing.action_priority = result.action_priority.value
        existing.confidence = result.confidence
        existing.summary = result.summary
        existing.evidence = result.evidence
        existing.suggested_action = result.suggested_action
        existing.model_name = deepseek_service.model_name
        existing.prompt_version = PROMPT_VERSION
        existing.needs_human_review = result.needs_human_review
        existing.analyzed_at = datetime.now(UTC)
    else:
        analysis = FeedbackAnalysis(
            feedback_item_id=item.id,
            is_relevant=result.is_relevant,
            feedback_type=result.feedback_type.value,
            sentiment=result.sentiment.value,
            sentiment_score=result.sentiment_score,
            is_negative=result.is_negative,
            complaint_category=result.complaint_category.value,
            complaint_subcategory=result.complaint_subcategory,
            target=result.target,
            severity=result.severity,
            urgency=result.urgency.value,
            requires_action=result.requires_action,
            action_priority=result.action_priority.value,
            confidence=result.confidence,
            summary=result.summary,
            evidence=result.evidence,
            suggested_action=result.suggested_action,
            model_name=deepseek_service.model_name,
            prompt_version=PROMPT_VERSION,
            needs_human_review=result.needs_human_review,
            analyzed_at=datetime.now(UTC),
        )
        db.add(analysis)


def reanalyze_items(db: Session, item_ids: list[int]) -> dict[str, int]:
    """Re-run analysis on already-analyzed items."""
    # Reset status
    db.query(FeedbackItem).filter(FeedbackItem.id.in_(item_ids)).update(
        {"analysis_status": "pending"}, synchronize_session=False
    )
    db.commit()
    return run_analysis(db, item_ids)

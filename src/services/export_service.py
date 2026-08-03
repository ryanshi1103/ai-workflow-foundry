"""Export service for CSV and JSON output."""

import csv
import io
import json
from typing import Any

from sqlalchemy.orm import Session

from src.models import FeedbackAnalysis, FeedbackItem, HumanReview
from src.schemas import ExportRow


def _build_export_rows(db: Session, item_ids: list[int] | None = None,
                       filters: dict[str, Any] | None = None) -> list[ExportRow]:
    """Build export rows from database query."""
    query = db.query(
        FeedbackItem,
        FeedbackAnalysis,
        HumanReview,
    ).outerjoin(
        FeedbackAnalysis, FeedbackAnalysis.feedback_item_id == FeedbackItem.id
    ).outerjoin(
        HumanReview, HumanReview.feedback_item_id == FeedbackItem.id
    )

    if item_ids:
        query = query.filter(FeedbackItem.id.in_(item_ids))

    if filters:
        if filters.get("platform"):
            query = query.filter(FeedbackItem.platform == filters["platform"])
        if filters.get("sentiment"):
            query = query.filter(FeedbackAnalysis.sentiment == filters["sentiment"])
        if filters.get("is_negative") is not None:
            query = query.filter(FeedbackAnalysis.is_negative == filters["is_negative"])
        if filters.get("complaint_category"):
            query = query.filter(
                FeedbackAnalysis.complaint_category == filters["complaint_category"]
            )
        if filters.get("feedback_type"):
            query = query.filter(
                FeedbackAnalysis.feedback_type == filters["feedback_type"]
            )
        if filters.get("requires_action") is not None:
            query = query.filter(
                FeedbackAnalysis.requires_action == filters["requires_action"]
            )
        if filters.get("action_priority"):
            query = query.filter(
                FeedbackAnalysis.action_priority == filters["action_priority"]
            )
        if filters.get("action_status"):
            query = query.filter(
                FeedbackAnalysis.action_status == filters["action_status"]
            )
        if filters.get("needs_human_review") is not None:
            query = query.filter(
                FeedbackAnalysis.needs_human_review == filters["needs_human_review"]
            )
        if filters.get("analysis_status"):
            query = query.filter(FeedbackItem.analysis_status == filters["analysis_status"])
        if filters.get("brand"):
            query = query.filter(FeedbackItem.brand == filters["brand"])
        if filters.get("product"):
            query = query.filter(FeedbackItem.product == filters["product"])

    # Limit to prevent memory issues
    if not item_ids:
        query = query.limit(10000)

    results = query.all()

    rows = []
    for item, analysis, review in results:
        row = ExportRow(
            id=item.id,
            platform=item.platform,
            source_url=item.source_url,
            external_id=item.external_id,
            author_display_name=item.author_display_name,
            content=item.content,
            language=item.language,
            published_at=item.published_at.isoformat() if item.published_at else None,
            collected_at=item.collected_at.isoformat() if item.collected_at else None,
            analysis_status=item.analysis_status,
            is_relevant=analysis.is_relevant if analysis else None,
            feedback_type=analysis.feedback_type if analysis else None,
            sentiment=analysis.sentiment if analysis else None,
            sentiment_score=analysis.sentiment_score if analysis else None,
            is_negative=analysis.is_negative if analysis else None,
            complaint_category=analysis.complaint_category if analysis else None,
            complaint_subcategory=analysis.complaint_subcategory if analysis else None,
            target=analysis.target if analysis else None,
            severity=analysis.severity if analysis else None,
            urgency=analysis.urgency if analysis else None,
            confidence=analysis.confidence if analysis else None,
            summary=analysis.summary if analysis else None,
            evidence=analysis.evidence if analysis else None,
            suggested_action=analysis.suggested_action if analysis else None,
            requires_action=analysis.requires_action if analysis else None,
            action_priority=analysis.action_priority if analysis else None,
            action_status=analysis.action_status if analysis else None,
            model_name=analysis.model_name if analysis else None,
            analyzed_at=analysis.analyzed_at.isoformat() if analysis and analysis.analyzed_at else None,
            needs_human_review=analysis.needs_human_review if analysis else None,
            corrected_sentiment=review.corrected_sentiment if review else None,
            corrected_category=review.corrected_category if review else None,
            corrected_severity=review.corrected_severity if review else None,
            corrected_feedback_type=review.corrected_feedback_type if review else None,
            corrected_requires_action=review.corrected_requires_action if review else None,
            corrected_action_priority=review.corrected_action_priority if review else None,
            corrected_action_status=review.corrected_action_status if review else None,
            is_misjudged=review.is_misjudged if review else None,
            review_notes=review.review_notes if review else None,
            review_status=review.review_status if review else None,
            reviewed_at=review.reviewed_at.isoformat() if review and review.reviewed_at else None,
        )
        rows.append(row)

    return rows


def export_csv(db: Session, item_ids: list[int] | None = None,
               filters: dict[str, Any] | None = None) -> str:
    """Export data as CSV string (UTF-8-SIG for Excel compatibility)."""
    rows = _build_export_rows(db, item_ids, filters)

    output = io.StringIO()
    # Write BOM for Excel
    output.write("﻿")

    if rows:
        fieldnames = list(ExportRow.model_fields.keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.model_dump())

    return output.getvalue()


def export_json_str(db: Session, item_ids: list[int] | None = None,
                    filters: dict[str, Any] | None = None) -> str:
    """Export data as JSON string."""
    rows = _build_export_rows(db, item_ids, filters)
    return json.dumps([row.model_dump() for row in rows], ensure_ascii=False, indent=2)

"""Repository for FeedbackItem queries and filtering."""

from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from feedback_intelligence.models import FeedbackAnalysis, FeedbackItem, HumanReview


def get_stats(db: Session) -> dict:
    """Get dashboard statistics."""
    total = db.query(FeedbackItem).count()
    negative = db.query(FeedbackAnalysis).filter(
        FeedbackAnalysis.is_negative == True  # noqa: E712
    ).count()
    high_severity = db.query(FeedbackAnalysis).filter(
        FeedbackAnalysis.severity >= 75
    ).count()
    needs_review = db.query(FeedbackAnalysis).filter(
        FeedbackAnalysis.needs_human_review == True  # noqa: E712
    ).count()

    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    today_new = db.query(FeedbackItem).filter(
        FeedbackItem.created_at >= today
    ).count()

    # Feedback type counts
    problem_count = db.query(FeedbackAnalysis).filter(
        FeedbackAnalysis.feedback_type == "problem_feedback"
    ).count()
    experience_count = db.query(FeedbackAnalysis).filter(
        FeedbackAnalysis.feedback_type == "experience_feedback"
    ).count()

    # Problem feedback stats
    high_priority = db.query(FeedbackAnalysis).filter(
        FeedbackAnalysis.feedback_type == "problem_feedback",
        FeedbackAnalysis.action_priority.in_(["high", "critical"]),
    ).count()
    resolved_count = db.query(FeedbackAnalysis).filter(
        FeedbackAnalysis.feedback_type == "problem_feedback",
        FeedbackAnalysis.action_status == "resolved",
    ).count()
    pending_action = db.query(FeedbackAnalysis).filter(
        FeedbackAnalysis.feedback_type == "problem_feedback",
        FeedbackAnalysis.requires_action == True,  # noqa: E712
        FeedbackAnalysis.action_status == "new",
    ).count()

    # Experience feedback stats
    positive_count = db.query(FeedbackAnalysis).filter(
        FeedbackAnalysis.feedback_type == "experience_feedback",
        FeedbackAnalysis.sentiment == "positive",
    ).count()
    suggestion_count = db.query(FeedbackAnalysis).filter(
        FeedbackAnalysis.feedback_type == "experience_feedback",
        FeedbackAnalysis.sentiment.in_(["neutral", "mixed"]),
        FeedbackAnalysis.complaint_category == "none",
    ).count()
    feature_request_count = db.query(FeedbackAnalysis).filter(
        FeedbackAnalysis.feedback_type == "experience_feedback",
        FeedbackAnalysis.complaint_subcategory.like("%feature%"),
    ).count()

    # Platforms
    platform_counts = (
        db.query(FeedbackItem.platform, func.count(FeedbackItem.id))
        .group_by(FeedbackItem.platform)
        .all()
    )

    # Categories
    category_counts = (
        db.query(FeedbackAnalysis.complaint_category, func.count(FeedbackAnalysis.id))
        .group_by(FeedbackAnalysis.complaint_category)
        .all()
    )

    # Feedback type distribution
    type_counts = (
        db.query(FeedbackAnalysis.feedback_type, func.count(FeedbackAnalysis.id))
        .group_by(FeedbackAnalysis.feedback_type)
        .all()
    )

    # Action status distribution
    action_status_counts = (
        db.query(FeedbackAnalysis.action_status, func.count(FeedbackAnalysis.id))
        .filter(FeedbackAnalysis.feedback_type == "problem_feedback")
        .group_by(FeedbackAnalysis.action_status)
        .all()
    )

    # Severity distribution
    severities = db.query(FeedbackAnalysis.severity).filter(
        FeedbackAnalysis.severity.isnot(None)
    ).all()

    # Severity trend for problem feedback (recent 30 days by analyzed_at)
    from sqlalchemy import text
    sev_trend = db.execute(
        text(
            """SELECT DATE(fa.analyzed_at) as d, AVG(fa.severity) as avg_sev
               FROM feedback_analyses fa
               WHERE fa.feedback_type = 'problem_feedback'
                 AND fa.analyzed_at >= DATE('now', '-30 days')
                 AND fa.severity IS NOT NULL
               GROUP BY d ORDER BY d"""
        )
    ).fetchall()

    neg_ratio = (negative / total * 100) if total > 0 else 0.0

    return {
        "total": total,
        "negative": negative,
        "high_severity": high_severity,
        "needs_review": needs_review,
        "today_new": today_new,
        "neg_ratio": round(neg_ratio, 1),
        "problem_count": problem_count,
        "experience_count": experience_count,
        "high_priority": high_priority,
        "resolved_count": resolved_count,
        "pending_action": pending_action,
        "positive_count": positive_count,
        "suggestion_count": suggestion_count,
        "feature_request_count": feature_request_count,
        "platforms": [{"name": p, "count": c} for p, c in platform_counts],
        "categories": [{"name": c, "count": cnt} for c, cnt in category_counts if c and c != "none"],
        "type_distribution": [{"name": t, "count": cnt} for t, cnt in type_counts],
        "action_statuses": [{"name": s, "count": cnt} for s, cnt in action_status_counts],
        "severities": [s[0] for s in severities if s[0] is not None],
        "severity_trend": [{"date": r[0], "avg_severity": round(r[1], 1) if r[1] else 0} for r in sev_trend],
    }


def get_timeline(db: Session, days: int = 30) -> list[dict]:
    """Get feedback timeline for charts."""
    from sqlalchemy import text

    result = db.execute(
        text(
            """SELECT DATE(created_at) as d, COUNT(*) as cnt
               FROM feedback_items
               WHERE created_at >= DATE('now', :days)
               GROUP BY d ORDER BY d"""
        ),
        {"days": f"-{days} days"},
    )
    return [{"date": r[0], "count": r[1]} for r in result]


def search_items(db: Session, filters: dict | None = None,
                 limit: int = 100, offset: int = 0) -> tuple[list, int]:
    """Search and filter feedback items. Returns (items, total_count)."""
    query = db.query(FeedbackItem).outerjoin(
        FeedbackAnalysis, FeedbackAnalysis.feedback_item_id == FeedbackItem.id
    )

    if filters:
        if filters.get("platform"):
            query = query.filter(FeedbackItem.platform == filters["platform"])
        if filters.get("brand"):
            query = query.filter(FeedbackItem.brand == filters["brand"])
        if filters.get("product"):
            query = query.filter(FeedbackItem.product == filters["product"])
        if filters.get("keyword"):
            kw = f"%{filters['keyword']}%"
            query = query.filter(FeedbackItem.content.like(kw))
        if filters.get("feedback_type"):
            query = query.filter(FeedbackAnalysis.feedback_type == filters["feedback_type"])
        if filters.get("sentiment"):
            query = query.filter(FeedbackAnalysis.sentiment == filters["sentiment"])
        if filters.get("is_negative") is not None:
            query = query.filter(FeedbackAnalysis.is_negative == filters["is_negative"])
        if filters.get("complaint_category"):
            query = query.filter(
                FeedbackAnalysis.complaint_category == filters["complaint_category"]
            )
        if filters.get("severity_min") is not None:
            query = query.filter(FeedbackAnalysis.severity >= filters["severity_min"])
        if filters.get("severity_max") is not None:
            query = query.filter(FeedbackAnalysis.severity <= filters["severity_max"])
        if filters.get("needs_human_review") is not None:
            query = query.filter(
                FeedbackAnalysis.needs_human_review == filters["needs_human_review"]
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
        if filters.get("analysis_status"):
            query = query.filter(FeedbackItem.analysis_status == filters["analysis_status"])
        if filters.get("date_from"):
            query = query.filter(FeedbackItem.created_at >= filters["date_from"])
        if filters.get("date_to"):
            query = query.filter(FeedbackItem.created_at <= filters["date_to"])

    total = query.count()
    items = query.order_by(FeedbackItem.created_at.desc()).offset(offset).limit(limit).all()

    return items, total


def get_item_detail(db: Session, item_id: int) -> FeedbackItem | None:
    """Get a single feedback item with analysis and review."""
    return db.query(FeedbackItem).filter(FeedbackItem.id == item_id).first()


def get_platforms(db: Session) -> list[str]:
    """Get distinct platform names."""
    results = db.query(FeedbackItem.platform).distinct().all()
    return [r[0] for r in results]


def save_human_review(db: Session, item_id: int, review_data: dict) -> HumanReview | None:
    """Save or update a human review. Returns the review object."""
    existing = db.query(HumanReview).filter(
        HumanReview.feedback_item_id == item_id
    ).first()

    if existing:
        for key, value in review_data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        db.commit()
        return existing
    else:
        review = HumanReview(feedback_item_id=item_id, **review_data)
        db.add(review)
        db.commit()
        return review


# ── Label helpers for display ────────────────────────────────────

FEEDBACK_TYPE_LABELS = {
    "problem_feedback": "问题反馈",
    "experience_feedback": "体验反馈",
    "unknown": "未知",
}

ACTION_PRIORITY_LABELS = {
    "low": "低",
    "medium": "中",
    "high": "高",
    "critical": "紧急",
}

ACTION_STATUS_LABELS = {
    "new": "待处理",
    "reviewing": "复核中",
    "processing": "处理中",
    "resolved": "已解决",
    "ignored": "已忽略",
}

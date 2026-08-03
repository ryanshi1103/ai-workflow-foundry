"""Human review page — correct AI results, add notes, preserve audit trail."""

from datetime import UTC, datetime

import streamlit as st
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import HumanReview
from src.repositories.feedback_repo import (
    ACTION_PRIORITY_LABELS,
    ACTION_STATUS_LABELS,
    FEEDBACK_TYPE_LABELS,
    get_item_detail,
    save_human_review,
)
from src.schemas import ActionPriority, ActionStatus, ComplaintCategory, FeedbackType, Sentiment


def show():
    st.title("👤 人工复核")

    db: Session = SessionLocal()
    try:
        # Select items needing review
        from src.models import FeedbackAnalysis, FeedbackItem

        review_items = (
            db.query(FeedbackItem)
            .join(FeedbackAnalysis, FeedbackAnalysis.feedback_item_id == FeedbackItem.id)
            .filter(FeedbackAnalysis.needs_human_review == True)  # noqa: E712
            .all()
        )

        if not review_items:
            # Also show items with pending reviews
            reviewed_ids = (
                db.query(HumanReview.feedback_item_id)
                .filter(HumanReview.review_status == "completed")
                .all()
            )
            reviewed_set = {r[0] for r in reviewed_ids}

            all_analyzed = (
                db.query(FeedbackItem)
                .join(FeedbackAnalysis, FeedbackAnalysis.feedback_item_id == FeedbackItem.id)
                .filter(FeedbackItem.analysis_status == "completed")
                .all()
            )

            review_items = [i for i in all_analyzed if i.id not in reviewed_set]

        if not review_items:
            st.info("没有需要复核的数据。分析完成后，需要人工复核的项目会出现在这里。")
            return

        st.markdown(f"共 **{len(review_items)}** 条待复核")

        # Item selector
        options = {f"#{item.id}: {item.content[:60]}...": item.id for item in review_items}
        selected_label = st.selectbox("选择要复核的数据", list(options.keys()))
        item_id = options[selected_label]

        item = get_item_detail(db, item_id)
        if not item or not item.analysis:
            st.error("无法加载数据")
            return

        review = item.human_review

        # ── Display original and AI analysis ───────────────────
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("原始数据")
            st.markdown(f"**平台:** {item.platform}")
            st.markdown(f"**作者:** {item.author_display_name}")
            st.text_area("原文", item.content, height=150, disabled=True, key="orig_content")

        with col2:
            st.subheader("AI 分析结果")
            analysis = item.analysis
            fb_label = FEEDBACK_TYPE_LABELS.get(analysis.feedback_type, analysis.feedback_type)
            st.markdown(f"**反馈类型:** {fb_label}")
            st.markdown(f"**情绪:** {analysis.sentiment} (分数: {analysis.sentiment_score})")
            st.markdown(f"**分类:** {analysis.complaint_category} / {analysis.complaint_subcategory}")
            st.markdown(f"**严重度:** {analysis.severity}/100")
            st.markdown(f"**置信度:** {analysis.confidence}")
            st.markdown(f"**需要处理:** {'是' if analysis.requires_action else '否'}")
            if analysis.action_priority:
                ap_label = ACTION_PRIORITY_LABELS.get(analysis.action_priority, analysis.action_priority)
                st.markdown(f"**处理优先级:** {ap_label}")
            if analysis.action_status:
                as_label = ACTION_STATUS_LABELS.get(analysis.action_status, analysis.action_status)
                st.markdown(f"**处理状态:** {as_label}")
            st.markdown(f"**摘要:** {analysis.summary}")
            st.markdown(f"**证据:** {analysis.evidence}")
            st.markdown(f"**建议:** {analysis.suggested_action}")

        st.markdown("---")
        st.subheader("人工复核")

        # ── Review form ────────────────────────────────────────
        col1, col2 = st.columns(2)

        with col1:
            corrected_feedback_type = st.selectbox(
                "修正反馈类型",
                ["保持 AI 判断"] + [ft.value for ft in FeedbackType],
                format_func=lambda x: FEEDBACK_TYPE_LABELS.get(x, x) if x != "保持 AI 判断" else x,
                key="corr_feedback_type",
            )
        with col2:
            corrected_sentiment = st.selectbox(
                "修正情绪",
                ["保持 AI 判断"] + [s.value for s in Sentiment],
                key="corr_sentiment",
            )

        col1, col2 = st.columns(2)
        with col1:
            corrected_category = st.selectbox(
                "修正分类",
                ["保持 AI 判断"] + [c.value for c in ComplaintCategory],
                key="corr_category",
            )
        with col2:
            corrected_severity = st.slider(
                "修正严重度",
                0,
                100,
                analysis.severity or 0,
                key="corr_severity",
            )

        col1, col2 = st.columns(2)
        with col1:
            corrected_requires_action = st.selectbox(
                "是否需要处理",
                ["保持 AI 判断", "是", "否"],
                key="corr_requires_action",
            )
            corrected_action_priority = st.selectbox(
                "修正处理优先级",
                ["保持 AI 判断"] + [ap.value for ap in ActionPriority],
                format_func=lambda x: ACTION_PRIORITY_LABELS.get(x, x) if x != "保持 AI 判断" else x,
                key="corr_action_priority",
            )
        with col2:
            corrected_action_status = st.selectbox(
                "修正处理状态",
                ["保持 AI 判断"] + [as_.value for as_ in ActionStatus],
                format_func=lambda x: ACTION_STATUS_LABELS.get(x, x) if x != "保持 AI 判断" else x,
                key="corr_action_status",
            )

        is_misjudged = st.checkbox("标记为 AI 误判", key="is_misjudged")

        review_notes = st.text_area(
            "复核备注",
            value=review.review_notes if review and review.review_notes else "",
            height=100,
            placeholder="输入复核备注...",
            key="review_notes",
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ 确认处理完成", type="primary"):
                review_data = {
                    "reviewed_by": "human",
                    "review_notes": review_notes,
                    "is_misjudged": is_misjudged,
                    "review_status": "completed",
                    "reviewed_at": datetime.now(UTC),
                }
                if corrected_feedback_type != "保持 AI 判断":
                    review_data["corrected_feedback_type"] = corrected_feedback_type
                if corrected_sentiment != "保持 AI 判断":
                    review_data["corrected_sentiment"] = corrected_sentiment
                if corrected_category != "保持 AI 判断":
                    review_data["corrected_category"] = corrected_category
                review_data["corrected_severity"] = corrected_severity
                if corrected_requires_action != "保持 AI 判断":
                    review_data["corrected_requires_action"] = (corrected_requires_action == "是")
                if corrected_action_priority != "保持 AI 判断":
                    review_data["corrected_action_priority"] = corrected_action_priority
                if corrected_action_status != "保持 AI 判断":
                    review_data["corrected_action_status"] = corrected_action_status

                save_human_review(db, item_id, review_data)
                st.success("复核完成！记录已保存。")
                st.rerun()

        with col2:
            if st.button("💾 保存草稿"):
                review_data = {
                    "reviewed_by": "human",
                    "review_notes": review_notes,
                    "is_misjudged": is_misjudged,
                    "review_status": "draft",
                }
                if corrected_feedback_type != "保持 AI 判断":
                    review_data["corrected_feedback_type"] = corrected_feedback_type
                if corrected_sentiment != "保持 AI 判断":
                    review_data["corrected_sentiment"] = corrected_sentiment
                if corrected_category != "保持 AI 判断":
                    review_data["corrected_category"] = corrected_category
                review_data["corrected_severity"] = corrected_severity
                if corrected_requires_action != "保持 AI 判断":
                    review_data["corrected_requires_action"] = (corrected_requires_action == "是")
                if corrected_action_priority != "保持 AI 判断":
                    review_data["corrected_action_priority"] = corrected_action_priority
                if corrected_action_status != "保持 AI 判断":
                    review_data["corrected_action_status"] = corrected_action_status

                save_human_review(db, item_id, review_data)
                st.success("草稿已保存！")
                st.rerun()

        # ── Show existing review ───────────────────────────────
        if review:
            st.markdown("---")
            st.subheader("历史复核记录")
            st.markdown(f"**状态:** {review.review_status}")
            st.markdown(f"**误判标记:** {'是' if review.is_misjudged else '否'}")
            if review.corrected_feedback_type:
                fb_label = FEEDBACK_TYPE_LABELS.get(review.corrected_feedback_type, review.corrected_feedback_type)
                st.markdown(f"**修正反馈类型:** {fb_label}")
            if review.corrected_sentiment:
                st.markdown(f"**修正情绪:** {review.corrected_sentiment}")
            if review.corrected_category:
                st.markdown(f"**修正分类:** {review.corrected_category}")
            if review.corrected_severity is not None:
                st.markdown(f"**修正严重度:** {review.corrected_severity}")
            if review.corrected_requires_action is not None:
                st.markdown(f"**修正需要处理:** {'是' if review.corrected_requires_action else '否'}")
            if review.corrected_action_priority:
                ap_label = ACTION_PRIORITY_LABELS.get(
                    review.corrected_action_priority, review.corrected_action_priority
                )
                st.markdown(f"**修正处理优先级:** {ap_label}")
            if review.corrected_action_status:
                as_label = ACTION_STATUS_LABELS.get(
                    review.corrected_action_status, review.corrected_action_status
                )
                st.markdown(f"**修正处理状态:** {as_label}")
            if review.review_notes:
                st.markdown(f"**备注:** {review.review_notes}")
            if review.reviewed_at:
                st.markdown(f"**复核时间:** {review.reviewed_at}")

    finally:
        db.close()

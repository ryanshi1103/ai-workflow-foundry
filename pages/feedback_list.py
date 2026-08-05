"""Feedback list page — filter, search, view details, and export."""


import streamlit as st
from sqlalchemy.orm import Session

from feedback_intelligence.database import SessionLocal
from feedback_intelligence.repositories.feedback_repo import (
    ACTION_PRIORITY_LABELS,
    ACTION_STATUS_LABELS,
    FEEDBACK_TYPE_LABELS,
    get_platforms,
    search_items,
)
from feedback_intelligence.schemas import ComplaintCategory, FeedbackType, Sentiment
from feedback_intelligence.services.export_service import export_csv, export_json_str


def show():
    st.title("📋 反馈列表")

    db: Session = SessionLocal()
    try:
        # ── Filters ────────────────────────────────────────────
        st.subheader("筛选条件")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            platforms = get_platforms(db)
            platform_filter = st.selectbox("平台", ["全部"] + platforms)
        with col2:
            feedback_type_options = ["全部"] + [ft.value for ft in FeedbackType]
            feedback_type_filter = st.selectbox(
                "反馈类型",
                feedback_type_options,
                format_func=lambda x: FEEDBACK_TYPE_LABELS.get(x, x) if x != "全部" else "全部",
            )
        with col3:
            sentiment_filter = st.selectbox(
                "情绪", ["全部"] + [s.value for s in Sentiment]
            )
        with col4:
            is_neg_filter = st.selectbox("是否负面", ["全部", "是", "否"])

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            category_filter = st.selectbox(
                "投诉类别", ["全部"] + [c.value for c in ComplaintCategory]
            )
        with col2:
            requires_action_filter = st.selectbox("需要处理", ["全部", "是", "否"])
        with col3:
            action_priority_filter = st.selectbox(
                "处理优先级",
                ["全部", "low", "medium", "high", "critical"],
                format_func=lambda x: ACTION_PRIORITY_LABELS.get(x, x) if x != "全部" else "全部",
            )
        with col4:
            action_status_filter = st.selectbox(
                "处理状态",
                ["全部", "new", "reviewing", "processing", "resolved", "ignored"],
                format_func=lambda x: ACTION_STATUS_LABELS.get(x, x) if x != "全部" else "全部",
            )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            sev_min = st.slider("最低严重度", 0, 100, 0)
        with col2:
            sev_max = st.slider("最高严重度", 0, 100, 100)
        with col3:
            needs_human = st.selectbox("需人工复核", ["全部", "是", "否"])
        with col4:
            status_filter = st.selectbox(
                "分析状态", ["全部", "pending", "analyzing", "completed", "error"]
            )

        col1, col2 = st.columns(2)
        with col1:
            keyword = st.text_input("关键词搜索", placeholder="输入内容关键词...")
        with col2:
            brand_filter = st.text_input("品牌", placeholder="输入品牌名称...")

        # ── Build filters ──────────────────────────────────────
        filters = {}
        if platform_filter != "全部":
            filters["platform"] = platform_filter
        if feedback_type_filter != "全部":
            filters["feedback_type"] = feedback_type_filter
        if sentiment_filter != "全部":
            filters["sentiment"] = sentiment_filter
        if is_neg_filter == "是":
            filters["is_negative"] = True
        elif is_neg_filter == "否":
            filters["is_negative"] = False
        if status_filter != "全部":
            filters["analysis_status"] = status_filter
        if category_filter != "全部":
            filters["complaint_category"] = category_filter
        if requires_action_filter == "是":
            filters["requires_action"] = True
        elif requires_action_filter == "否":
            filters["requires_action"] = False
        if action_priority_filter != "全部":
            filters["action_priority"] = action_priority_filter
        if action_status_filter != "全部":
            filters["action_status"] = action_status_filter
        if sev_min > 0:
            filters["severity_min"] = sev_min
        if sev_max < 100:
            filters["severity_max"] = sev_max
        if needs_human == "是":
            filters["needs_human_review"] = True
        elif needs_human == "否":
            filters["needs_human_review"] = False
        if keyword:
            filters["keyword"] = keyword
        if brand_filter:
            filters["brand"] = brand_filter

        items, total = search_items(db, filters)

        st.markdown(f"共 **{total}** 条记录")

        # ── Export ─────────────────────────────────────────────
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("📥 导出 CSV"):
                csv_data = export_csv(db, filters=filters)
                st.download_button(
                    "下载 CSV",
                    csv_data,
                    "feedback_export.csv",
                    "text/csv",
                    key="dl_csv",
                )
        with col2:
            if st.button("📥 导出 JSON"):
                json_data = export_json_str(db, filters=filters)
                st.download_button(
                    "下载 JSON",
                    json_data,
                    "feedback_export.json",
                    "application/json",
                    key="dl_json",
                )

        # ── Item list ──────────────────────────────────────────
        st.markdown("---")

        if not items:
            st.info("没有找到匹配的记录。请先导入数据。")
            return

        for item in items:
            _render_item_card(item)

    finally:
        db.close()


def _render_item_card(item):
    """Render a single feedback item card."""
    analysis = item.analysis

    # Determine border color based on feedback type
    if analysis:
        if analysis.feedback_type == "problem_feedback":
            border = "#ff4b4b" if analysis.action_priority in ("high", "critical") else "#ff9800"
        elif analysis.feedback_type == "experience_feedback":
            border = "#4caf50" if analysis.sentiment == "positive" else "#2196f3"
        else:
            border = "#cccccc"
    else:
        border = "#cccccc"

    with st.container():
        st.markdown(
            f'<div style="border-left: 4px solid {border}; padding-left: 12px; margin-bottom: 12px;">',
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            # Show feedback type label
            if analysis and analysis.feedback_type != "unknown":
                fb_type_label = FEEDBACK_TYPE_LABELS.get(analysis.feedback_type, analysis.feedback_type)
                st.markdown(f"**#{item.id}** | {item.platform} | 🏷️ {fb_type_label}")
            else:
                st.markdown(f"**#{item.id}** | {item.platform}")
            st.markdown(item.content[:200] + ("..." if len(item.content) > 200 else ""))
        with col2:
            if analysis:
                st.caption(f"情绪: {analysis.sentiment}")
                st.caption(f"严重度: {analysis.severity}")
                if analysis.feedback_type == "problem_feedback":
                    priority_label = ACTION_PRIORITY_LABELS.get(
                        analysis.action_priority, analysis.action_priority or "-"
                    )
                    status_label = ACTION_STATUS_LABELS.get(
                        analysis.action_status, analysis.action_status
                    )
                    st.caption(f"优先级: {priority_label}")
                    st.caption(f"状态: {status_label}")
                elif analysis.feedback_type == "experience_feedback":
                    st.caption(f"摘要: {(analysis.summary or '')[:40]}")
        with col3:
            st.caption(f"分析: {item.analysis_status}")
            if analysis and analysis.needs_human_review:
                st.warning("⚠️ 需复核")
            if analysis and analysis.feedback_type == "problem_feedback" and analysis.requires_action:
                if analysis.action_status == "new":
                    st.error("🔴 待处理")
                elif analysis.action_status == "resolved":
                    st.success("✅ 已解决")

        # Expandable detail
        with st.expander("查看详情"):
            _show_detail(item, analysis)

        st.markdown("</div>", unsafe_allow_html=True)


def _show_detail(item, analysis):
    """Show detailed view of a feedback item."""
    tab1, tab2, tab3 = st.tabs(["📝 原始数据", "🤖 AI 分析", "📋 原始 JSON"])

    with tab1:
        st.markdown(f"**平台:** {item.platform}")
        st.markdown(f"**来源类型:** {item.source_type}")
        if item.source_url:
            st.markdown(f"**链接:** {item.source_url}")
        if item.external_id:
            st.markdown(f"**外部 ID:** {item.external_id}")
        if item.author_display_name:
            st.markdown(f"**作者:** {item.author_display_name}")
        if item.language:
            st.markdown(f"**语言:** {item.language}")
        if item.published_at:
            st.markdown(f"**发布时间:** {item.published_at}")
        st.markdown(f"**采集时间:** {item.collected_at}")
        st.markdown("**原文:**")
        st.text_area("原文内容", item.content, height=150, disabled=True, key=f"content_{item.id}")

    with tab2:
        if analysis:
            st.markdown(f"**是否相关:** {'是' if analysis.is_relevant else '否'}")
            fb_type_label = FEEDBACK_TYPE_LABELS.get(analysis.feedback_type, analysis.feedback_type)
            st.markdown(f"**反馈类型:** {fb_type_label}")
            st.markdown(f"**情绪:** {analysis.sentiment}")
            st.markdown(f"**情绪分数:** {analysis.sentiment_score}")
            st.markdown(f"**是否负面:** {'是' if analysis.is_negative else '否'}")
            st.markdown(f"**投诉类别:** {analysis.complaint_category}")
            st.markdown(f"**投诉子类:** {analysis.complaint_subcategory}")
            st.markdown(f"**投诉对象:** {analysis.target}")
            st.markdown(f"**严重程度:** {analysis.severity}/100")
            st.markdown(f"**紧急度:** {analysis.urgency}")
            st.markdown(f"**置信度:** {analysis.confidence}")
            st.markdown(f"**需要处理:** {'是' if analysis.requires_action else '否'}")
            if analysis.action_priority:
                priority_label = ACTION_PRIORITY_LABELS.get(analysis.action_priority, analysis.action_priority)
                st.markdown(f"**处理优先级:** {priority_label}")
            if analysis.action_status:
                status_label = ACTION_STATUS_LABELS.get(analysis.action_status, analysis.action_status)
                st.markdown(f"**处理状态:** {status_label}")
            st.markdown(f"**摘要:** {analysis.summary}")
            st.markdown(f"**证据:** {analysis.evidence}")
            st.markdown(f"**建议行动:** {analysis.suggested_action}")
            st.markdown(f"**模型:** {analysis.model_name}")
            st.markdown(f"**提示词版本:** {analysis.prompt_version}")
            st.markdown(f"**分析时间:** {analysis.analyzed_at}")
            if analysis.needs_human_review:
                st.warning("⚠️ 需要人工复核")
        else:
            st.info("尚未分析")

    with tab3:
        raw = {
            "item": {
                "id": item.id,
                "platform": item.platform,
                "content": item.content,
                "source_url": item.source_url,
                "author_display_name": item.author_display_name,
                "language": item.language,
                "brand": item.brand,
                "product": item.product,
            },
            "analysis": None if not analysis else {
                "is_relevant": analysis.is_relevant,
                "feedback_type": analysis.feedback_type,
                "sentiment": analysis.sentiment,
                "sentiment_score": analysis.sentiment_score,
                "is_negative": analysis.is_negative,
                "complaint_category": analysis.complaint_category,
                "severity": analysis.severity,
                "confidence": analysis.confidence,
                "requires_action": analysis.requires_action,
                "action_priority": analysis.action_priority,
                "action_status": analysis.action_status,
                "needs_human_review": analysis.needs_human_review,
            },
        }
        st.json(raw)

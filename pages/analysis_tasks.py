"""Analysis tasks page — run AI analysis on feedback items."""

import streamlit as st
from sqlalchemy.orm import Session

from feedback_intelligence.database import SessionLocal
from feedback_intelligence.services.analysis_service import reanalyze_items, run_analysis


def show():
    st.title("🤖 分析任务")

    db: Session = SessionLocal()
    try:
        from feedback_intelligence.models import FeedbackItem

        # Count pending
        pending_count = (
            db.query(FeedbackItem)
            .filter(FeedbackItem.analysis_status == "pending")
            .count()
        )
        completed_count = (
            db.query(FeedbackItem)
            .filter(FeedbackItem.analysis_status == "completed")
            .count()
        )
        error_count = (
            db.query(FeedbackItem)
            .filter(FeedbackItem.analysis_status == "error")
            .count()
        )
        total_count = db.query(FeedbackItem).count()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总计", total_count)
        with col2:
            st.metric("待分析", pending_count)
        with col3:
            st.metric("已完成", completed_count)
        with col4:
            st.metric("失败", error_count)

        st.markdown("---")

        # ── Analyze pending ────────────────────────────────────
        st.subheader("分析待处理数据")

        max_items = st.number_input(
            "最大处理条数",
            min_value=1,
            max_value=max(pending_count, 1),
            value=min(10, pending_count or 1),
            step=1,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 开始分析", type="primary", disabled=pending_count == 0):
                _run_pending_analysis(db, max_items)
        with col2:
            if st.button("🔄 重试失败项", disabled=error_count == 0):
                _retry_errors(db)

        st.markdown("---")

        # ── Re-analyze ─────────────────────────────────────────
        st.subheader("重新分析已处理数据")
        completed_items = (
            db.query(FeedbackItem.id, FeedbackItem.content)
            .filter(FeedbackItem.analysis_status == "completed")
            .limit(50)
            .all()
        )

        if completed_items:
            options = {f"#{item.id}: {item.content[:60]}...": item.id for item in completed_items}
            selected = st.multiselect("选择要重新分析的数据", list(options.keys()))

            if st.button("🔄 重新分析选中数据", disabled=not selected):
                ids = [options[s] for s in selected]
                with st.spinner(f"正在重新分析 {len(ids)} 条数据..."):
                    result = reanalyze_items(db, ids)
                st.success(f"重新分析完成 — 成功: {result['completed']}, 失败: {result['error']}")
        else:
            st.info("暂无已完成分析的数据")

    finally:
        db.close()


def _run_pending_analysis(db: Session, max_items: int):
    from feedback_intelligence.models import FeedbackItem

    items = (
        db.query(FeedbackItem.id)
        .filter(FeedbackItem.analysis_status == "pending")
        .limit(max_items)
        .all()
    )

    if not items:
        st.warning("没有待分析的数据。请先导入数据。")
        return

    ids = [item.id for item in items]

    progress_bar = st.progress(0)
    status_text = st.empty()

    def on_progress(completed: int, total: int):
        progress_bar.progress(completed / total if total else 0)
        status_text.text(f"分析进度: {completed}/{total}")

    with st.spinner(f"正在分析 {len(ids)} 条数据..."):
        result = run_analysis(db, ids, on_progress=on_progress)

    progress_bar.progress(1.0)
    status_text.text("分析完成!")
    st.success(f"分析完成 — 成功: {result['completed']}, 失败: {result['error']}, 总计: {result['total']}")


def _retry_errors(db: Session):
    from feedback_intelligence.models import FeedbackItem

    items = (
        db.query(FeedbackItem.id)
        .filter(FeedbackItem.analysis_status == "error")
        .all()
    )

    if not items:
        st.info("没有失败的项。")
        return

    ids = [item.id for item in items]
    # Reset to pending first
    for item_id in ids:
        db.query(FeedbackItem).filter(FeedbackItem.id == item_id).update(
            {"analysis_status": "pending"}
        )
    db.commit()

    progress_bar = st.progress(0)
    status_text = st.empty()

    def on_progress(completed: int, total: int):
        progress_bar.progress(completed / total if total else 0)
        status_text.text(f"重试进度: {completed}/{total}")

    with st.spinner(f"正在重试 {len(ids)} 条..."):
        result = run_analysis(db, ids, on_progress=on_progress)

    progress_bar.progress(1.0)
    status_text.text("重试完成!")
    st.success(f"重试完成 — 成功: {result['completed']}, 失败: {result['error']}")

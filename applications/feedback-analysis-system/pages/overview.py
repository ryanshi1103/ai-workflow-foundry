"""Overview dashboard page — feedback analysis system."""

import plotly.express as px
import streamlit as st
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import FeedbackAnalysis, FeedbackItem
from src.repositories.feedback_repo import (
    get_stats,
    get_timeline,
)


def show():
    st.title("📊 总览看板")
    st.markdown("反馈分析系统 — 统一收集、分析和处理公开反馈与用户评价")

    db: Session = SessionLocal()
    try:
        stats = get_stats(db)

        # ── Tabs for feedback types ──────────────────────────────
        tab1, tab2, tab3 = st.tabs(["⚠️ 问题反馈", "💬 体验反馈", "📋 全部反馈"])

        with tab1:
            _show_problem_feedback(stats)
        with tab2:
            _show_experience_feedback(stats, db)
        with tab3:
            _show_all_feedback(stats, db)

    finally:
        db.close()


def _show_problem_feedback(stats: dict):
    """Show problem feedback dashboard."""
    st.subheader("问题反馈概览")

    # KPI row
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("问题总数", stats["problem_count"])
    with col2:
        st.metric("待处理", stats["pending_action"])
    with col3:
        st.metric("高优先级", stats["high_priority"])
    with col4:
        st.metric("严重问题 (≥75)", stats["high_severity"])
    with col5:
        st.metric("待人工复核", stats["needs_review"])
    with col6:
        st.metric("已解决", stats["resolved_count"])

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("问题类别分布")
        if stats["categories"]:
            fig = px.bar(
                x=[c["name"] for c in stats["categories"]],
                y=[c["count"] for c in stats["categories"]],
                labels={"x": "类别", "y": "数量"},
            )
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无数据")

    with col2:
        st.subheader("处理状态分布")
        if stats["action_statuses"]:
            labels_map = {
                "new": "待处理", "reviewing": "复核中",
                "processing": "处理中", "resolved": "已解决",
                "ignored": "已忽略",
            }
            fig = px.pie(
                values=[s["count"] for s in stats["action_statuses"]],
                names=[labels_map.get(s["name"], s["name"]) for s in stats["action_statuses"]],
                hole=0.4,
            )
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无数据")

    # Severity trend
    st.subheader("严重程度趋势（近30天）")
    if stats["severity_trend"]:
        fig = px.line(
            x=[t["date"] for t in stats["severity_trend"]],
            y=[t["avg_severity"] for t in stats["severity_trend"]],
            labels={"x": "日期", "y": "平均严重程度"},
        )
        fig.add_hline(y=75, line_dash="dash", line_color="red", annotation_text="预警线")
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无趋势数据（需要先分析数据）")

    # Severity histogram
    st.subheader("严重程度分布")
    if stats["severities"]:
        fig = px.histogram(
            x=stats["severities"],
            nbins=20,
            range_x=[0, 100],
            labels={"x": "严重程度", "y": "数量"},
        )
        fig.add_vline(x=75, line_dash="dash", line_color="red", annotation_text="预警线")
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无数据")


def _show_experience_feedback(stats: dict, db: Session):
    """Show experience feedback dashboard."""
    st.subheader("体验反馈概览")

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("体验反馈总数", stats["experience_count"])
    with col2:
        st.metric("正面反馈", stats["positive_count"])
    with col3:
        st.metric("建议/需求", stats["suggestion_count"])
    with col4:
        st.metric("功能需求", stats["feature_request_count"])

    # Sentiment distribution for experience feedback
    st.subheader("情绪分布")

    sentiment_dist = (
        db.query(FeedbackAnalysis.sentiment, func.count(FeedbackAnalysis.id))
        .filter(FeedbackAnalysis.feedback_type == "experience_feedback")
        .group_by(FeedbackAnalysis.sentiment)
        .all()
    )

    if sentiment_dist:
        sentiment_labels = {
            "positive": "正面", "neutral": "中性", "mixed": "混合",
            "negative": "负面", "unknown": "未知",
        }
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(
                values=[c for _, c in sentiment_dist],
                names=[sentiment_labels.get(s, s) for s, _ in sentiment_dist],
                hole=0.4,
            )
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            # Platform distribution
            plat_dist = (
                db.query(FeedbackItem.platform, func.count(FeedbackItem.id))
                .join(FeedbackAnalysis, FeedbackAnalysis.feedback_item_id == FeedbackItem.id)
                .filter(FeedbackAnalysis.feedback_type == "experience_feedback")
                .group_by(FeedbackItem.platform)
                .all()
            )
            if plat_dist:
                fig = px.bar(
                    x=[p for p, _ in plat_dist],
                    y=[c for _, c in plat_dist],
                    labels={"x": "平台", "y": "数量"},
                )
                fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无平台数据")

    st.subheader("情绪趋势")
    timeline = get_timeline(db, days=30)
    if timeline:
        fig = px.line(
            x=[t["date"] for t in timeline],
            y=[t["count"] for t in timeline],
            labels={"x": "日期", "y": "新增数量"},
        )
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无数据")


def _show_all_feedback(stats: dict, db: Session):
    """Show all feedback overview."""
    # KPI row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("总数据量", stats["total"])
    with col2:
        st.metric("问题反馈", stats["problem_count"])
    with col3:
        st.metric("体验反馈", stats["experience_count"])
    with col4:
        st.metric("负面数量", stats["negative"])
    with col5:
        st.metric("负面比例", f"{stats['neg_ratio']}%")

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("反馈类型分布")
        if stats["type_distribution"]:
            type_labels = {
                "problem_feedback": "问题反馈",
                "experience_feedback": "体验反馈",
                "unknown": "未知",
            }
            fig = px.pie(
                values=[t["count"] for t in stats["type_distribution"]],
                names=[type_labels.get(t["name"], t["name"]) for t in stats["type_distribution"]],
                hole=0.4,
            )
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无数据")

    with col2:
        st.subheader("各平台数量")
        if stats["platforms"]:
            fig = px.pie(
                values=[p["count"] for p in stats["platforms"]],
                names=[p["name"] for p in stats["platforms"]],
                hole=0.4,
            )
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无数据")

    # Complaint category distribution
    st.subheader("投诉类别分布")
    if stats["categories"]:
        fig = px.bar(
            x=[c["name"] for c in stats["categories"]],
            y=[c["count"] for c in stats["categories"]],
            labels={"x": "类别", "y": "数量"},
        )
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无数据")

    # Severity histogram
    st.subheader("严重程度分布")
    if stats["severities"]:
        fig = px.histogram(
            x=stats["severities"],
            nbins=20,
            range_x=[0, 100],
            labels={"x": "严重程度", "y": "数量"},
        )
        fig.add_vline(x=75, line_dash="dash", line_color="red", annotation_text="预警线")
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无数据")

    # Timeline
    st.subheader("时间趋势（近30天）")
    timeline = get_timeline(db, days=30)
    if timeline:
        fig = px.line(
            x=[t["date"] for t in timeline],
            y=[t["count"] for t in timeline],
            labels={"x": "日期", "y": "新增数量"},
        )
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无数据")

"""Settings page — show configuration status."""

import streamlit as st

from src.config import (
    APIFY_CONFIGURED,
    APP_DB_URL,
    APP_MOCK_MODE,
    DEEPSEEK_BATCH_SIZE,
    DEEPSEEK_CONFIGURED,
    DEEPSEEK_MAX_CONCURRENCY,
    DEEPSEEK_MODEL,
    DEEPSEEK_TIMEOUT_SECONDS,
    SEVERITY_WARNING_THRESHOLD,
)


def show():
    st.title("⚙️ 设置")

    # ── API Configuration Status ──────────────────────────────
    st.subheader("API 配置状态")

    col1, col2, col3 = st.columns(3)
    with col1:
        if DEEPSEEK_CONFIGURED:
            st.success("✅ DeepSeek 已配置")
        else:
            st.warning("⚠️ DeepSeek 未配置")

    with col2:
        if APIFY_CONFIGURED:
            st.success("✅ Apify 已配置")
        else:
            st.warning("⚠️ Apify 未配置")

    with col3:
        if APP_MOCK_MODE:
            st.info("🔧 Mock 模式")
        else:
            st.success("✅ 真实模式")

    st.markdown("---")

    # ── Configuration details ─────────────────────────────────
    st.subheader("当前配置")

    settings_data = {
        "DeepSeek 模型": DEEPSEEK_MODEL,
        "Mock 模式": "是" if APP_MOCK_MODE else "否",
        "数据库路径": APP_DB_URL.replace("sqlite:///", ""),
        "每批数量": DEEPSEEK_BATCH_SIZE,
        "最大并发数": DEEPSEEK_MAX_CONCURRENCY,
        "请求超时 (秒)": DEEPSEEK_TIMEOUT_SECONDS,
        "严重度预警阈值": SEVERITY_WARNING_THRESHOLD,
    }

    for key, value in settings_data.items():
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"**{key}**")
        with col2:
            st.markdown(str(value))

    st.markdown("---")

    # ── Environment info ──────────────────────────────────────
    st.subheader("环境信息")

    st.info(
        """
    **反馈分析系统 v0.2.0**

    **API Key 配置方式:**
    - 复制 `.env.example` 为 `.env`
    - 填写 `DEEPSEEK_API_KEY=你的密钥`
    - 启动应用即可自动加载

    **安全提示:**
    - API Key 只能在环境变量中配置，不会显示在此页面
    - 默认仅监听 127.0.0.1，不暴露到网络
    - 日志不记录完整 API Key
    """
    )

    # ── Data management ───────────────────────────────────────
    st.subheader("数据管理")
    st.warning("⚠️ 以下操作不可逆，请谨慎使用。")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 清除分析缓存"):
            from src.services.deepseek_service import deepseek_service

            deepseek_service.clear_cache()
            st.success("分析缓存已清除")

    with col2:
        if st.button("🔍 检查数据库完整性"):
            from src.database import SessionLocal
            from src.models import FeedbackAnalysis, FeedbackItem

            db = SessionLocal()
            try:
                total = db.query(FeedbackItem).count()
                analyzed = db.query(FeedbackAnalysis).count()
                orphaned = (
                    db.query(FeedbackAnalysis)
                    .filter(
                        ~FeedbackAnalysis.feedback_item_id.in_(
                            db.query(FeedbackItem.id)
                        )
                    )
                    .count()
                )
                st.success(f"总条目: {total}, 分析记录: {analyzed}, 孤立记录: {orphaned}")
            finally:
                db.close()

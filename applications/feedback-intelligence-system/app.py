"""Social Negative Feedback Monitor — Main Streamlit Application."""

import logging
import sys
from pathlib import Path

import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from feedback_intelligence.config import APP_LOG_LEVEL, APP_MOCK_MODE, DEEPSEEK_CONFIGURED
from feedback_intelligence.database import init_db, run_migrations

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="反馈分析系统",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, APP_LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Init database ──────────────────────────────────────────────
init_db()
run_migrations()


def main():
    """Main entry point for the Streamlit app."""
    st.sidebar.title("🔍 反馈分析系统")
    st.sidebar.markdown("统一收集、分析和处理公开反馈与用户评价")
    st.sidebar.markdown("---")

    # Status indicators
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if DEEPSEEK_CONFIGURED:
            st.sidebar.success("DeepSeek ✓")
        else:
            st.sidebar.warning("DeepSeek ✗")
    with col2:
        if APP_MOCK_MODE:
            st.sidebar.info("Mock 模式")
        else:
            st.sidebar.success("真实模式")

    st.sidebar.markdown("---")

    # Navigation
    page = st.sidebar.radio(
        "导航",
        ["📊 总览", "📥 数据导入", "🤖 分析任务", "📋 反馈列表", "👤 人工复核", "⚙️ 设置"],
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("v0.2.0 | 本地运行 | 仅监听 127.0.0.1")

    # Route to pages
    page_map = {
        "📊 总览": "pages.overview",
        "📥 数据导入": "pages.import_data",
        "🤖 分析任务": "pages.analysis_tasks",
        "📋 反馈列表": "pages.feedback_list",
        "👤 人工复核": "pages.human_review",
        "⚙️ 设置": "pages.settings",
    }

    module_name = page_map.get(page, "pages.overview")
    try:
        mod = __import__(module_name, fromlist=["show"])
        mod.show()
    except Exception as e:
        st.error(f"页面加载失败: {e}")
        logger.exception("Failed to load page %s", module_name)


if __name__ == "__main__":
    main()

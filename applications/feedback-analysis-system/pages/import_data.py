"""Data import page — example data, CSV, JSON, and Apify connector."""

import json

import streamlit as st
from sqlalchemy.orm import Session

from src.config import APIFY_CONFIGURED, APP_MOCK_MODE
from src.database import SessionLocal
from src.schemas import ImportRow
from src.services.import_service import (
    ImportResult,
    import_csv_string,
    import_json_string,
    import_rows,
)


def show():
    st.title("📥 数据导入")

    tab1, tab2, tab3, tab4 = st.tabs(["📦 示例数据", "📄 CSV 上传", "📋 JSON 上传", "🤖 Apify 通用连接器"])

    with tab1:
        _show_example_data()

    with tab2:
        _show_csv_upload()

    with tab3:
        _show_json_upload()

    with tab4:
        _show_apify_connector()


def _show_example_data():
    st.subheader("初始化示例数据")
    st.markdown("导入 50 条虚构示例数据，覆盖问题反馈、体验反馈、正面/负面/中性/反讽/广告等多种场景。")

    st.info("⚠️ 所有示例数据均为虚构，不包含真实个人信息。")

    if st.button("🚀 导入示例数据", type="primary"):
        from src.connectors.mock_connector import MOCK_DATA

        db: Session = SessionLocal()
        try:
            rows = []
            for raw in MOCK_DATA:
                try:
                    row = ImportRow(
                        platform=raw["platform"],
                        content=raw["content"],
                        source_url=raw.get("source_url"),
                        external_id=raw.get("external_id"),
                        author_display_name=raw.get("author_display_name"),
                        language=raw.get("language"),
                        brand=raw.get("brand") or None,
                        product=raw.get("product") or None,
                        search_keyword=raw.get("search_keyword") or None,
                        source_type=raw.get("source_type", "mock"),
                    )
                    rows.append(row)
                except Exception:
                    pass

            result = import_rows(db, rows)
            _show_result(result)
        finally:
            db.close()


def _show_csv_upload():
    st.subheader("CSV 文件上传")
    st.markdown(
        """
    上传 CSV 文件。必填字段: `platform`, `content`。
    可选字段: `source_url`, `external_id`, `author_display_name`, `published_at`,
    `engagement_count`, `brand`, `product`, `search_keyword`, `language`。
    文件大小限制: 10 MB。
    """
    )

    uploaded = st.file_uploader("选择 CSV 文件", type=["csv"], key="csv_uploader")
    if uploaded is not None:
        if uploaded.size > 10 * 1024 * 1024:
            st.error("文件超过 10 MB 限制，请拆分后上传。")
            return

        csv_content = uploaded.read().decode("utf-8")
        lines = csv_content.split("\n")
        preview_lines = lines[:6]

        st.subheader("预览（前 5 行）")
        st.code("\n".join(preview_lines), language="csv")

        if st.button("📥 导入 CSV 数据", key="btn_csv_import"):
            db: Session = SessionLocal()
            try:
                result = import_csv_string(db, csv_content)
                _show_result(result)
            finally:
                db.close()


def _show_json_upload():
    st.subheader("JSON 文件上传")
    st.markdown(
        """
    上传 JSON 文件（对象数组或单个对象）。必填字段: `platform`, `content`。
    """
    )

    uploaded = st.file_uploader("选择 JSON 文件", type=["json"], key="json_uploader")
    if uploaded is not None:
        if uploaded.size > 10 * 1024 * 1024:
            st.error("文件超过 10 MB 限制。")
            return

        json_content = uploaded.read().decode("utf-8")
        try:
            data = json.loads(json_content)
            if isinstance(data, dict):
                data = [data]
            preview = data[:3]
            st.subheader("预览（前 3 条）")
            st.json(preview)
        except json.JSONDecodeError as e:
            st.error(f"JSON 格式错误: {e}")
            return

        if st.button("📥 导入 JSON 数据", key="btn_json_import"):
            db: Session = SessionLocal()
            try:
                result = import_json_string(db, json_content)
                _show_result(result)
            finally:
                db.close()


def _show_apify_connector():
    st.subheader("🤖 Apify 通用连接器")
    st.markdown("通过 Apify Actor 采集公开数据。需要配置 `APIFY_TOKEN` 和 `APIFY_ACTOR_ID`。")

    if not APIFY_CONFIGURED:
        st.warning("⚠️ Apify 未配置。请设置 APIFY_TOKEN 和 APIFY_ACTOR_ID 环境变量。")

    if APP_MOCK_MODE or not APIFY_CONFIGURED:
        st.info("🔧 当前为 Mock 模式，将使用模拟数据演示。")

    st.subheader("Actor 输入 JSON")
    actor_input_str = st.text_area(
        "输入 Actor 参数（JSON 格式）",
        value='{\n  "searchTerms": ["example"],\n  "maxItems": 10\n}',
        height=150,
        disabled=APP_MOCK_MODE or not APIFY_CONFIGURED,
    )

    if st.button("🚀 启动 Apify 采集", disabled=(not APP_MOCK_MODE and not APIFY_CONFIGURED)):
        try:
            actor_input = json.loads(actor_input_str)
        except json.JSONDecodeError as e:
            st.error(f"JSON 格式错误: {e}")
            return

        from src.connectors.apify_connector import ApifyConnector

        connector = ApifyConnector()
        with st.spinner("正在运行 Apify Actor..."):
            run_result = connector.run_actor(actor_input)

        st.subheader("运行结果")
        st.json({
            "status": run_result["status"],
            "total_count": run_result["total_count"],
            "success_count": run_result["success_count"],
            "error_count": run_result["error_count"],
            "errors": run_result["errors"],
        })

        if run_result["items"]:
            db: Session = SessionLocal()
            try:
                result = import_rows(db, run_result["items"])
                _show_result(result)
            finally:
                db.close()


def _show_result(result: ImportResult):
    st.subheader("导入结果")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("原始数量", result.total)
    with col2:
        st.metric("新增", result.new, delta=None)
    with col3:
        st.metric("重复", result.duplicates)
    with col4:
        st.metric("无效", result.invalid)
    with col5:
        st.metric("失败", result.errors)

    if result.error_details:
        st.warning("错误详情:")
        for err in result.error_details[:10]:
            st.caption(f"- {err}")
        if len(result.error_details) > 10:
            st.caption(f"... 还有 {len(result.error_details) - 10} 条错误")

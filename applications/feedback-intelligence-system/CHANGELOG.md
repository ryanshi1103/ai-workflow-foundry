# Changelog

## [0.1.0] — 2026-07-13

### Added (初版 MVP)

- **数据模型**: FeedbackItem, FeedbackAnalysis, HumanReview (SQLAlchemy + SQLite)
- **数据导入**: CSV 上传、JSON 上传、示例数据（35 条虚构数据）、Apify 通用连接器
- **内容去重**: 基于 SHA-256 的内容哈希，规范化后比较
- **DeepSeek 分析**: OpenAI 兼容 SDK 调用，Mock 模式，指数退避重试，缓存机制，JSON Schema 校验
- **情感分析**: 区分真实投诉、反讽、广告、新闻转述等 10 种场景
- **Streamlit 看板**: 6 个页面（总览、导入、分析、列表、人工复核、设置）
- **数据导出**: CSV（UTF-8-SIG）和 JSON
- **人工复核**: 保留审计记录，不覆盖 AI 原始结果
- **测试**: 68 个 pytest 测试覆盖哈希、去重、校验、Mock、数据库、导出、Apify 映射、安全
- **脚本**: setup.sh, run.sh, test.sh, reset_demo.sh
- **配置**: .env.example，所有密钥从环境变量读取

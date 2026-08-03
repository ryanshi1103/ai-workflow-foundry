<p align="center">
  <img src="branding/logo.svg" width="128" alt="Feedback Analysis System logo">
</p>

<h1 align="center">反馈分析系统</h1>
<p align="center">Feedback Analysis System</p>

## 项目作用

一个本地运行的反馈分析系统。导入公开帖子、评论和评价数据，调用 DeepSeek API 自动分类反馈类型（问题反馈/体验反馈），提取投诉对象、问题类别、严重程度和证据句，在 Streamlit 看板中查询、筛选、统计和导出结果。

## FlowFoundry AI 关系

本项目作为独立的客户反馈智能产品，被
[FlowFoundry AI](https://github.com/ryanshi1103/ai-workflow-foundry)
登记为参考应用。它展示“导入 → AI 候选 → 人工复核 → 审计保留 → 导出”的完整
工作流，但不虚构尚未实现的即插即用集成。

## 当前版本能力 (v0.2.0)

- ✅ 反馈二分类：问题反馈（需处理的问题）与体验反馈（感受/建议/表扬）
- ✅ 问题反馈包含处理优先级、处理状态跟踪
- ✅ 三种数据导入方式：示例数据、CSV/JSON 上传、Apify 通用连接器
- ✅ 基于 SHA-256 的内容去重，相同内容不会重复入库
- ✅ DeepSeek API 反馈分析（区分问题/体验、真实投诉、反讽、广告、新闻转述等）
- ✅ Mock 模式 — 无 API Key 也可完整演示
- ✅ 分析结果缓存，避免重复调用
- ✅ 指数退避重试、超时控制、并发限制
- ✅ SQLite 本地存储，无需外部数据库
- ✅ Streamlit 看板：总览、导入、分析、列表、人工复核、设置
- ✅ 数据导出为 CSV（UTF-8-SIG，Excel 兼容）和 JSON
- ✅ 人工复核保留审计记录，不覆盖 AI 原始结果
- ✅ 虚构示例数据 50 条，覆盖问题反馈/体验反馈/正面/负面/中性/反讽/广告

## 明确不支持

- ❌ 绕过登录验证、验证码、付费墙、访问控制
- ❌ 抓取私信、私密账号、非公开个人信息
- ❌ 代理池、反检测、Cookie 窃取等隐蔽功能
- ❌ 公网暴露（默认仅监听 127.0.0.1）
- ❌ 实时自动爬取（需通过 Apify 连接器手动触发）
- ❌ 多用户、权限管理、企业级部署
- ❌ 真实 Twitter/Reddit/YouTube/TikTok 适配器（本次仅做接口预留）

## Fedora 安装步骤

```bash
# 安装 Python 3.11+
sudo dnf install python3.11 python3.11-devel

# 进入项目
cd ~/Projects/feedback-analysis-system
```

## Python 虚拟环境

```bash
# 运行初始化脚本（自动创建 venv、安装依赖、复制 .env）
./scripts/setup.sh

# 或手动操作：
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## 环境变量配置

编辑 `.env` 文件：

```bash
# 必填（真实模式）
DEEPSEEK_API_KEY=sk-your-key-here

# 可选
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_MAX_CONCURRENCY=3
DEEPSEEK_TIMEOUT_SECONDS=60
DEEPSEEK_BATCH_SIZE=10

# Apify（可选）
APIFY_TOKEN=your-apify-token
APIFY_ACTOR_ID=your-actor-id
APIFY_MAX_ITEMS=100

# 应用设置
APP_MOCK_MODE=true          # Mock 模式，无需 API Key
APP_DB_URL=sqlite:///data/social_monitor.db
APP_LOG_LEVEL=INFO
```

## Mock 演示步骤（无需 API Key）

```bash
# 1. 安装依赖
./scripts/setup.sh

# 2. 确保 .env 中 APP_MOCK_MODE=true（默认就是）
# 3. 启动应用
./scripts/run.sh

# 4. 打开浏览器访问 http://127.0.0.1:8501
# 5. 进入「数据导入」→「示例数据」→ 点击导入
# 6. 进入「分析任务」→ 点击开始分析
# 7. 查看「总览」和「反馈列表」
```

## DeepSeek API 配置

```bash
# 1. 在 https://platform.deepseek.com 获取 API Key
# 2. 编辑 .env：
DEEPSEEK_API_KEY=sk-your-real-key
APP_MOCK_MODE=false

# 3. 重启应用
```

**重要：** 分析结果会根据真实 API 返回。Mock 模式的分析结果是基于内容关键词的规则匹配，仅供演示。

## Apify 配置

```bash
# 1. 在 https://console.apify.com 获取 API Token
# 2. 选择要使用的 Actor，获取其 Actor ID
# 3. 编辑 .env：
APIFY_TOKEN=your-token
APIFY_ACTOR_ID=your-actor-id

# 4. 配置字段映射（编辑 config/field_mappings.example.yaml）
```

## 启动命令

```bash
# 启动 Streamlit 应用
./scripts/run.sh

# 或手动启动
source .venv/bin/activate
streamlit run app.py
```

访问 http://127.0.0.1:8501

## 测试命令

```bash
./scripts/test.sh

# 或手动测试
source .venv/bin/activate
ruff check src/ tests/ app.py pages/
pytest tests/ -v
```

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `ModuleNotFoundError: No module named 'src'` | 未从项目根目录运行 | `cd` 到项目根目录 |
| `No such file: .env` | 未创建 .env | `cp .env.example .env` |
| `API key not configured` | Mock 模式关闭且无 Key | 设置 `APP_MOCK_MODE=true` 或填入 Key |
| Streamlit 端口被占用 | 8501 端口已使用 | 修改 `.env` 中 `APP_PORT` |
| CSV 中文乱码 (Excel) | 用错了打开方式 | 导出文件使用 UTF-8-SIG，请用 Excel「数据」→「自文本/CSV」导入 |

## 数据和隐私边界

- **只处理**：公开内容、用户自行上传的数据、授权 API 获取的数据
- **不处理**：私信、私密账号、非公开个人信息
- **存储位置**：本地 SQLite 数据库（`data/social_monitor.db`）
- **API Key**：只从环境变量读取，不写入源码、日志或 Git
- **网络监听**：默认仅 127.0.0.1
- **外部数据**：所有外部数据视为不可信输入，进行长度限制和类型检查

## 后续增加新平台适配器

1. 在 `src/connectors/` 创建新文件（如 `twitter_connector.py`）
2. 继承 `BaseConnector`，实现 `fetch()` 方法
3. 在 `pages/import_data.py` 添加对应的导入标签页
4. 在 `config/field_mappings.example.yaml` 添加字段映射
5. 编写相应的测试文件

```python
# 示例：src/connectors/twitter_connector.py
from src.connectors.base import BaseConnector
from src.schemas import ImportRow

class TwitterConnector(BaseConnector):
    def fetch(self) -> list[ImportRow]:
        # 实现 Twitter API 数据获取
        # 返回 ImportRow 列表
        ...
```

## 目录结构

```
social-negative-monitor/
├── app.py                    # Streamlit 主入口
├── pages/                    # Streamlit 页面
│   ├── overview.py           # 总览看板
│   ├── import_data.py        # 数据导入
│   ├── analysis_tasks.py     # 分析任务
│   ├── feedback_list.py      # 反馈列表
│   ├── human_review.py       # 人工复核
│   └── settings.py           # 设置
├── src/
│   ├── config.py             # 配置管理
│   ├── database.py           # 数据库引擎和会话
│   ├── models.py             # SQLAlchemy ORM 模型
│   ├── schemas.py            # Pydantic 数据校验
│   ├── repositories/
│   │   └── feedback_repo.py  # 数据查询和统计
│   ├── services/
│   │   ├── deepseek_service.py   # DeepSeek API 服务
│   │   ├── analysis_service.py   # 分析编排
│   │   ├── import_service.py     # 数据导入
│   │   ├── dedup_service.py      # 内容去重
│   │   └── export_service.py     # 数据导出
│   ├── connectors/
│   │   ├── base.py           # 连接器基类
│   │   ├── csv_connector.py  # CSV 连接器
│   │   ├── json_connector.py # JSON 连接器
│   │   ├── apify_connector.py # Apify 通用连接器
│   │   └── mock_connector.py # 示例数据
│   └── prompts/
│       └── sentiment_v1.py   # 分析提示词 v1
├── config/
│   └── field_mappings.example.yaml
├── data/                     # 数据库存储目录
├── tests/                    # pytest 测试
├── scripts/
│   ├── setup.sh              # 初始化脚本
│   ├── run.sh                # 启动脚本
│   ├── test.sh               # 测试脚本
│   └── reset_demo.sh         # 重置演示数据
├── .env.example              # 环境变量模板
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── README.md
└── CHANGELOG.md
```

## License

本项目仅供学习和内部使用。使用 DeepSeek API 和 Apify 时请遵守相应服务条款。

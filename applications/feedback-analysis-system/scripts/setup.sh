#!/usr/bin/env bash
# Setup script — creates virtual environment and installs dependencies
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Social Negative Monitor — 项目初始化 ==="
echo "项目目录: $PROJECT_DIR"

# Check we're in the right project
if [ ! -f "$PROJECT_DIR/pyproject.toml" ]; then
    echo "错误: 未找到 pyproject.toml，请确认在项目根目录运行此脚本。"
    exit 1
fi

cd "$PROJECT_DIR"

# Create virtual environment
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo ">>> 创建 Python 虚拟环境..."
    python3 -m venv .venv
else
    echo ">>> 虚拟环境已存在，跳过创建。"
fi

# Activate and install
echo ">>> 激活虚拟环境..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo ">>> 升级 pip..."
pip install --upgrade pip -q

echo ">>> 安装依赖..."
pip install -e ".[dev]" -q

# Create .env if not exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo ">>> 创建 .env 文件（从 .env.example 复制）..."
    cp .env.example .env
    echo "    请编辑 .env 文件填入你的 API Key。"
else
    echo ">>> .env 文件已存在，跳过。"
fi

# Create data directory
mkdir -p "$PROJECT_DIR/data"

echo ""
echo "=== 初始化完成 ==="
echo ""
echo "下一步:"
echo "  1. 编辑 .env 文件（如需真实 API）"
echo "  2. source .venv/bin/activate"
echo "  3. ./scripts/run.sh"
echo "  4. 或 ./scripts/test.sh 运行测试"

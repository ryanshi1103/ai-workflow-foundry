#!/usr/bin/env bash
# Test script — runs ruff and pytest
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== 运行测试 ==="
echo "项目目录: $PROJECT_DIR"

cd "$PROJECT_DIR"

# Check virtual environment
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "错误: 未找到虚拟环境，请先运行 ./scripts/setup.sh"
    exit 1
fi

# Activate
# shellcheck disable=SC1091
source .venv/bin/activate

# Load .env if it exists (for test environment)
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/.env"
    set +a
fi

# Ensure mock mode for tests
export APP_MOCK_MODE=true
export APP_DB_URL=sqlite:///:memory:

echo ""
echo "=== 1/2: Ruff 代码检查 ==="
ruff check src/ tests/ app.py pages/ || {
    echo "⚠️  Ruff 检查发现问题，请修复后重试。"
    exit 1
}
echo "✓ Ruff 检查通过"

echo ""
echo "=== 2/2: Pytest 测试 ==="
python -m pytest tests/ -v --tb=short 2>&1 || {
    echo "⚠️  测试失败，请查看上方输出。"
    exit 1
}

echo ""
echo "=== 全部通过 ==="

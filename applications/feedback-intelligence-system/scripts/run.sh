#!/usr/bin/env bash
# Run script — starts the Streamlit application
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== 启动 Feedback Intelligence System ==="

cd "$PROJECT_DIR"

# Check virtual environment
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "错误: 未找到虚拟环境，请先运行 ./scripts/setup.sh"
    exit 1
fi

# Activate
# shellcheck disable=SC1091
source .venv/bin/activate

# Load .env if it exists
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/.env"
    set +a
fi

echo "启动 Streamlit，监听 http://127.0.0.1:8501"
echo "按 Ctrl+C 停止。"
echo ""

streamlit run app.py --server.address=127.0.0.1 --server.port=8501

#!/usr/bin/env bash
# Reset demo — delete database and re-initialize
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== 重置演示数据 ==="
echo "这将删除数据库中的所有数据。"
echo ""

cd "$PROJECT_DIR"

# Confirm
read -rp "确认重置？这将删除 data/*.db 文件。 [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消。"
    exit 0
fi

# Remove database files
echo ">>> 删除数据库文件..."
rm -f data/*.db data/*.db-wal data/*.db-shm

echo ">>> 数据库已重置。"
echo ""
echo "重新启动应用后，可以通过「数据导入 → 示例数据」重新初始化。"

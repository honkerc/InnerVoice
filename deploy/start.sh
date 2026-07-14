#!/bin/bash
# InnerVoice - 生产启动脚本
# 用法:
#   INNERVOICE_PORT=8080 bash deploy/start.sh          # 自定义端口
#   INNERVOICE_DATA_DIR=/data/innervoice bash deploy/start.sh  # 自定义数据目录

set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# 从环境变量读取配置（与 config.py 一致）
INNERVOICE_PORT="${INNERVOICE_PORT:-8001}"
INNERVOICE_DATA_DIR="${INNERVOICE_DATA_DIR:-$ROOT_DIR/backend/data}"

echo "=== InnerVoice 后端启动 ==="
echo "端口:       $INNERVOICE_PORT"
echo "数据目录:   $INNERVOICE_DATA_DIR"
echo ""

cd "$ROOT_DIR/backend"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# 安装依赖
pip install -r requirements.txt -q

# 启动 uvicorn（环境变量会自动传递给 config.py）
export INNERVOICE_PORT
export INNERVOICE_DATA_DIR

exec python -m uvicorn main:app \
    --host 127.0.0.1 \
    --port "$INNERVOICE_PORT" \
    --workers 2 \
    --log-level info

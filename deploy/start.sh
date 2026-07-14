#!/bin/bash
# 与神对话 - 生产启动脚本
# 用法: PORT=8080 bash deploy/start.sh

set -e

# 项目根目录
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# 后端端口（默认 8001）
PORT="${PORT:-8001}"

echo "=== 启动后端（端口 $PORT）==="
cd "$ROOT_DIR/backend"

# 如果虚拟环境存在则激活
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# 安装依赖
pip install -r requirements.txt -q

# 启动 uvicorn
exec python -m uvicorn main:app \
    --host 127.0.0.1 \
    --port "$PORT" \
    --workers 2 \
    --log-level info

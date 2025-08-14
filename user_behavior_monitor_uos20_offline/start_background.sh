#!/bin/bash
# 后台启动用户行为监控系统

cd "$(dirname "$0")"

echo "后台启动用户行为监控系统..."

# 激活虚拟环境
source venv/bin/activate

# 启动后台进程
python3 uos20_background_manager.py start

echo "后台进程已启动"
echo "查看状态: ./status_monitor.sh"
echo "查看日志: ./view_logs.sh"

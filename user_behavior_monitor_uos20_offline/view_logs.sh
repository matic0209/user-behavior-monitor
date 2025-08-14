#!/bin/bash
# 查看监控系统日志

cd "$(dirname "$0")"

echo "用户行为监控系统日志:"
echo "======================"

# 显示最近的日志
echo "最近的日志 (最后50行):"
python3 uos20_background_manager.py logs

echo ""
echo "实时跟踪日志 (Ctrl+C 退出):"
python3 uos20_background_manager.py follow

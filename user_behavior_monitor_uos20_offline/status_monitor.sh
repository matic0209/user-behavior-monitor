#!/bin/bash
# 查看监控系统状态

cd "$(dirname "$0")"

echo "用户行为监控系统状态:"
echo "========================"

# 检查后台进程状态
echo "后台进程状态:"
python3 uos20_background_manager.py status

echo ""

# 检查服务状态
echo "系统服务状态:"
sudo python3 uos20_service_manager.py status 2>/dev/null || echo "服务未安装"

echo ""

# 检查日志文件
echo "日志文件:"
ls -la logs/ 2>/dev/null || echo "日志目录不存在"

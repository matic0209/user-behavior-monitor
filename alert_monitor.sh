
#!/bin/bash
# 告警监控脚本 - 适用于system用户环境

ALERT_DIR="logs/alerts"
REALTIME_FILE="$ALERT_DIR/realtime_alerts.txt"
LOG_DIR="logs"

echo "🔍 启动告警监控..."
echo "监控目录: $ALERT_DIR"
echo "实时告警文件: $REALTIME_FILE"

# 监控实时告警文件
if [ -f "$REALTIME_FILE" ]; then
    echo "📋 最近的告警记录:"
    tail -10 "$REALTIME_FILE"
else
    echo "⚠️  实时告警文件不存在"
fi

# 监控告警目录
echo "📁 告警文件列表:"
if [ -d "$ALERT_DIR" ]; then
    ls -la "$ALERT_DIR"/*.txt 2>/dev/null || echo "暂无告警文件"
else
    echo "⚠️  告警目录不存在"
fi

# 监控日志文件
echo "📝 最近的日志记录:"
if [ -d "$LOG_DIR" ]; then
    find "$LOG_DIR" -name "*.log" -type f -exec tail -5 {} \; 2>/dev/null || echo "暂无日志文件"
else
    echo "⚠️  日志目录不存在"
fi

echo "✅ 告警监控完成"

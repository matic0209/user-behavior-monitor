#!/bin/bash
# 测试超快模式配置

echo "🚀 测试超快模式配置..."
echo "=========================================="

# 设置超快模式
export FAST_MODE=true
export ULTRA_FAST_MODE=true

echo "环境变量设置:"
echo "  FAST_MODE=$FAST_MODE"
echo "  ULTRA_FAST_MODE=$ULTRA_FAST_MODE"

# 加载公共函数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

echo ""
echo "超快模式配置结果:"
echo "  STARTUP_WAIT=$STARTUP_WAIT"
echo "  FEATURE_WAIT=$FEATURE_WAIT"
echo "  TRAINING_WAIT=$TRAINING_WAIT"
echo "  LOG_WAIT=$LOG_WAIT"
echo "  KEY_INTERVAL=$KEY_INTERVAL"
echo "  MOUSE_INTERVAL=$MOUSE_INTERVAL"

echo ""
echo "✅ 超快模式配置测试完成！"

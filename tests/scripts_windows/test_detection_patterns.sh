#!/bin/bash
# 测试我们的检测模式是否正确工作

echo "=== 测试训练完成检测模式 ==="

# 创建测试日志内容
TEST_LOG="/tmp/test_detection.log"
cat > "$TEST_LOG" << 'EOF'
2025-08-26 08:35:10,123 - INFO - [logger.py:83] - 开始自动数据采集
2025-08-26 08:35:15,456 - INFO - [logger.py:83] - 数据采集完成
2025-08-26 08:35:20,789 - INFO - [logger.py:83] - 开始特征处理
2025-08-26 08:35:25,012 - INFO - [logger.py:83] - 特征处理完成
2025-08-26 08:35:30,345 - INFO - [logger.py:83] - 开始模型训练
2025-08-26 08:35:35,678 - INFO - [logger.py:83] - [SUCCESS] 模型训练完成
2025-08-26 08:35:40,901 - INFO - [logger.py:83] - 开始自动异常检测
2025-08-26 08:35:45,234 - INFO - [logger.py:83] - 自动异常检测已启动
2025-08-26 08:35:50,567 - INFO - [logger.py:83] - UBM_MARK: PREDICT_START
2025-08-26 08:35:55,890 - INFO - [logger.py:83] - UBM_MARK: PREDICT_RUNNING batch=100
EOF

echo "测试日志文件: $TEST_LOG"
echo ""

# 测试我们的检测模式
TRAINING_PATTERNS="\[SUCCESS\].*模型训练完成|用户.*模型训练完成|模型训练完成|Training completed|Model training finished|开始自动异常检测|自动异常检测已启动"

echo "=== 测试训练完成检测 ==="
if grep -qiE "$TRAINING_PATTERNS" "$TEST_LOG" 2>/dev/null; then
    echo "✅ 训练完成检测: 成功"
    echo "匹配的行:"
    grep -iE "$TRAINING_PATTERNS" "$TEST_LOG" | sed 's/^/  /'
else
    echo "❌ 训练完成检测: 失败"
fi

echo ""
echo "=== 测试预测循环检测 ==="
PREDICTION_PATTERNS="UBM_MARK:\s*PREDICT_(INIT|START|RUNNING)|使用训练模型预测完成|预测结果[:：]"

if grep -qiE "$PREDICTION_PATTERNS" "$TEST_LOG" 2>/dev/null; then
    echo "✅ 预测循环检测: 成功"
    echo "匹配的行:"
    grep -iE "$PREDICTION_PATTERNS" "$TEST_LOG" | sed 's/^/  /'
else
    echo "❌ 预测循环检测: 失败"
fi

echo ""
echo "=== 模拟测试脚本逻辑 ==="

# 模拟我们的测试脚本逻辑
if grep -qiE "$TRAINING_PATTERNS" "$TEST_LOG" 2>/dev/null; then
    echo "🎯 测试脚本应该在这里检测到训练完成并终止程序"
    echo "   检测模式: $TRAINING_PATTERNS"
    echo "   检测结果: 匹配成功"
    echo ""
    echo "   应该执行: stop_ubm_immediately \$PID '训练完成或预测启动检测'"
    echo "   然后退出循环，不会进入预测阶段"
elif grep -qiE "$PREDICTION_PATTERNS" "$TEST_LOG" 2>/dev/null; then
    echo "⚠️  测试脚本会在这里检测到预测循环并终止程序"
    echo "   但这是备用方案，理想情况下应该在训练完成时就终止"
else
    echo "❌ 测试脚本不会检测到任何终止条件，可能会超时"
fi

# 清理测试文件
rm -f "$TEST_LOG"

echo ""
echo "=== 结论 ==="
echo "如果用户仍然看到预测循环，可能的原因:"
echo "1. 用户直接运行了EXE，没有通过测试脚本"
echo "2. 测试脚本的进程终止逻辑失败了"
echo "3. 应用程序的日志格式与我们的测试不同"
echo ""
echo "建议用户运行:"
echo "  bash tests/scripts_windows/debug_training_detection.sh <日志文件>"
echo "来诊断具体问题"

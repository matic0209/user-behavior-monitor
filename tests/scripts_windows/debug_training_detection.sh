#!/bin/bash
# 调试训练完成检测问题的脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

LOG_FILE="${1:-}"
if [[ -z "$LOG_FILE" ]]; then
    echo "用法: $0 <日志文件路径>"
    echo "例如: $0 /path/to/monitor_20250826_083729.log"
    exit 1
fi

if [[ ! -f "$LOG_FILE" ]]; then
    echo "[ERROR] 日志文件不存在: $LOG_FILE"
    exit 1
fi

echo "=== 调试训练完成检测 ==="
echo "日志文件: $LOG_FILE"
echo "文件大小: $(wc -l < "$LOG_FILE") 行"
echo ""

echo "=== 1. 检查我们寻找的训练完成模式 ==="
PATTERNS=(
    "\[SUCCESS\].*模型训练完成"
    "用户.*模型训练完成" 
    "模型训练完成"
    "Training completed"
    "Model training finished"
    "开始自动异常检测"
    "自动异常检测已启动"
)

FOUND_ANY=false
for pattern in "${PATTERNS[@]}"; do
    if grep -qiE "$pattern" "$LOG_FILE" 2>/dev/null; then
        COUNT=$(grep -ciE "$pattern" "$LOG_FILE" 2>/dev/null || echo "0")
        echo "[FOUND] $pattern ($COUNT 次)"
        FOUND_ANY=true
        
        # 显示匹配的具体行
        echo "  匹配行:"
        grep -iE "$pattern" "$LOG_FILE" | head -3 | sed 's/^/    /'
        echo ""
    else
        echo "[NOT FOUND] $pattern"
    fi
done

if [[ "$FOUND_ANY" == "false" ]]; then
    echo ""
    echo "❌ 没有找到任何训练完成模式！"
    echo ""
else
    echo ""
    echo "✅ 找到了训练完成模式！"
    echo ""
fi

echo "=== 2. 检查预测相关日志 ==="
PRED_PATTERNS=(
    "UBM_MARK:\s*PREDICT_(INIT|START|RUNNING)"
    "使用训练模型预测完成"
    "预测结果[:：]"
    "开始用户.*的连续预测"
    "UBM_MARK: PREDICT_START"
    "UBM_MARK: PREDICT_RUNNING"
)

for pattern in "${PRED_PATTERNS[@]}"; do
    if grep -qiE "$pattern" "$LOG_FILE" 2>/dev/null; then
        COUNT=$(grep -ciE "$pattern" "$LOG_FILE" 2>/dev/null || echo "0")
        echo "[FOUND] $pattern ($COUNT 次)"
        
        # 显示第一次出现的时间
        FIRST_LINE=$(grep -iE "$pattern" "$LOG_FILE" | head -1)
        echo "  首次出现: $FIRST_LINE"
        echo ""
    else
        echo "[NOT FOUND] $pattern"
    fi
done

echo "=== 3. 分析日志时间线 ==="
echo "训练相关事件:"
grep -iE "训练|training|model|模型" "$LOG_FILE" | tail -10 | sed 's/^/  /'
echo ""

echo "预测相关事件:"
grep -iE "predict|预测|PREDICT_" "$LOG_FILE" | head -5 | sed 's/^/  /'
echo ""

echo "=== 4. 检查工作流程日志 ==="
WORKFLOW_PATTERNS=(
    "步骤1: 自动数据采集"
    "步骤2: 自动特征处理"  
    "步骤3: 自动模型训练"
    "步骤4: 自动异常检测"
    "\[SUCCESS\] 数据采集完成"
    "\[SUCCESS\] 特征处理完成"
    "\[SUCCESS\] 模型训练完成"
)

for pattern in "${WORKFLOW_PATTERNS[@]}"; do
    if grep -qiE "$pattern" "$LOG_FILE" 2>/dev/null; then
        LINE=$(grep -iE "$pattern" "$LOG_FILE" | tail -1)
        echo "[FOUND] $LINE"
    else
        echo "[NOT FOUND] $pattern"
    fi
done

echo ""
echo "=== 5. 诊断结论 ==="

# 检查是否有训练完成但仍在预测
HAS_TRAINING_DONE=$(grep -ciE "\[SUCCESS\].*模型训练完成|用户.*模型训练完成|开始自动异常检测" "$LOG_FILE" 2>/dev/null || echo "0")
HAS_PREDICTION=$(grep -ciE "UBM_MARK: PREDICT_RUNNING" "$LOG_FILE" 2>/dev/null || echo "0")

if [[ $HAS_TRAINING_DONE -gt 0 ]] && [[ $HAS_PREDICTION -gt 0 ]]; then
    echo "❌ 问题确认: 训练已完成但预测循环仍在运行"
    echo "   - 训练完成事件: $HAS_TRAINING_DONE 次"
    echo "   - 预测循环事件: $HAS_PREDICTION 次"
    echo ""
    echo "💡 可能原因:"
    echo "   1. 测试脚本没有正确检测到训练完成"
    echo "   2. 测试脚本检测到了但进程终止失败"
    echo "   3. 用户直接运行了EXE而不是测试脚本"
    echo ""
    echo "🔧 建议解决方案:"
    echo "   1. 确认是通过测试脚本运行的，不是直接运行EXE"
    echo "   2. 检查测试脚本的终止逻辑是否生效"
    echo "   3. 尝试使用更激进的进程终止方法"
    
elif [[ $HAS_TRAINING_DONE -eq 0 ]] && [[ $HAS_PREDICTION -gt 0 ]]; then
    echo "❓ 异常情况: 没有训练完成日志但有预测循环"
    echo "   这可能表示:"
    echo "   1. 使用了已有的模型，跳过了训练阶段"
    echo "   2. 训练完成日志被过滤或没有记录"
    echo "   3. 应用程序直接从预测阶段开始"
    
elif [[ $HAS_TRAINING_DONE -gt 0 ]] && [[ $HAS_PREDICTION -eq 0 ]]; then
    echo "✅ 正常情况: 训练完成且没有预测循环"
    echo "   测试脚本可能工作正常"
    
else
    echo "❓ 未知情况: 既没有训练完成也没有预测循环日志"
    echo "   请检查日志文件是否完整"
fi

echo ""
echo "=== 6. 推荐的下一步操作 ==="
echo "1. 确认运行方式:"
echo "   bash tests/scripts_windows/TC03_deep_learning_classification.sh"
echo "   (不要直接运行 UserBehaviorMonitor.exe)"
echo ""
echo "2. 如果问题持续，尝试手动终止:"
echo "   taskkill /IM \"UserBehaviorMonitor.exe\" /F"
echo ""
echo "3. 检查进程状态:"
echo "   tasklist | findstr UserBehaviorMonitor"
echo ""

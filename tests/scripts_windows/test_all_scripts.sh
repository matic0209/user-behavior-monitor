#!/bin/bash
# 测试所有脚本的可用性

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

echo "🔍 测试所有脚本的可用性"
echo "=========================================="

# 测试用例列表
declare -a TEST_CASES=(
    "TC01:TC01_realtime_input_collection.sh:实时输入采集"
    "TC02:TC02_feature_extraction.sh:特征提取功能"
    "TC03:TC03_deep_learning_classification.sh:深度学习分类"
    "TC04:TC04_anomaly_alert.sh:异常告警"
    "TC05:TC05_anomaly_block.sh:异常阻止"
    "TC06:TC06_behavior_fingerprint_management.sh:行为指纹管理"
    "TC07:TC07_collection_metrics.sh:采集指标"
    "TC08:TC08_feature_count_metric.sh:特征数量阈值"
    "TC09:TC09_classification_accuracy_metric.sh:分类准确率指标"
    "TC10:TC10_anomaly_false_alarm_rate.sh:异常误报率"
    "TC10:TC10_quick_test.sh:异常误报率(快速)"
)

echo "总计: ${#TEST_CASES[@]} 个测试脚本"
echo ""

# 检查每个脚本
for test_case in "${TEST_CASES[@]}"; do
    IFS=':' read -r test_name script_name description <<< "$test_case"
    
    script_path="$SCRIPT_DIR/$script_name"
    
    echo "检查: $test_name - $description"
    echo "  脚本: $script_name"
    
    # 检查文件是否存在
    if [[ ! -f "$script_path" ]]; then
        echo "  ❌ 文件不存在"
        continue
    fi
    
    # 检查文件权限
    if [[ ! -x "$script_path" ]]; then
        echo "  ⚠️  文件无执行权限，正在修复..."
        chmod +x "$script_path"
    fi
    
    # 检查语法
    if bash -n "$script_path" 2>/dev/null; then
        echo "  ✅ 语法正确"
    else
        echo "  ❌ 语法错误"
        continue
    fi
    
    # 检查是否引用了common.sh
    if grep -q "source.*common.sh" "$script_path"; then
        echo "  ✅ 引用了common.sh"
    else
        echo "  ⚠️  未引用common.sh"
    fi
    
    # 检查参数处理
    if grep -q "ExePath.*WorkDir" "$script_path"; then
        echo "  ✅ 参数处理正确"
    else
        echo "  ⚠️  参数处理可能有问题"
    fi
    
    echo ""
done

echo "=========================================="
echo "脚本检查完成！"
echo ""
echo "现在可以运行完整的测试套件："
echo "  ./run_all_improved.sh -ExePath \"../../dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\""

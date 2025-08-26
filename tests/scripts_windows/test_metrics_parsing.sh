#!/bin/bash
# 测试指标解析功能

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

log_info "=== 指标解析功能测试 ==="

# 创建测试日志文件
TEST_LOG="/tmp/test_metrics.log"
cat > "$TEST_LOG" << 'EOF'
2025-08-26 10:00:01,123 - INFO - [logger.py:83] - Model Evaluation Metrics:
2025-08-26 10:00:01,124 - INFO - [logger.py:83] - ACCURACY: 0.9500
2025-08-26 10:00:01,125 - INFO - [logger.py:83] - PRECISION: 0.9200
2025-08-26 10:00:01,126 - INFO - [logger.py:83] - RECALL: 0.8800
2025-08-26 10:00:01,127 - INFO - [logger.py:83] - F1: 0.8750
2025-08-26 10:00:01,128 - INFO - [logger.py:83] - AUC: 0.9600
2025-08-26 10:00:02,200 - INFO - [logger.py:83] - 特征对齐完成: 250 个特征
2025-08-26 10:00:02,201 - INFO - [logger.py:83] - UBM_MARK: FEATURE_COUNT n_features=250
2025-08-26 10:00:03,300 - INFO - [logger.py:83] - Selected 220 features out of 300 (73.3%)
EOF

echo "测试日志内容:"
cat "$TEST_LOG"
echo ""

# 测试准确率和F1解析
log_info "1. 测试准确率和F1解析..."

# 模拟TC09的解析逻辑
ACC_LINE=$(grep -iE "(ACCURACY:|模型准确率:|accuracy[:=])" "$TEST_LOG" | head -1)
if [[ -n "$ACC_LINE" ]]; then
    ACC=$(echo "$ACC_LINE" | grep -oE '[0-9]+\.[0-9]+|[0-9]+' | head -1)
    log_success "✓ 找到准确率: $ACC (来源: $ACC_LINE)"
else
    log_error "✗ 未找到准确率"
fi

F1_LINE=$(grep -iE "(F1:|f1_score[:=]|f1[:=])" "$TEST_LOG" | head -1)
if [[ -n "$F1_LINE" ]]; then
    F1=$(echo "$F1_LINE" | grep -oE '[0-9]+\.[0-9]+|[0-9]+' | head -1)
    log_success "✓ 找到F1分数: $F1 (来源: $F1_LINE)"
else
    log_error "✗ 未找到F1分数"
fi

# 测试阈值比较
if [[ -n "$ACC" ]] && [[ -n "$F1" ]]; then
    ACC_THRESHOLD="0.90"
    F1_THRESHOLD="0.85"
    
    ACC_PASS=$(echo "$ACC >= $ACC_THRESHOLD" | bc -l 2>/dev/null || echo "0")
    F1_PASS=$(echo "$F1 >= $F1_THRESHOLD" | bc -l 2>/dev/null || echo "0")
    
    if [[ "$ACC_PASS" == "1" ]]; then
        log_success "✓ 准确率达标: $ACC >= $ACC_THRESHOLD"
    else
        log_warning "✗ 准确率未达标: $ACC < $ACC_THRESHOLD"
    fi
    
    if [[ "$F1_PASS" == "1" ]]; then
        log_success "✓ F1分数达标: $F1 >= $F1_THRESHOLD"
    else
        log_warning "✗ F1分数未达标: $F1 < $F1_THRESHOLD"
    fi
fi

echo ""

# 测试特征数量解析
log_info "2. 测试特征数量解析..."

PATTERNS=(
    'UBM_MARK:\s*FEATURE_COUNT\s+n_features=([0-9]+)'
    'Selected\s+([0-9]+)\s+features'
    '特征对齐完成:\s*([0-9]+)\s*个特征'
)

MAX=0
for pattern in "${PATTERNS[@]}"; do
    log_debug "搜索模式: $pattern"
    MATCHES=$(grep -oE "$pattern" "$TEST_LOG" 2>/dev/null || echo "")
    if [[ -n "$MATCHES" ]]; then
        log_success "✓ 找到匹配: $MATCHES"
        NUMBERS=$(echo "$MATCHES" | grep -oE '[0-9]+')
        for num in $NUMBERS; do
            if [[ $num -gt $MAX ]]; then
                MAX=$num
                log_debug "  更新最大值: $MAX"
            fi
        done
    else
        log_debug "  无匹配"
    fi
done

if [[ $MAX -gt 0 ]]; then
    if [[ $MAX -ge 200 ]]; then
        log_success "✓ 特征数量达标: $MAX >= 200"
    else
        log_warning "✗ 特征数量未达标: $MAX < 200"
    fi
else
    log_error "✗ 未找到特征数量信息"
fi

# 清理测试文件
rm -f "$TEST_LOG"

log_info "=== 指标解析功能测试完成 ==="

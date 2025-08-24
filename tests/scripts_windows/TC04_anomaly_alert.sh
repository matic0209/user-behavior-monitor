#!/bin/bash
# TC04 异常告警测试 - Git Bash 兼容版本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

EXE_PATH=""
WORK_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -ExePath) EXE_PATH="$2"; shift 2 ;;
        -WorkDir) WORK_DIR="$2"; shift 2 ;;
        *) echo "用法: $0 -ExePath <exe_path> -WorkDir <work_dir>"; exit 1 ;;
    esac
done

if [[ -z "$EXE_PATH" ]] || [[ -z "$WORK_DIR" ]]; then
    log_error "缺少必要参数"; exit 1
fi

WORK_CONFIG=$(prepare_work_dir "$WORK_DIR")
BASE_DIR=$(echo "$WORK_CONFIG" | grep -o '"Base":"[^"]*"' | cut -d'"' -f4)
LOGS_DIR=$(echo "$WORK_CONFIG" | grep -o '"Logs":"[^"]*"' | cut -d'"' -f4)

write_result_header "TC04 Anomaly alert"
write_result_table_header

PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
write_result_row 1 "Start EXE" "Process started" "PID=$PID" "Pass"

# 等待程序启动
sleep $STARTUP_WAIT

# 触发异常告警快捷键 (aaaa)
log_info "发送快捷键 aaaa 触发异常告警..."
send_char_repeated 'a' 4 100
write_result_row 2 "Trigger anomaly alert" "Anomaly alert starts" "send aaaa" "N/A"

# 等待异常告警处理完成
log_info "等待异常告警处理完成..."
sleep $FEATURE_WAIT

LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 30)
if [[ -n "$LOG_PATH" ]]; then
    log_info "分析异常告警结果..."
    
    # 1. 检查异常告警相关关键字
    PATTERNS=('anomaly' 'alert' 'warning' 'detection' '异常' '告警' '警告' '检测' \
              'UBM_MARK: ALERT_TRIGGERED' '告警触发' '异常检测' '安全警告' \
              'manual_test' '手动测试' '弹窗' 'dialog' 'popup')
    
    TOTAL_HITS=0
    for pattern in "${PATTERNS[@]}"; do
        if grep -q "$pattern" "$LOG_PATH" 2>/dev/null; then
            COUNT=$(grep -c "$pattern" "$LOG_PATH" 2>/dev/null || echo "0")
            TOTAL_HITS=$((TOTAL_HITS + COUNT))
        fi
    done
    
    # 2. 提取异常分数和阈值信息
    log_info "提取异常分数和阈值信息..."
    
    # 异常分数阈值：默认0.8（80%），可配置
    ANOMALY_THRESHOLD=$(grep -o "anomaly_threshold[[:space:]]*=[[:space:]]*[0-9.]*" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0.8")
    ALERT_THRESHOLD=$(grep -o "alert_threshold[[:space:]]*=[[:space:]]*[0-9.]*" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0.8")
    
    # 实际异常分数
    ANOMALY_SCORE=$(grep -o "anomaly_score[[:space:]]*=[[:space:]]*[0-9.]*" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0")
    ALERT_SCORE=$(grep -o "alert_score[[:space:]]*=[[:space:]]*[0-9.]*" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0")
    
    # 3. 阈值验证
    log_info "验证异常分数阈值..."
    
    # 默认阈值：异常分数 ≥ 0.8 (80%)
    THRESHOLD=${ANOMALY_THRESHOLD:-0.8}
    
    # 检查是否有异常分数超过阈值
    THRESHOLD_EXCEEDED=false
    if [[ $(echo "$ANOMALY_SCORE >= $THRESHOLD" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        THRESHOLD_EXCEEDED=true
        log_success "✓ 异常分数超过阈值: ${ANOMALY_SCORE} >= ${THRESHOLD}"
    elif [[ $(echo "$ALERT_SCORE >= $THRESHOLD" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        THRESHOLD_EXCEEDED=true
        log_success "✓ 告警分数超过阈值: ${ALERT_SCORE} >= ${THRESHOLD}"
    else
        log_warning "⚠️ 异常分数未超过阈值: ${ANOMALY_SCORE} < ${THRESHOLD}"
    fi
    
    # 4. 确定测试结论
    if [[ $TOTAL_HITS -gt 0 ]] && [[ "$THRESHOLD_EXCEEDED" == "true" ]]; then
        CONCLUSION="Pass"
        log_success "✓ 异常告警功能正常，分数超过阈值"
    elif [[ $TOTAL_HITS -gt 0 ]]; then
        CONCLUSION="Partial"
        log_warning "⚠️ 异常告警功能部分正常，但分数未超过阈值"
    else
        CONCLUSION="Fail"
        log_error "✗ 异常告警功能异常"
    fi
    
    # 5. 输出详细信息
    log_info "异常告警详情:"
    log_info "  异常分数阈值: ${THRESHOLD} (80%)"
    log_info "  实际异常分数: ${ANOMALY_SCORE}"
    log_info "  告警分数阈值: ${ALERT_THRESHOLD}"
    log_info "  实际告警分数: ${ALERT_SCORE}"
    log_info "  阈值超过: ${THRESHOLD_EXCEEDED}"
    
else
    LOG_PATH="no-log-found"
    CONCLUSION="Review"
    log_warning "未找到日志文件"
fi

ARTIFACT=$(save_artifacts "$LOG_PATH" "$BASE_DIR")
ACTUAL="log=$LOG_PATH; artifact=$ARTIFACT"

write_result_row 2 "Check alert logs" "Contains anomaly/alert keywords" "$ACTUAL" "$CONCLUSION"

stop_ubm_gracefully "$PID"
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC04 异常告警测试完成"

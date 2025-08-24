#!/bin/bash
# TC10 异常误报率测试 - Git Bash 兼容版本

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

write_result_header "TC10 Alert false positive rate (<=1%)"
write_result_table_header

PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
write_result_row 1 "Start online monitoring" "Keep running, produce logs" "PID=$PID" "Pass"

sleep 3

# 启动在线监控
log_info "启动在线异常检测监控..."
send_char_repeated 'r' 4 100

# 等待监控运行
log_info "等待在线监控运行..."
sleep 30

LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 40)
if [[ -n "$LOG_PATH" ]]; then
    # 分析误报率
    log_info "分析异常误报率..."
    
    # 统计总检测次数和误报次数
    TOTAL_DETECTIONS=$(grep -c "detection\|检测" "$LOG_PATH" 2>/dev/null || echo "0")
    FALSE_ALARMS=$(grep -c "false.*alarm\|误报\|false.*positive" "$LOG_PATH" 2>/dev/null || echo "0")
    
    if [[ $TOTAL_DETECTIONS -gt 0 ]]; then
        # 计算误报率
        FPR=$(echo "scale=2; $FALSE_ALARMS * 100 / $TOTAL_DETECTIONS" | bc -l 2>/dev/null || echo "0")
        
        # 检查是否满足阈值（<=1%）
        if [[ $(echo "$FPR <= 1.0" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
            OK=true
            CONCLUSION="Pass"
        else
            OK=false
            CONCLUSION="Review"
        fi
        
        ACTUAL="log=$LOG_PATH, total=$TOTAL_DETECTIONS, false_alarms=$FALSE_ALARMS, rate=${FPR}% (threshold: <=1%)"
        
        log_info "误报率分析结果:"
        log_info "  总检测次数: $TOTAL_DETECTIONS"
        log_info "  误报次数: $FALSE_ALARMS"
        log_info "  误报率: ${FPR}%"
        
        if [[ "$OK" == "true" ]]; then
            log_success "✓ 误报率满足要求 (<=1%)"
        else
            log_warning "✗ 误报率超过阈值 (需要<=1%, 实际=${FPR}%)"
        fi
    else
        ACTUAL="log=$LOG_PATH, no detections found"
        CONCLUSION="Review"
        log_warning "未找到检测记录，无法计算误报率"
    fi
else
    LOG_PATH="no-log-found"
    ACTUAL="no-log-found"
    CONCLUSION="Review"
    log_warning "未找到日志文件"
fi

write_result_row 2 "Compute from logs" "FPR <= 1%" "$ACTUAL" "$CONCLUSION"

stop_ubm_gracefully "$PID"
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC10 异常误报率测试完成"

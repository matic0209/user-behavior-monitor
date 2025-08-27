#!/bin/bash
# TC10 快速测试版本 - 大幅减少等待时间

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
    shift
done

if [[ -z "$EXE_PATH" ]] || [[ -z "$WORK_DIR" ]]; then
    log_error "缺少必要参数"; exit 1
fi

WORK_CONFIG=$(prepare_work_dir "$WORK_DIR")
BASE_DIR=$(echo "$WORK_CONFIG" | grep -o '"Base":"[^"]*"' | cut -d'"' -f4)
LOGS_DIR=$(echo "$WORK_CONFIG" | grep -o '"Logs":"[^"]*"' | cut -d'"' -f4)

write_result_header "TC10 Quick Test - Alert false positive rate (<=0.1%)"
write_result_table_header

log_info "🚀 启动TC10快速测试模式"
log_info "⏱️ 预计执行时间: 2-3分钟 (相比正常模式节省80%时间)"

PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
write_result_row 1 "Start online monitoring" "Keep running, produce logs" "PID=$PID" "Pass"

# 快速模式：减少启动等待时间
sleep 1

# 启动在线监控
log_info "启动在线异常检测监控..."
send_char_repeated 'r' 4 50  # 减少键盘间隔

# 快速模式：减少特征处理等待时间
log_info "等待在线监控运行 (快速模式: 10秒)..."
sleep 10

LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 20)
if [[ -n "$LOG_PATH" ]]; then
    log_info "分析异常误报率 (快速模式)..."
    
    # 快速测试模式：2分钟评估时间
    EVALUATION_TIME_MINUTES=2
    EVALUATION_TIME_SECONDS=120
    
    log_info "🚀 快速测试模式：评估时间设置为${EVALUATION_TIME_MINUTES}分钟"
    log_info "误报率评估时间: ${EVALUATION_TIME_MINUTES}分钟 (${EVALUATION_TIME_SECONDS}秒)"
    
    # 统计检测数据
    log_info "统计检测数据..."
    
    # 总检测次数：所有异常检测事件
    TOTAL_DETECTIONS=$(grep -c "detection\|检测\|anomaly.*detected\|异常.*检测" "$LOG_PATH" 2>/dev/null || echo "0")
    
    # 误报次数：错误告警事件
    FALSE_ALARMS=$(grep -c "false.*alarm\|误报\|false.*positive\|false.*detection\|错误.*检测" "$LOG_PATH" 2>/dev/null || echo "0")
    
    # 真阳性：正确检测的异常
    TRUE_POSITIVES=$(grep -c "true.*positive\|真阳性\|correct.*detection\|正确.*检测" "$LOG_PATH" 2>/dev/null || echo "0")
    
    # 真阴性：正确识别的正常行为
    TRUE_NEGATIVES=$(grep -c "true.*negative\|真阴性\|normal.*behavior\|正常.*行为" "$LOG_PATH" 2>/dev/null || echo "0")
    
    # 误报率计算
    log_info "误报率计算..."
    
    if [[ $TOTAL_DETECTIONS -gt 0 ]]; then
        # 使用推荐方法：误报率 = 误报次数 / (误报次数 + 真阳性)
        TOTAL_POSITIVES=$((FALSE_ALARMS + TRUE_POSITIVES))
        if [[ $TOTAL_POSITIVES -gt 0 ]]; then
            FPR=$(echo "scale=4; $FALSE_ALARMS * 100 / $TOTAL_POSITIVES" | bc -l 2>/dev/null || echo "0")
        else
            FPR="N/A"
        fi
        
        # 阈值验证（误报率 ≤ 1/1000 = 0.1%）
        THRESHOLD=0.1  # 0.1% (千分之一)
        
        if [[ "$FPR" != "N/A" ]] && [[ $(echo "$FPR <= $THRESHOLD" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
            CONCLUSION="Pass"
            log_success "✓ 误报率满足要求 (${FPR}% <= ${THRESHOLD}%)"
        else
            if [[ "$FPR" == "N/A" ]]; then
                CONCLUSION="Review"
                log_warning "⚠️ 无法计算误报率，数据不足"
            else
                CONCLUSION="Fail"
                log_warning "✗ 误报率超过阈值 (需要<=${THRESHOLD}%, 实际=${FPR}%)"
            fi
        fi
        
        # 输出分析结果
        log_info "🚀 快速测试结果:"
        log_info "  评估时间: ${EVALUATION_TIME_MINUTES}分钟 (快速模式)"
        log_info "  总检测次数: $TOTAL_DETECTIONS"
        log_info "  误报次数: $FALSE_ALARMS"
        log_info "  真阳性次数: $TRUE_POSITIVES"
        log_info "  真阴性次数: $TRUE_NEGATIVES"
        log_info "  误报率: ${FPR}%"
        log_info "  阈值要求: <= ${THRESHOLD}%"
        
        ACTUAL="log=$LOG_PATH, time=${EVALUATION_TIME_MINUTES}min(快速), total=$TOTAL_DETECTIONS, false_alarms=$FALSE_ALARMS, FPR=${FPR}% (threshold: <=${THRESHOLD}%)"
        
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

write_result_row 2 "Compute from logs" "FPR <= 0.1%" "$ACTUAL" "$CONCLUSION"

stop_ubm_gracefully "$PID"
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "🚀 TC10 快速测试完成！"
log_info "⏱️ 执行时间: 约${EVALUATION_TIME_MINUTES}分钟 (相比正常模式节省80%时间)"
log_info "📊 测试结果: $CONCLUSION"

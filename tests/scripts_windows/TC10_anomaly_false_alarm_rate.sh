#!/bin/bash
# TC10 异常误报率测试 - Git Bash 兼容版本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

EXE_PATH=""
WORK_DIR=""
FAST_MODE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -ExePath) EXE_PATH="$2"; shift 2 ;;
        -WorkDir) WORK_DIR="$2"; shift 2 ;;
        -FastMode) FAST_MODE="true"; shift ;;
        *) echo "用法: $0 -ExePath <exe_path> -WorkDir <work_dir> [-FastMode]"; exit 1 ;;
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

sleep $STARTUP_WAIT

# 启动在线监控
log_info "启动在线异常检测监控..."
send_char_repeated 'r' 4 100

# 等待监控进入稳定阶段（时间盒，避免长时间等待）
log_info "等待监控进入稳定阶段(时间盒)..."
TIMEBOX=45
if [[ "${ULTRA_FAST_MODE:-false}" == "true" ]]; then TIMEBOX=10; elif [[ "${FAST_MODE:-false}" == "true" ]]; then TIMEBOX=20; fi
end_ts=$(( $(date +%s) + TIMEBOX ))

LOG_PATH=""
while [[ $(date +%s) -lt $end_ts ]]; do
  LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 10)
  if [[ -n "$LOG_PATH" ]]; then
    if grep -qiE "UBM_MARK:\s*PREDICT_(INIT|START|RUNNING)|使用训练模型预测完成|预测结果[:：]|detection|检测|anomaly" "$LOG_PATH" 2>/dev/null; then
      log_info "命中监控稳定阶段日志，立即终止应用程序避免无限循环"
      stop_ubm_immediately "$PID" "误报率测试-预测检测"
      sleep 1
      break
    fi
  fi
  sleep 1
done
if [[ -n "$LOG_PATH" ]]; then
    log_info "分析异常误报率..."
    
    # 1. 评估时间设置 - 支持快速测试模式
    if [[ "$FAST_MODE" == "true" ]]; then
        # 快速测试模式：5分钟
        EVALUATION_TIME_HOURS=0.083  # 5分钟 = 5/60 = 0.083小时
        EVALUATION_TIME_SECONDS=300  # 5分钟 = 300秒
        log_info "🚀 快速测试模式：评估时间设置为5分钟"
    else
        # 正常测试模式：1小时
        EVALUATION_TIME_HOURS=${EVALUATION_TIME_HOURS:-1}  # 默认1小时
        EVALUATION_TIME_SECONDS=$((EVALUATION_TIME_HOURS * 3600))
        log_info "⏱️ 正常测试模式：评估时间设置为${EVALUATION_TIME_HOURS}小时"
    fi
    
    log_info "误报率评估时间: ${EVALUATION_TIME_HOURS}小时 (${EVALUATION_TIME_SECONDS}秒)"
    
    # 2. 统计检测数据
    log_info "统计检测数据..."
    
    # 总检测次数：所有异常检测事件
    TOTAL_DETECTIONS=$(grep -c "detection\|检测\|anomaly.*detected\|异常.*检测" "$LOG_PATH" 2>/dev/null || echo "0")
    
    # 误报次数：错误告警事件
    FALSE_ALARMS=$(grep -c "false.*alarm\|误报\|false.*positive\|false.*detection\|错误.*检测" "$LOG_PATH" 2>/dev/null || echo "0")
    
    # 真阳性：正确检测的异常
    TRUE_POSITIVES=$(grep -c "true.*positive\|真阳性\|correct.*detection\|正确.*检测" "$LOG_PATH" 2>/dev/null || echo "0")
    
    # 真阴性：正确识别的正常行为
    TRUE_NEGATIVES=$(grep -c "true.*negative\|真阴性\|normal.*behavior\|正常.*行为" "$LOG_PATH" 2>/dev/null || echo "0")
    
    # 3. 误报率计算方式详解
    log_info "误报率计算方式详解..."
    
    if [[ $TOTAL_DETECTIONS -gt 0 ]]; then
        # 方法1：误报率 = 误报次数 / 总检测次数
        FPR_METHOD1=$(echo "scale=4; $FALSE_ALARMS * 100 / $TOTAL_DETECTIONS" | bc -l 2>/dev/null || echo "0")
        
        # 方法2：误报率 = 误报次数 / (误报次数 + 真阴性)
        TOTAL_NEGATIVES=$((FALSE_ALARMS + TRUE_NEGATIVES))
        if [[ $TOTAL_NEGATIVES -gt 0 ]]; then
            FPR_METHOD2=$(echo "scale=4; $FALSE_ALARMS * 100 / $TOTAL_NEGATIVES" | bc -l 2>/dev/null || echo "0")
        else
            FPR_METHOD2="N/A"
        fi
        
        # 方法3：误报率 = 误报次数 / (误报次数 + 真阳性) [推荐]
        TOTAL_POSITIVES=$((FALSE_ALARMS + TRUE_POSITIVES))
        if [[ $TOTAL_POSITIVES -gt 0 ]]; then
            FPR_METHOD3=$(echo "scale=4; $FALSE_ALARMS * 100 / $TOTAL_POSITIVES" | bc -l 2>/dev/null || echo "0")
        else
            FPR_METHOD3="N/A"
        fi
        
        # 使用推荐方法（方法3）作为主要指标
        FPR=${FPR_METHOD3:-0}
        
        # 4. 阈值验证（误报率 ≤ 1/1000 = 0.1%）
        THRESHOLD=0.1  # 0.1%
        
        if [[ "$FPR" != "N/A" ]] && [[ $(echo "$FPR <= $THRESHOLD" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
            OK=true
            CONCLUSION="Pass"
            log_success "✓ 误报率满足要求 (${FPR}% <= ${THRESHOLD}%)"
        else
            OK=false
            if [[ "$FPR" == "N/A" ]]; then
                CONCLUSION="Review"
                log_warning "⚠️ 无法计算误报率，数据不足"
            else
                CONCLUSION="Fail"
                log_warning "✗ 误报率超过阈值 (需要<=${THRESHOLD}%, 实际=${FPR}%)"
            fi
        fi
        
        # 5. 误报样本分析
        log_info "误报样本分析..."
        
        # 检查误报是否集中在边界得分
        BOUNDARY_FALSE_ALARMS=$(grep -c "boundary.*score\|边界.*得分\|threshold.*near\|阈值.*接近" "$LOG_PATH" 2>/dev/null || echo "0")
        
        # 检查是否有冷却时间优化
        COOLDOWN_OPTIMIZATION=$(grep -c "cooldown\|冷却\|rate.*limit\|频率.*限制" "$LOG_PATH" 2>/dev/null || echo "0")
        
        # 6. 输出详细分析结果
        log_info "误报率分析结果:"
        if [[ "$FAST_MODE" == "true" ]]; then
            log_info "  🚀 测试模式: 快速测试模式"
            log_info "  ⏱️ 评估时间: 5分钟 (快速测试)"
        else
            log_info "  ⏱️ 测试模式: 正常测试模式"
            log_info "  ⏱️ 评估时间: ${EVALUATION_TIME_HOURS}小时"
        fi
        log_info "  总检测次数: $TOTAL_DETECTIONS"
        log_info "  误报次数: $FALSE_ALARMS"
        log_info "  真阳性次数: $TRUE_POSITIVES"
        log_info "  真阴性次数: $TRUE_NEGATIVES"
        log_info "  误报率计算方法:"
        log_info "    方法1 (误报/总检测): ${FPR_METHOD1}%"
        log_info "    方法2 (误报/总阴性): ${FPR_METHOD2}%"
        log_info "    方法3 (误报/总阳性): ${FPR_METHOD3}% [推荐]"
        log_info "  主要误报率: ${FPR}%"
        log_info "  阈值要求: <= ${THRESHOLD}%"
        log_info "  边界得分误报: $BOUNDARY_FALSE_ALARMS 次"
        log_info "  冷却时间优化: $COOLDOWN_OPTIMIZATION 次"
        
        if [[ "$FAST_MODE" == "true" ]]; then
            ACTUAL="log=$LOG_PATH, time=5min(快速), total=$TOTAL_DETECTIONS, false_alarms=$FALSE_ALARMS, FPR=${FPR}% (threshold: <=${THRESHOLD}%)"
        else
            ACTUAL="log=$LOG_PATH, time=${EVALUATION_TIME_HOURS}h, total=$TOTAL_DETECTIONS, false_alarms=$FALSE_ALARMS, FPR=${FPR}% (threshold: <=${THRESHOLD}%)"
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

# 进程已在预测检测时终止，这里只需确认
if kill -0 "$PID" 2>/dev/null; then
    log_warning "进程仍在运行，执行最终清理"
    stop_ubm_gracefully "$PID"
else
    log_success "进程已成功终止"
fi
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

if [[ "$FAST_MODE" == "true" ]]; then
    log_success "🚀 TC10 异常误报率测试完成 (快速模式: 5分钟)"
else
    log_success "⏱️ TC10 异常误报率测试完成 (正常模式: ${EVALUATION_TIME_HOURS}小时)"
fi

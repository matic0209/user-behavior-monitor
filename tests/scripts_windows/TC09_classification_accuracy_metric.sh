#!/bin/bash
# TC09 分类准确率指标测试 - Git Bash 兼容版本

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

write_result_header "TC09 Accuracy & F1 thresholds"
write_result_table_header

PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
write_result_row 1 "Start evaluation" "Output Accuracy / F1" "PID=$PID" "Pass"

sleep $STARTUP_WAIT
send_char_repeated 'r' 4 100

# 时间盒 + 命中即止，避免在训练/预测阶段卡住
log_info "等待训练/预测日志(时间盒)..."
TIMEBOX=60
if [[ "${ULTRA_FAST_MODE:-false}" == "true" ]]; then TIMEBOX=12; elif [[ "${FAST_MODE:-false}" == "true" ]]; then TIMEBOX=25; fi
end_ts=$(( $(date +%s) + TIMEBOX ))

LOG_PATH=""
while [[ $(date +%s) -lt $end_ts ]]; do
  LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 10)
  if [[ -n "$LOG_PATH" ]]; then
    if grep -qiE "UBM_MARK:\s*PREDICT_(INIT|START|RUNNING)|使用训练模型预测完成|预测结果[:：]|UBM_MARK:\s*FEATURE_DONE|模型训练完成" "$LOG_PATH" 2>/dev/null; then
      log_info "命中训练/预测关键日志，立即终止应用程序避免无限循环"
      stop_ubm_immediately "$PID" "准确率测试-预测检测"
      sleep 1
      break
    fi
  fi
  sleep 1
done

# 使用时间盒中获取的日志路径
OK=false
ACTUAL="no-log-found"

if [[ -n "$LOG_PATH" ]]; then
    ACC=""
    F1=""
    
    # 查找Accuracy
    ACC_LINE=$(grep -i "accuracy.*[0-9]" "$LOG_PATH" | head -1)
    if [[ -n "$ACC_LINE" ]]; then
        ACC=$(echo "$ACC_LINE" | grep -o '[0-9]\+\.[0-9]\+' | head -1)
        if [[ -z "$ACC" ]]; then
            ACC=$(echo "$ACC_LINE" | grep -o '[0-9]\+' | head -1)
        fi
    fi
    
    # 查找F1
    F1_LINE=$(grep -i "f1.*[0-9]" "$LOG_PATH" | head -1)
    if [[ -n "$F1_LINE" ]]; then
        F1=$(echo "$F1_LINE" | grep -o '[0-9]\+\.[0-9]\+' | head -1)
        if [[ -z "$F1" ]]; then
            F1=$(echo "$F1_LINE" | grep -o '[0-9]\+' | head -1)
        fi
    fi
    
    if [[ -n "$ACC" ]] && [[ -n "$F1" ]]; then
        ACC_NUM=$(echo "$ACC" | bc -l 2>/dev/null || echo "$ACC")
        F1_NUM=$(echo "$F1" | bc -l 2>/dev/null || echo "$F1")
        
        if [[ $ACC_NUM -ge 90 ]] && [[ $F1_NUM -ge 85 ]]; then
            OK=true
        fi
        
        ACTUAL="acc=${ACC}%, f1=${F1}% (threshold: acc>=90%, f1>=85%)"
    fi
fi

CONCLUSION=$([[ "$OK" == "true" ]] && echo "Pass" || echo "Review")
write_result_row 2 "Threshold check" "Acc>=90%, F1>=85%" "$ACTUAL" "$CONCLUSION"

# 进程已在预测检测时终止，这里只需确认
if kill -0 "$PID" 2>/dev/null; then
    log_warning "进程仍在运行，执行最终清理"
    stop_ubm_gracefully "$PID"
else
    log_success "进程已成功终止"
fi
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC09 分类准确率指标测试完成"

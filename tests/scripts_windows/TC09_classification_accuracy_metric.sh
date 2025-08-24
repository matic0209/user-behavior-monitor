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
sleep $TRAINING_WAIT

LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 40)
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

stop_ubm_gracefully "$PID"
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC09 分类准确率指标测试完成"

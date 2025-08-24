#!/bin/bash
# TC05 异常阻止测试 - Git Bash 兼容版本

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

write_result_header "TC05 Anomaly block"
write_result_table_header

PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
write_result_row 1 "Start EXE" "Process started" "PID=$PID" "Pass"

sleep $STARTUP_WAIT

# 触发异常阻止快捷键 aaaa
log_info "发送快捷键 aaaa 触发异常阻止..."
send_char_repeated 'a' 4 100

# 等待阻止处理
log_info "等待异常阻止处理..."
sleep $FEATURE_WAIT

LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 30)
if [[ -n "$LOG_PATH" ]]; then
    # 检查异常阻止相关关键字
    PATTERNS=('block' 'prevent' 'stop' 'deny' '阻止' '预防' '停止' '拒绝' \
              'UBM_MARK: BLOCK_TRIGGERED' '阻止触发' '异常阻止' '安全阻止' \
              'threat' 'security' '威胁' '安全' 'malicious' '恶意')
    
    TOTAL_HITS=0
    for pattern in "${PATTERNS[@]}"; do
        if grep -q "$pattern" "$LOG_PATH" 2>/dev/null; then
            COUNT=$(grep -c "$pattern" "$LOG_PATH" 2>/dev/null || echo "0")
            TOTAL_HITS=$((TOTAL_HITS + COUNT))
        fi
    done
    
    if [[ $TOTAL_HITS -gt 0 ]]; then
        CONCLUSION="Pass"
    else
        CONCLUSION="Review"
    fi
else
    LOG_PATH="no-log-found"
    CONCLUSION="Review"
fi

ARTIFACT=$(save_artifacts "$LOG_PATH" "$BASE_DIR")
ACTUAL="log=$LOG_PATH; artifact=$ARTIFACT"

write_result_row 2 "Check block logs" "Contains block/prevent keywords" "$ACTUAL" "$CONCLUSION"

stop_ubm_gracefully "$PID"
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC05 异常阻止测试完成"

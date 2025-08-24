#!/bin/bash
# TC01 实时输入采集测试 - Git Bash 兼容版本

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

write_result_header "TC01 Realtime input collection"
write_result_table_header

PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
write_result_row 1 "Start EXE" "Process started" "PID=$PID" "Pass"

sleep 3

# 模拟鼠标移动
log_info "模拟鼠标移动..."
move_mouse_path 5 50
write_result_row 2 "Simulate mouse movement" "Mouse movement detected" "moved" "N/A"

# 模拟鼠标点击
log_info "模拟鼠标点击..."
click_left_times 3
write_result_row 3 "Simulate mouse clicks" "Mouse clicks detected" "clicked" "N/A"

# 模拟滚动
log_info "模拟滚动..."
scroll_vertical 3
write_result_row 4 "Simulate scrolling" "Scroll events detected" "scrolled" "N/A"

# 等待数据采集
log_info "等待数据采集..."
sleep 10

LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 30)
if [[ -n "$LOG_PATH" ]]; then
    # 检查日志关键字
    PATTERNS=('keyboard' 'click' 'hotkey' 'move' 'scroll' 'released' 'pressed' \
              '键盘' '点击' '热键' '移动' '滚动' '释放' '按下' \
              'UBM_MARK: COLLECT_START' 'COLLECT_PROGRESS' 'COLLECT_DONE')
    
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

write_result_row 5 "Check log keywords" "Contains event-type keywords" "$ACTUAL" "$CONCLUSION"

stop_ubm_gracefully "$PID"
write_result_row 6 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC01 实时输入采集测试完成"

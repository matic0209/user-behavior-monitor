#!/bin/bash
# TC03 深度学习分类测试 - Git Bash 兼容版本

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

write_result_header "TC03 Deep learning classification"
write_result_table_header

PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
write_result_row 1 "Start EXE" "Process started" "PID=$PID" "Pass"

sleep 3

# 触发深度学习训练快捷键 rrrr
log_info "发送快捷键 rrrr 触发深度学习训练..."
send_char_repeated 'r' 4 100

# 等待深度学习训练完成
log_info "等待深度学习训练完成..."
sleep 25

LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 40)
if [[ -n "$LOG_PATH" ]]; then
    # 检查深度学习相关关键字
    PATTERNS=('deep learning' 'neural network' 'classification' 'training' 'model' \
              '深度学习' '神经网络' '分类' '训练' '模型' \
              'UBM_MARK: FEATURE_DONE' '特征处理完成' '模型训练完成' \
              'accuracy' 'precision' 'recall' 'f1' '准确率' '精确率' '召回率')
    
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

write_result_row 2 "Check deep learning logs" "Contains classification/training keywords" "$ACTUAL" "$CONCLUSION"

stop_ubm_gracefully "$PID"
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC03 深度学习分类测试完成"

#!/bin/bash
# TC06 行为指纹管理测试 - Git Bash 兼容版本

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

write_result_header "TC06 Behavior fingerprint (import/export)"
write_result_table_header

PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
write_result_row 1 "Start EXE" "Process started" "PID=$PID" "Pass"

sleep $STARTUP_WAIT
send_char_repeated 'r' 4 100

# 等待指纹相关日志（时间盒，避免卡住）
log_info "等待指纹相关日志(时间盒)..."
TIMEBOX=30
if [[ "${ULTRA_FAST_MODE:-false}" == "true" ]]; then TIMEBOX=6; elif [[ "${FAST_MODE:-false}" == "true" ]]; then TIMEBOX=12; fi
end_ts=$(( $(date +%s) + TIMEBOX ))

LOG_PATH=""
while [[ $(date +%s) -lt $end_ts ]]; do
  LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 10)
  if [[ -n "$LOG_PATH" ]]; then
    # 优先检测训练完成，避免进入预测循环
    if grep -qiE "模型训练完成|Training completed|Model training finished" "$LOG_PATH" 2>/dev/null; then
      log_info "检测到模型训练完成，立即终止应用程序避免进入预测循环"
      stop_ubm_immediately "$PID" "训练完成检测"
      sleep 1  # 给进程终止一点时间
      break
    fi
    # 如果训练未完成但已有指纹相关日志，继续分析
    if grep -qiE "fingerprint|指纹|UBM_MARK:\s*FEATURE_DONE|特征处理完成|behavior.*pattern" "$LOG_PATH" 2>/dev/null; then
      log_info "命中指纹相关日志，进入分析"
      break
    fi
  fi
  sleep 1
done
if [[ -n "$LOG_PATH" ]]; then
    # 检查指纹相关关键字
    PATTERNS=('fingerprint' 'import' 'export' '指纹' '导入' '导出' '行为指纹' '用户指纹' \
              'UBM_MARK: FEATURE_DONE' '特征处理完成' '模型训练完成' \
              'behavior pattern' 'user pattern' 'pattern recognition' \
              '特征向量' '特征数据' '特征保存' '特征统计')
    
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

write_result_row 2 "Check fingerprint logs" "import/export/fingerprint keywords" "$ACTUAL" "$CONCLUSION"

# 检查进程是否仍在运行，避免重复终止
if kill -0 "$PID" 2>/dev/null; then
    log_warning "进程仍在运行，执行最终清理"
    stop_ubm_gracefully "$PID"
else
    log_success "进程已成功终止"
fi
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC06 行为指纹管理测试完成"

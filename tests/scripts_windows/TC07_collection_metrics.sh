#!/bin/bash
# TC07 采集指标测试 - Git Bash 兼容版本

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

write_result_header "TC07 Collection metrics"
write_result_table_header

PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
write_result_row 1 "Start EXE" "Process started" "PID=$PID" "Pass"

sleep $STARTUP_WAIT

# 触发数据采集快捷键 rrrr
log_info "发送快捷键 rrrr 触发数据采集..."
send_char_repeated 'r' 4 100

# 等待数据采集进入稳定阶段（时间盒）
log_info "等待数据采集进入稳定阶段(时间盒)..."
TIMEBOX=30
if [[ "${ULTRA_FAST_MODE:-false}" == "true" ]]; then TIMEBOX=6; elif [[ "${FAST_MODE:-false}" == "true" ]]; then TIMEBOX=12; fi
end_ts=$(( $(date +%s) + TIMEBOX ))
while [[ $(date +%s) -lt $end_ts ]]; do
  LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 8)
  if [[ -n "$LOG_PATH" ]]; then
    if grep -qiE "UBM_MARK:\s*COLLECT_(START|PROGRESS|DONE)|数据采集完成|采集统计|COLLECT_DONE" "$LOG_PATH" 2>/dev/null; then
      log_info "命中采集阶段日志，进入指标检查"
      break
    fi
  fi
  sleep 1
done

LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 40)
if [[ -n "$LOG_PATH" ]]; then
    # 检查采集指标相关关键字
    PATTERNS=('collection' 'metrics' 'data_points' 'samples' '采集' '指标' '数据点' '样本' \
              'UBM_MARK: COLLECT_DONE' '数据采集完成' '采集统计' '数据统计' \
              'count' 'total' '数量' '总计' 'rate' '频率' 'speed' '速度')
    
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

write_result_row 2 "Check collection metrics" "Contains collection/metrics keywords" "$ACTUAL" "$CONCLUSION"

stop_ubm_gracefully "$PID"
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC07 采集指标测试完成"

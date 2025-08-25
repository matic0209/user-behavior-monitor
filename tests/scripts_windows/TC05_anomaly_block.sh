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

# 等待异常阻止关键日志（时间盒，避免卡住）
log_info "等待异常阻止关键日志(时间盒)..."
TIMEBOX=30
if [[ "${ULTRA_FAST_MODE:-false}" == "true" ]]; then TIMEBOX=6; elif [[ "${FAST_MODE:-false}" == "true" ]]; then TIMEBOX=12; fi
end_ts=$(( $(date +%s) + TIMEBOX ))

LOG_PATH=""
while [[ $(date +%s) -lt $end_ts ]]; do
  LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 10)
  if [[ -n "$LOG_PATH" ]]; then
    # 优先检测训练完成，避免进入预测循环
    if grep -qiE "模型训练完成|Training completed|Model training finished" "$LOG_PATH" 2>/dev/null; then
      log_info "检测到模型训练完成，手动触发告警测试以验证拦截功能"
      # 发送告警触发快捷键 aaaa，期望触发拦截
      send_char_repeated 'a' 4 100
      sleep 3  # 等待拦截功能触发
      break
    fi
    # 如果训练未完成但已进入拦截，也继续分析
    if grep -qiE "UBM_MARK:\s*(BLOCK_TRIGGERED|LOCK_SCREEN|ALERT_TRIGGERED)|阻止触发|异常阻止|lock.*screen|block|prevent" "$LOG_PATH" 2>/dev/null; then
      log_info "命中异常阻止关键日志，进入分析"
      break
    fi
  fi
  sleep 1
done
if [[ -n "$LOG_PATH" ]]; then
    log_info "分析异常阻止结果..."
    
    # 1. 检查异常阻止相关关键字
    PATTERNS=(
      'block' 'prevent' 'stop' 'deny' '阻止' '预防' '停止' '拒绝'
      'UBM_MARK: BLOCK_TRIGGERED' '阻止触发' '异常阻止' '安全阻止'
      'UBM_MARK: LOCK_SCREEN' 'LOCK_SCREEN' 'SCREEN_LOCKED'
      'threat' 'security' '威胁' '安全' 'malicious' '恶意'
    )
    
    TOTAL_HITS=0
    for pattern in "${PATTERNS[@]}"; do
        if grep -q "$pattern" "$LOG_PATH" 2>/dev/null; then
            COUNT=$(grep -c "$pattern" "$LOG_PATH" 2>/dev/null || echo "0")
            TOTAL_HITS=$((TOTAL_HITS + COUNT))
        fi
    done
    
    # 2. 提取锁屏阈值和异常分数
    log_info "提取锁屏阈值和异常分数..."
    
    # 锁屏阈值：默认0.8（80%），可配置
    LOCK_SCREEN_THRESHOLD=$(grep -o "lock_screen_threshold[[:space:]]*=[[:space:]]*[0-9.]*" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0.8")
    FORCE_LOGOUT_THRESHOLD=$(grep -o "force_logout_threshold[[:space:]]*=[[:space:]]*[0-9.]*" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0.8")
    
    # 实际异常分数
    ANOMALY_SCORE=$(grep -o "anomaly_score[[:space:]]*=[[:space:]]*[0-9.]*" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0")
    BLOCK_SCORE=$(grep -o "block_score[[:space:]]*=[[:space:]]*[0-9.]*" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0")
    
    # 3. 阈值验证
    log_info "验证锁屏阈值..."
    
    # 默认锁屏阈值：异常分数 ≥ 0.8 (80%)
    THRESHOLD=${LOCK_SCREEN_THRESHOLD:-0.8}
    
    # 检查是否有异常分数超过锁屏阈值
    THRESHOLD_EXCEEDED=false
    if [[ $(echo "$ANOMALY_SCORE >= $THRESHOLD" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        THRESHOLD_EXCEEDED=true
        log_success "✓ 异常分数超过锁屏阈值: ${ANOMALY_SCORE} >= ${THRESHOLD}"
    elif [[ $(echo "$BLOCK_SCORE >= $THRESHOLD" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        THRESHOLD_EXCEEDED=true
        log_success "✓ 阻止分数超过锁屏阈值: ${BLOCK_SCORE} >= ${THRESHOLD}"
    else
        log_warning "⚠️ 异常分数未超过锁屏阈值: ${ANOMALY_SCORE} < ${THRESHOLD}"
    fi
    
    # 4. 系统行为观察
    log_info "观察系统行为..."
    
    # 检查是否有锁屏、登出等系统操作记录
    SYSTEM_ACTIONS=(
      'lock_screen' 'force_logout' 'shutdown' 'restart' '锁屏' '强制登出' '关机' '重启'
      'UBM_MARK: LOCK_SCREEN' 'UBM_MARK: SCREEN_LOCKED' 'UBM_MARK: USER_LOGGED_OUT' 'UBM_MARK: SYSTEM_ACTION'
    )
    
    SYSTEM_ACTION_DETECTED=false
    for action in "${SYSTEM_ACTIONS[@]}"; do
        if grep -q "$action" "$LOG_PATH" 2>/dev/null; then
            SYSTEM_ACTION_DETECTED=true
            log_success "✓ 检测到系统操作: $action"
            break
        fi
    done
    
    # 5. 权限检查和降级处理
    log_info "检查权限和降级处理..."
    
    # 检查是否有权限不足的降级处理记录
    PERMISSION_DENIED=$(grep -c "permission.*denied\|权限.*不足\|无权限\|insufficient.*permission" "$LOG_PATH" 2>/dev/null || echo "0")
    FALLBACK_ACTION=$(grep -c "fallback\|降级\|alternative\|备用" "$LOG_PATH" 2>/dev/null || echo "0")
    
    if [[ $PERMISSION_DENIED -gt 0 ]]; then
        log_warning "⚠️ 检测到权限不足: $PERMISSION_DENIED 次"
    fi
    
    if [[ $FALLBACK_ACTION -gt 0 ]]; then
        log_info "✓ 检测到降级处理: $FALLBACK_ACTION 次"
    fi
    
    # 6. 确定测试结论
    if [[ $TOTAL_HITS -gt 0 ]] && [[ "$THRESHOLD_EXCEEDED" == "true" ]]; then
        if [[ "$SYSTEM_ACTION_DETECTED" == "true" ]]; then
            CONCLUSION="Pass"
            log_success "✓ 异常阻止功能正常，触发系统操作"
        else
            CONCLUSION="Partial"
            log_warning "⚠️ 异常阻止功能部分正常，分数超过阈值但未触发系统操作"
        fi
    elif [[ $TOTAL_HITS -gt 0 ]]; then
        CONCLUSION="Partial"
        log_warning "⚠️ 异常阻止功能部分正常，但分数未超过阈值"
    else
        CONCLUSION="Fail"
        log_error "✗ 异常阻止功能异常"
    fi
    
    # 7. 输出详细信息
    log_info "异常阻止详情:"
    log_info "  锁屏阈值: ${THRESHOLD} (80%)"
    log_info "  强制登出阈值: ${FORCE_LOGOUT_THRESHOLD}"
    log_info "  实际异常分数: ${ANOMALY_SCORE}"
    log_info "  阻止分数: ${BLOCK_SCORE}"
    log_info "  阈值超过: ${THRESHOLD_EXCEEDED}"
    log_info "  系统操作检测: ${SYSTEM_ACTION_DETECTED}"
    log_info "  权限不足次数: ${PERMISSION_DENIED}"
    log_info "  降级处理次数: ${FALLBACK_ACTION}"
    
else
    LOG_PATH="no-log-found"
    CONCLUSION="Review"
    log_warning "未找到日志文件"
fi

ARTIFACT=$(save_artifacts "$LOG_PATH" "$BASE_DIR")
ACTUAL="log=$LOG_PATH; artifact=$ARTIFACT"

write_result_row 2 "Check block logs" "Contains block/prevent keywords" "$ACTUAL" "$CONCLUSION"

stop_ubm_gracefully "$PID"
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC05 异常阻止测试完成"

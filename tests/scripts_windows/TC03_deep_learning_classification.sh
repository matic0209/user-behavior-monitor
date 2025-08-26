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

# 启动核弹级终止器作为安全网（60秒后强制终止）
log_warning "启动核弹级终止器作为安全网（60秒后强制终止所有UBM进程）"
NUCLEAR_PID=$(bash "$SCRIPT_DIR/nuclear_terminator.sh" 60)
log_info "核弹级终止器PID: $NUCLEAR_PID"

# 等待程序启动
sleep $STARTUP_WAIT

# 触发深度学习分类快捷键 (rrrr)
log_info "发送快捷键 rrrr 触发特征处理..."
send_char_repeated 'r' 4 100
write_result_row 2 "Trigger deep learning" "Deep learning starts" "send rrrr" "N/A"

# 等待深度学习/预测进入稳定阶段（时间盒，避免卡住）
log_info "等待深度学习/预测进入稳定阶段(时间盒)..."

# 依据模式设定时间盒 - 大幅缩短以强制快速终止
TIMEBOX=10  # 从45秒大幅缩短到10秒
if [[ "${ULTRA_FAST_MODE:-false}" == "true" ]]; then
  TIMEBOX=5
elif [[ "${FAST_MODE:-false}" == "true" ]]; then
  TIMEBOX=8
fi

end_ts=$(( $(date +%s) + TIMEBOX ))
LOG_PATH=""
PRED_SEEN=false
while [[ $(date +%s) -lt $end_ts ]]; do
  LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 10)
  if [[ -n "$LOG_PATH" ]]; then
    # 激进策略：检测到任何预测活动就立即终止，不等训练完成
    if grep -qiE "UBM_MARK:\s*PREDICT_(INIT|START|RUNNING)|使用训练模型预测完成|预测结果[:：]|成功加载用户.*的模型" "$LOG_PATH" 2>/dev/null; then
      PRED_SEEN=true
      log_info "检测到预测活动（模型加载/预测运行），立即终止应用程序避免无限循环"
      stop_ubm_immediately "$PID" "预测活动检测"
      sleep 2  # 给进程更多时间终止
      break
    fi
    # 备用：检测训练完成
    if grep -qiE "\[SUCCESS\].*模型训练完成|用户.*模型训练完成|模型训练完成|Training completed|Model training finished|开始自动异常检测|自动异常检测已启动" "$LOG_PATH" 2>/dev/null; then
      log_info "检测到模型训练完成或异常检测启动，立即终止应用程序"
      stop_ubm_immediately "$PID" "训练完成检测"
      sleep 2  # 给进程更多时间终止
      break
    fi
  fi
  sleep 1
done

# 时间盒结束后，无论是否检测到，都强制终止所有UBM进程
log_warning "时间盒结束，强制终止所有UBM进程以防止无限循环"
taskkill //IM "UserBehaviorMonitor.exe" //F //T 2>/dev/null || true
taskkill //IM "python.exe" //F //FI "COMMANDLINE eq *UserBehaviorMonitor*" 2>/dev/null || true
pkill -f "UserBehaviorMonitor" 2>/dev/null || true
sleep 2

if [[ -n "$LOG_PATH" ]]; then
    log_info "分析深度学习分类结果..."
    
    # 1. 检查深度学习/预测相关关键字
    PATTERNS=(
      'deep learning' 'neural network' 'classification' 'training' 'model'
      '深度学习' '神经网络' '分类' '训练' '模型'
      'UBM_MARK: FEATURE_DONE' '特征处理完成' '模型训练完成'
      'UBM_MARK: PREDICT_(INIT|START|RUNNING)'
      '使用训练模型预测完成' '预测结果:' '保存了 .* 预测结果到数据库'
    )
    
    TOTAL_HITS=0
    for pattern in "${PATTERNS[@]}"; do
        if grep -q "$pattern" "$LOG_PATH" 2>/dev/null; then
            COUNT=$(grep -c "$pattern" "$LOG_PATH" 2>/dev/null || echo "0")
            TOTAL_HITS=$((TOTAL_HITS + COUNT))
        fi
    done
    
    # 2. 提取具体的性能指标
    log_info "提取分类性能指标..."
    
    # 准确率计算方式：正确预测的样本数 / 总样本数
    ACCURACY=$(grep -o "accuracy[[:space:]]*=[[:space:]]*[0-9.]*" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0")
    ACCURACY_PCT=$(grep -o "准确率[[:space:]]*[0-9.]*%" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0")
    
    # F1-score计算方式：2 * (精确率 * 召回率) / (精确率 + 召回率)
    F1_SCORE=$(grep -o "f1[[:space:]]*=[[:space:]]*[0-9.]*" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0")
    F1_SCORE_PCT=$(grep -o "F1[[:space:]]*[0-9.]*%" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0")
    
    # 召回率计算方式：正确预测为正类的样本数 / 实际正类样本数
    RECALL=$(grep -o "recall[[:space:]]*=[[:space:]]*[0-9.]*" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0")
    RECALL_PCT=$(grep -o "召回率[[:space:]]*[0-9.]*%" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0")
    
    # 精确率计算方式：正确预测为正类的样本数 / 预测为正类的样本数
    PRECISION=$(grep -o "precision[[:space:]]*=[[:space:]]*[0-9.]*" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0")
    PRECISION_PCT=$(grep -o "精确率[[:space:]]*[0-9.]*%" "$LOG_PATH" 2>/dev/null | grep -o "[0-9.]*" | head -1 || echo "0")
    
    # 3. 指标验证（阈值：准确率 ≥ 90%，F1-score ≥ 85%）
    log_info "验证性能指标阈值..."
    
    # 转换为百分比进行比较
    ACCURACY_VAL=${ACCURACY:-$ACCURACY_PCT}
    F1_VAL=${F1_SCORE:-$F1_SCORE_PCT}
    
    # 如果值小于1，转换为百分比
    if [[ $(echo "$ACCURACY_VAL < 1" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        ACCURACY_VAL=$(echo "$ACCURACY_VAL * 100" | bc -l 2>/dev/null || echo "0")
    fi
    
    if [[ $(echo "$F1_VAL < 1" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        F1_VAL=$(echo "$F1_VAL * 100" | bc -l 2>/dev/null || echo "0")
    fi
    
    # 阈值检查
    ACCURACY_OK=false
    F1_OK=false
    
    if [[ $(echo "$ACCURACY_VAL >= 90" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        ACCURACY_OK=true
        log_success "✓ 准确率达标: ${ACCURACY_VAL}% >= 90%"
    else
        log_warning "✗ 准确率未达标: ${ACCURACY_VAL}% < 90%"
    fi
    
    if [[ $(echo "$F1_VAL >= 85" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        F1_OK=true
        log_success "✓ F1-score达标: ${F1_VAL}% >= 85%"
    else
        log_warning "✗ F1-score未达标: ${F1_VAL}% < 85%"
    fi
    
    # 4. 确定测试结论
    if [[ "$ACCURACY_OK" == "true" ]] && [[ "$F1_OK" == "true" ]]; then
        CONCLUSION="Pass"
        log_success "✓ 深度学习分类性能指标全部达标"
    elif [[ "$ACCURACY_OK" == "true" ]] || [[ "$F1_OK" == "true" ]]; then
        CONCLUSION="Partial"
        log_warning "⚠️ 深度学习分类性能指标部分达标"
    else
        CONCLUSION="Fail"
        log_error "✗ 深度学习分类性能指标未达标"
    fi
    
    # 5. 输出详细指标
    log_info "分类性能指标详情:"
    log_info "  准确率 (Accuracy): ${ACCURACY_VAL}% (阈值: ≥90%)"
    log_info "  F1-score: ${F1_VAL}% (阈值: ≥85%)"
    log_info "  召回率 (Recall): ${RECALL:-$RECALL_PCT}%"
    log_info "  精确率 (Precision): ${PRECISION:-$PRECISION_PCT}%"
    
else
    LOG_PATH="no-log-found"
    CONCLUSION="Review"
    log_warning "未找到日志文件"
fi

ARTIFACT=$(save_artifacts "$LOG_PATH" "$BASE_DIR")
ACTUAL="log=$LOG_PATH; artifact=$ARTIFACT"

write_result_row 2 "Check deep learning logs" "Contains classification/training keywords" "$ACTUAL" "$CONCLUSION"

# 进程已在预测检测时终止，这里只需确认
if kill -0 "$PID" 2>/dev/null; then
    log_warning "进程仍在运行，执行最终清理"
    stop_ubm_gracefully "$PID"
else
    log_success "进程已成功终止"
fi

# 清理核弹级终止器
if [[ -n "$NUCLEAR_PID" ]] && kill -0 "$NUCLEAR_PID" 2>/dev/null; then
    log_info "清理核弹级终止器进程: $NUCLEAR_PID"
    kill "$NUCLEAR_PID" 2>/dev/null || true
fi

write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

# 最终安全检查：确保所有UBM进程都被终止
log_warning "最终安全检查：确保所有UBM进程都被终止"
taskkill //IM "UserBehaviorMonitor.exe" //F //T 2>/dev/null || true
taskkill //IM "python.exe" //F //FI "COMMANDLINE eq *behavior*" 2>/dev/null || true
pkill -f "behavior" 2>/dev/null || true

log_success "TC03 深度学习分类测试完成"

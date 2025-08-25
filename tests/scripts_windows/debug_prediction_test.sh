#!/bin/bash
# 调试版预测循环终止测试脚本
# 增加详细的调试输出来诊断问题

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 脚本配置
EXE_PATH="${1:-../../dist/UserBehaviorMonitor.exe}"
WORK_DIR="${2:-./debug_test_run}"
ULTRA_FAST_MODE=true

echo "=== DEBUG: 预测循环终止调试测试 ==="
echo "EXE路径: $EXE_PATH"
echo "工作目录: $WORK_DIR"
echo "调试模式: 详细输出"
echo ""

# 检查EXE文件
if [[ ! -f "$EXE_PATH" ]]; then
    log_error "EXE文件不存在: $EXE_PATH"
    exit 1
fi

# 准备工作目录
WORK_CONFIG=$(prepare_work_dir "$WORK_DIR")
BASE_DIR=$(echo "$WORK_CONFIG" | grep -o '"Base":"[^"]*"' | cut -d'"' -f4)
LOGS_DIR=$(echo "$WORK_CONFIG" | grep -o '"Logs":"[^"]*"' | cut -d'"' -f4)

log_info "DEBUG: 工作目录: $BASE_DIR"
log_info "DEBUG: 日志目录: $LOGS_DIR"

# 启动应用程序
echo ""
echo "[DEBUG STEP 1] 启动应用程序"
echo "----------------------------"
START_TIME=$(date +%s)
PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
log_success "DEBUG: 应用程序已启动，PID: $PID"

# 等待启动
sleep 3

# 触发训练
echo ""
echo "[DEBUG STEP 2] 触发训练"
echo "----------------------"
log_info "DEBUG: 发送 rrrr 快捷键..."
send_char_repeated 'r' 4 100

# 简单用户操作
sleep 2
log_info "DEBUG: 模拟用户操作..."
move_mouse_path 50
click_left_times 2 200

# 调试：检查日志目录
echo ""
echo "[DEBUG STEP 3] 检查日志目录"
echo "---------------------------"
if [[ -d "$LOGS_DIR" ]]; then
    log_info "DEBUG: 日志目录存在"
    LOG_FILES=$(find "$LOGS_DIR" -name "*.log" -type f 2>/dev/null || echo "")
    if [[ -n "$LOG_FILES" ]]; then
        echo "DEBUG: 发现日志文件:"
        echo "$LOG_FILES" | while read -r logfile; do
            echo "  - $logfile ($(wc -l < "$logfile" 2>/dev/null || echo "0") 行)"
        done
    else
        log_warning "DEBUG: 日志目录为空"
    fi
else
    log_error "DEBUG: 日志目录不存在: $LOGS_DIR"
fi

# 调试：等待并检测预测循环
echo ""
echo "[DEBUG STEP 4] 等待预测循环检测"
echo "------------------------------"
DETECTION_TIMEOUT=15
end_ts=$(( $(date +%s) + DETECTION_TIMEOUT ))
PREDICTION_DETECTED=false
DETECTION_ATTEMPTS=0

while [[ $(date +%s) -lt $end_ts ]]; do
    DETECTION_ATTEMPTS=$((DETECTION_ATTEMPTS + 1))
    ELAPSED=$(($(date +%s) - START_TIME))
    
    echo -n "DEBUG: 检测尝试 $DETECTION_ATTEMPTS, 已用时 ${ELAPSED}s..."
    
    LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 3)
    if [[ -n "$LOG_PATH" && -f "$LOG_PATH" ]]; then
        echo " 日志文件: $(basename "$LOG_PATH")"
        
        # 检查文件大小和最后修改时间
        LOG_SIZE=$(wc -l < "$LOG_PATH" 2>/dev/null || echo "0")
        LOG_MTIME=$(stat -c %Y "$LOG_PATH" 2>/dev/null || echo "0")
        echo "DEBUG:   文件大小: ${LOG_SIZE}行, 修改时间: $(date -d @$LOG_MTIME 2>/dev/null || echo "unknown")"
        
        # 显示最后几行日志
        echo "DEBUG: 最后5行日志:"
        tail -5 "$LOG_PATH" 2>/dev/null | while IFS= read -r line; do
            echo "  > $line"
        done
        
        # 检查预测相关标记
        PREDICT_MARKS=$(grep -iE "UBM_MARK.*PREDICT" "$LOG_PATH" 2>/dev/null || echo "")
        if [[ -n "$PREDICT_MARKS" ]]; then
            echo "DEBUG: 发现预测标记:"
            echo "$PREDICT_MARKS" | while IFS= read -r line; do
                echo "  MARK> $line"
            done
        fi
        
        # 检查预测结果
        PREDICT_RESULTS=$(grep -iE "预测结果|使用训练模型预测完成" "$LOG_PATH" 2>/dev/null || echo "")
        if [[ -n "$PREDICT_RESULTS" ]]; then
            echo "DEBUG: 发现预测结果:"
            echo "$PREDICT_RESULTS" | tail -3 | while IFS= read -r line; do
                echo "  RESULT> $line"
            done
        fi
        
        # 执行检测逻辑
        if grep -qiE "UBM_MARK:\s*PREDICT_(INIT|START|RUNNING)|使用训练模型预测完成|预测结果[:：]" "$LOG_PATH" 2>/dev/null; then
            PREDICTION_DETECTED=true
            log_success "DEBUG: 预测循环检测成功！"
            
            # 立即终止
            log_warning "DEBUG: 立即终止应用程序..."
            TERMINATION_START=$(date +%s)
            
            stop_ubm_immediately "$PID" "调试测试"
            
            # 验证终止
            sleep 1
            TERMINATION_END=$(date +%s)
            TERMINATION_TIME=$((TERMINATION_END - TERMINATION_START))
            
            if kill -0 "$PID" 2>/dev/null; then
                log_error "DEBUG: 立即终止失败，进程仍在运行"
                # 强力终止
                stop_ubm_gracefully "$PID"
                if kill -0 "$PID" 2>/dev/null; then
                    log_error "DEBUG: 强力终止也失败"
                else
                    log_warning "DEBUG: 强力终止成功"
                fi
            else
                log_success "DEBUG: 立即终止成功，用时: ${TERMINATION_TIME}秒"
            fi
            
            break
        else
            echo "DEBUG: 未检测到预测循环标记"
        fi
    else
        echo " 未找到日志文件"
    fi
    
    sleep 2
done

# 结果分析
echo ""
echo "[DEBUG RESULTS] 测试结果分析"
echo "=============================="
TOTAL_TIME=$(($(date +%s) - START_TIME))

if [[ "$PREDICTION_DETECTED" == "true" ]]; then
    log_success "DEBUG: 预测循环检测: 成功"
    if ! kill -0 "$PID" 2>/dev/null; then
        log_success "DEBUG: 进程终止: 成功"
        echo "结论: 修复有效！"
        exit_code=0
    else
        log_error "DEBUG: 进程终止: 失败"
        echo "结论: 终止逻辑需要调试"
        exit_code=1
    fi
else
    log_warning "DEBUG: 预测循环检测: 超时"
    echo "可能原因:"
    echo "  1. 应用程序启动缓慢"
    echo "  2. 训练时间过长"
    echo "  3. 日志文件路径问题"
    echo "  4. 正则表达式匹配问题"
    exit_code=1
fi

# 最终清理
if kill -0 "$PID" 2>/dev/null; then
    log_warning "DEBUG: 执行最终清理..."
    stop_ubm_gracefully "$PID"
fi

echo ""
echo "DEBUG: 总测试时间: ${TOTAL_TIME}秒"
echo "DEBUG: 检测尝试次数: $DETECTION_ATTEMPTS"
echo "调试测试完成"

exit $exit_code

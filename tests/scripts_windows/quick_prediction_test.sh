#!/bin/bash
# 快速验证预测循环终止修复的脚本
# 这个脚本专门测试预测循环检测和立即终止功能

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 脚本配置
EXE_PATH="${1:-../../dist/UserBehaviorMonitor.exe}"
WORK_DIR="${2:-./quick_test_run}"
ULTRA_FAST_MODE=true  # 强制使用超快模式

echo "🚀 快速验证预测循环终止修复"
echo "================================"
echo "EXE路径: $EXE_PATH"
echo "工作目录: $WORK_DIR"
echo "模式: 超快验证 (5-10秒)"
echo ""

# 检查EXE文件
if [[ ! -f "$EXE_PATH" ]]; then
    log_error "EXE文件不存在: $EXE_PATH"
    echo "请确保已构建EXE文件，或指定正确路径："
    echo "  bash quick_prediction_test.sh /path/to/UserBehaviorMonitor.exe"
    exit 1
fi

# 准备工作目录
WORK_CONFIG=$(prepare_work_dir "$WORK_DIR")
BASE_DIR=$(echo "$WORK_CONFIG" | grep -o '"Base":"[^"]*"' | cut -d'"' -f4)
LOGS_DIR=$(echo "$WORK_CONFIG" | grep -o '"Logs":"[^"]*"' | cut -d'"' -f4)

log_info "工作目录准备完成: $BASE_DIR"
log_info "日志目录: $LOGS_DIR"

# 测试步骤1: 启动应用程序
echo ""
echo "📋 测试步骤1: 启动应用程序"
echo "------------------------"
START_TIME=$(date +%s)
PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
log_success "✓ 应用程序已启动，PID: $PID"

# 等待应用程序完全启动
echo "等待应用程序完全启动..."
sleep 3

# 测试步骤2: 触发快速数据收集
echo ""
echo "📋 测试步骤2: 触发数据收集和训练"
echo "--------------------------------"
log_info "发送 rrrr 快捷键触发数据收集和训练..."
send_char_repeated 'r' 4 100

# 等待一些基础操作
sleep 2

# 模拟少量用户操作（快速版本）
log_info "模拟少量用户操作..."
move_mouse_path 50
sleep 1
click_left_times 3 200
sleep 1

# 测试步骤3: 等待预测循环开始并立即终止
echo ""
echo "📋 测试步骤3: 检测预测循环并立即终止"
echo "------------------------------------"
log_info "等待预测循环开始（最多等待10秒）..."

DETECTION_TIMEOUT=10
end_ts=$(( $(date +%s) + DETECTION_TIMEOUT ))
LOG_PATH=""
PREDICTION_DETECTED=false

while [[ $(date +%s) -lt $end_ts ]]; do
    LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 5)
    if [[ -n "$LOG_PATH" ]]; then
        # 检查是否出现预测相关日志
        if grep -qiE "UBM_MARK:\s*PREDICT_(INIT|START|RUNNING)|使用训练模型预测完成|预测结果[:：]" "$LOG_PATH" 2>/dev/null; then
            PREDICTION_DETECTED=true
            log_success "✓ 检测到预测循环开始！"
            
            # 记录检测时间
            DETECTION_TIME=$(date +%s)
            TIME_TO_PREDICTION=$((DETECTION_TIME - START_TIME))
            log_info "从启动到预测检测用时: ${TIME_TO_PREDICTION}秒"
            
            # 立即终止应用程序（测试修复）
            log_warning "🛑 立即终止应用程序（测试修复）..."
            TERMINATION_START=$(date +%s)
            
            stop_ubm_immediately "$PID" "快速验证测试"
            
            # 验证终止效果
            sleep 1
            TERMINATION_END=$(date +%s)
            TERMINATION_TIME=$((TERMINATION_END - TERMINATION_START))
            
            if kill -0 "$PID" 2>/dev/null; then
                log_error "❌ 进程仍在运行，立即终止失败！"
                # 尝试强力清理
                stop_ubm_gracefully "$PID"
                if kill -0 "$PID" 2>/dev/null; then
                    log_error "❌ 强力清理也失败，进程无法终止"
                    echo "⚠️  可能需要手动终止进程: $PID"
                    break
                else
                    log_warning "⚠️  立即终止失败，但强力清理成功"
                fi
            else
                log_success "✅ 进程已成功终止！"
                log_info "终止用时: ${TERMINATION_TIME}秒"
            fi
            
            break
        fi
        
        # 显示进度
        ELAPSED=$(($(date +%s) - START_TIME))
        echo -n "⏳ 等待预测循环... ${ELAPSED}/${DETECTION_TIMEOUT}秒\r"
    fi
    sleep 1
done

echo ""  # 换行

# 测试结果分析
echo ""
echo "📊 测试结果分析"
echo "==============="

TOTAL_TIME=$(($(date +%s) - START_TIME))

if [[ "$PREDICTION_DETECTED" == "true" ]]; then
    log_success "🎉 预测循环检测: 成功"
    log_info "  - 检测用时: ${TIME_TO_PREDICTION}秒"
    
    if ! kill -0 "$PID" 2>/dev/null; then
        log_success "🎉 立即终止功能: 成功"
        log_info "  - 终止用时: ${TERMINATION_TIME}秒"
        echo ""
        echo "✅ 修复验证成功！预测循环能够被立即终止，不会导致测试卡住。"
    else
        log_error "❌ 立即终止功能: 失败"
        echo ""
        echo "⚠️  修复可能不完全，需要进一步调试终止逻辑。"
    fi
else
    log_warning "⚠️  预测循环检测: 超时"
    log_info "可能原因："
    log_info "  1. 应用程序启动缓慢"
    log_info "  2. 数据收集时间不足"
    log_info "  3. 模型训练时间较长"
    
    # 尝试清理进程
    if kill -0 "$PID" 2>/dev/null; then
        log_info "清理仍在运行的进程..."
        stop_ubm_gracefully "$PID"
    fi
    
    echo ""
    echo "🔄 建议尝试："
    echo "  1. 延长检测超时时间"
    echo "  2. 检查应用程序日志"
    echo "  3. 确保有足够的系统资源"
fi

echo ""
echo "📁 日志文件位置:"
if [[ -n "$LOG_PATH" && -f "$LOG_PATH" ]]; then
    echo "  $LOG_PATH"
    
    # 显示最后几行日志
    echo ""
    echo "📝 最新日志内容 (最后10行):"
    echo "----------------------------"
    tail -10 "$LOG_PATH" 2>/dev/null || echo "无法读取日志文件"
else
    echo "  未找到日志文件"
fi

echo ""
echo "⏱️  总测试时间: ${TOTAL_TIME}秒"
echo "🏁 快速验证测试完成"

# 最终清理确认
if kill -0 "$PID" 2>/dev/null; then
    log_warning "进程仍在运行，执行最终清理..."
    stop_ubm_gracefully "$PID"
fi

echo ""
if [[ "$PREDICTION_DETECTED" == "true" ]] && ! kill -0 "$PID" 2>/dev/null; then
    echo "🎯 结论: 修复有效，可以进行完整测试！"
    exit 0
else
    echo "🔧 结论: 需要进一步调试"
    exit 1
fi

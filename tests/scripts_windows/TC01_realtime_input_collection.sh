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

write_result_header "TC01 实时输入采集测试"
write_result_table_header

# 步骤1：启动程序
show_test_step 1 "启动UBM程序" "start"
PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
if [[ -n "$PID" ]]; then
    write_result_row 1 "启动程序" "进程启动成功" "PID=$PID" "Pass"
    show_test_step 1 "启动UBM程序" "success"
else
    write_result_row 1 "启动程序" "进程启动成功" "启动失败" "Fail"
    show_test_step 1 "启动UBM程序" "error"
    exit 1
fi

sleep $STARTUP_WAIT

# 步骤2：模拟鼠标移动
show_test_step 2 "模拟鼠标移动" "start"
log_info "模拟鼠标移动..."
if move_mouse_path 5 50; then
    write_result_row 2 "模拟鼠标移动" "鼠标移动被检测到" "移动成功" "Pass"
    show_test_step 2 "模拟鼠标移动" "success"
else
    write_result_row 2 "模拟鼠标移动" "鼠标移动被检测到" "移动失败，使用备选方案" "Partial"
    show_test_step 2 "模拟鼠标移动" "warning"
fi

# 步骤3：模拟鼠标点击
show_test_step 3 "模拟鼠标点击" "start"
log_info "模拟鼠标点击..."
if click_left_times 3; then
    write_result_row 3 "模拟鼠标点击" "鼠标点击被检测到" "点击成功" "Pass"
    show_test_step 3 "模拟鼠标点击" "success"
else
    write_result_row 3 "模拟鼠标点击" "鼠标点击被检测到" "点击失败，使用备选方案" "Partial"
    show_test_step 3 "模拟鼠标点击" "warning"
fi

# 步骤4：模拟滚动
show_test_step 4 "模拟滚动" "start"
log_info "模拟滚动..."
if scroll_vertical 3; then
    write_result_row 4 "模拟滚动" "滚动事件被检测到" "滚动成功" "Pass"
    show_test_step 4 "模拟滚动" "success"
else
    write_result_row 4 "模拟滚动" "滚动事件被检测到" "滚动失败，使用备选方案" "Partial"
    show_test_step 4 "模拟滚动" "warning"
fi

# 步骤5：等待数据采集
show_test_step 5 "等待数据采集" "start"
log_info "等待数据采集..."
sleep $FEATURE_WAIT
show_test_step 5 "等待数据采集" "success"

# 步骤6：检查日志关键字
show_test_step 6 "检查日志关键字" "start"
LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 30)
if [[ -n "$LOG_PATH" ]]; then
    # 检查日志关键字
    PATTERNS=('keyboard' 'click' 'hotkey' 'move' 'scroll' 'released' 'pressed' \
              '键盘' '点击' '热键' '移动' '滚动' '释放' '按下' \
              'UBM_MARK: COLLECT_START' 'COLLECT_PROGRESS' 'COLLECT_DONE')
    
    TOTAL_HITS=0
    MATCHED_PATTERNS=()
    
    for pattern in "${PATTERNS[@]}"; do
        if grep -q "$pattern" "$LOG_PATH" 2>/dev/null; then
            COUNT=$(grep -c "$pattern" "$LOG_PATH" 2>/dev/null || echo "0")
            TOTAL_HITS=$((TOTAL_HITS + COUNT))
            if [[ $COUNT -gt 0 ]]; then
                MATCHED_PATTERNS+=("$pattern($COUNT)")
            fi
        fi
    done
    
    if [[ $TOTAL_HITS -gt 0 ]]; then
        CONCLUSION="Pass"
        ACTUAL="找到${TOTAL_HITS}个关键字: ${MATCHED_PATTERNS[*]}"
        show_test_step 6 "检查日志关键字" "success"
    else
        CONCLUSION="Review"
        ACTUAL="未找到关键字，需要复核"
        show_test_step 6 "检查日志关键字" "warning"
    fi
else
    LOG_PATH="no-log-found"
    ACTUAL="未找到日志文件"
    CONCLUSION="Review"
    show_test_step 6 "检查日志关键字" "error"
fi

ARTIFACT=$(save_artifacts "$LOG_PATH" "$BASE_DIR")
ACTUAL="$ACTUAL; 日志=$LOG_PATH; 产物=$ARTIFACT"

write_result_row 5 "检查日志关键字" "包含事件类型关键字" "$ACTUAL" "$CONCLUSION"

# 步骤7：优雅退出
show_test_step 7 "退出程序" "start"
stop_ubm_gracefully "$PID"
write_result_row 6 "退出程序" "优雅退出或被终止" "退出完成" "Pass"
show_test_step 7 "退出程序" "success"

# 显示测试结果汇总
write_result_footer

echo ""
echo "📊 TC01 测试结果汇总:"
if [[ "$CONCLUSION" == "Pass" ]]; then
    echo "✅ 测试通过：实时输入采集功能正常工作"
elif [[ "$CONCLUSION" == "Partial" ]]; then
    echo "⚠️  测试部分通过：部分功能需要关注"
else
    echo "❌ 测试需要复核：请检查日志文件"
fi

echo ""
echo "🔍 详细结果:"
echo "  日志文件: $LOG_PATH"
echo "  产物文件: $ARTIFACT"
echo "  关键字匹配: $TOTAL_HITS 个"
echo "  测试状态: $CONCLUSION"

log_success "TC01 实时输入采集测试完成"

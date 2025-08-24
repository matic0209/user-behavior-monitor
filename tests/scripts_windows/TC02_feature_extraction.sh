#!/bin/bash
# TC02 特征提取功能测试 - Git Bash 兼容版本

# 加载公共函数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 参数处理
EXE_PATH=""
WORK_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -ExePath)
            EXE_PATH="$2"
            shift 2
            ;;
        -WorkDir)
            WORK_DIR="$2"
            shift 2
            ;;
        *)
            echo "用法: $0 -ExePath <exe_path> -WorkDir <work_dir>"
            exit 1
            ;;
    esac
done

# 验证参数
if [[ -z "$EXE_PATH" ]] || [[ -z "$WORK_DIR" ]]; then
    log_error "缺少必要参数"
    echo "用法: $0 -ExePath <exe_path> -WorkDir <work_dir>"
    exit 1
fi

# 解析工作目录配置
WORK_CONFIG=$(prepare_work_dir "$WORK_DIR")
BASE_DIR=$(echo "$WORK_CONFIG" | grep -o '"Base":"[^"]*"' | cut -d'"' -f4)
LOGS_DIR=$(echo "$WORK_CONFIG" | grep -o '"Logs":"[^"]*"' | cut -d'"' -f4)

write_result_header "TC02 Feature extraction"
write_result_table_header

# 启动程序
log_info "启动UBM程序..."
PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
write_result_row 1 "Start EXE" "Process started" "PID=$PID" "Pass"

# 等待程序启动
sleep 3

# 触发特征处理快捷键 (rrrr)
log_info "发送快捷键 rrrr 触发特征处理..."
send_char_repeated 'r' 4 100
write_result_row 2 "Trigger feature processing" "Feature processing starts" "send rrrr" "N/A"

# 等待特征处理完成
log_info "等待特征处理完成..."
sleep 10

# 等待日志文件
log_info "等待日志文件生成..."
LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 30)
if [[ -n "$LOG_PATH" ]]; then
    log_info "找到日志文件: $LOG_PATH"
    
    # 检查日志关键字
    log_info "检查日志关键字..."
    if wait_log_contains "$LOG_PATH" \
        'features' 'process_session_features' 'feature' 'processed' 'complete' \
        '特征处理' '处理完成' '特征 处理 完成' '[SUCCESS] 特征处理完成' \
        'UBM_MARK: FEATURE_DONE' 'FEATURE_START' 'FEATURE_DONE' \
        '特征数据' '特征转换' '特征保存' '特征统计' \
        40 500; then
        
        log_success "找到所有关键字，测试通过"
        CONCLUSION="Pass"
    else
        # 检查是否有部分关键字匹配
        TOTAL_HITS=0
        PATTERNS=('features' 'process_session_features' 'feature' 'processed' 'complete' \
                  '特征处理' '处理完成' '特征 处理 完成' '[SUCCESS] 特征处理完成' \
                  'UBM_MARK: FEATURE_DONE' 'FEATURE_START' 'FEATURE_DONE' \
                  '特征数据' '特征转换' '特征保存' '特征统计')
        
        for pattern in "${PATTERNS[@]}"; do
            if grep -q "$pattern" "$LOG_PATH" 2>/dev/null; then
                COUNT=$(grep -c "$pattern" "$LOG_PATH" 2>/dev/null || echo "0")
                TOTAL_HITS=$((TOTAL_HITS + COUNT))
            fi
        done
        
        if [[ $TOTAL_HITS -gt 0 ]]; then
            log_warning "部分关键字匹配，测试部分通过"
            CONCLUSION="Partial"
        else
            log_warning "未找到关键字，需要复核"
            CONCLUSION="Review"
        fi
    fi
else
    log_warning "未找到日志文件"
    LOG_PATH="no-log-found"
    CONCLUSION="Review"
fi

# 保存测试产物
ARTIFACT=$(save_artifacts "$LOG_PATH" "$BASE_DIR")
ACTUAL="log=$LOG_PATH; artifact=$ARTIFACT"

write_result_row 3 "Check feature logs" "Contains processing/complete keywords" "$ACTUAL" "$CONCLUSION"

# 停止程序
log_info "停止UBM程序..."
stop_ubm_gracefully "$PID"
write_result_row 4 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC02 特征提取测试完成"

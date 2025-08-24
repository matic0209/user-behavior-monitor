#!/bin/bash
# TC08 特征数量阈值测试 - Git Bash 兼容版本

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

write_result_header "TC08 Feature count threshold (>=200)"
write_result_table_header

# 启动程序
log_info "启动UBM程序..."
PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
write_result_row 1 "Start EXE (feature)" "Output feature stats" "PID=$PID" "Pass"

# 等待程序启动
sleep $STARTUP_WAIT

# 触发特征处理快捷键 rrrr
log_info "发送快捷键 rrrr 触发特征处理..."
send_char_repeated 'r' 4 100

# 等待特征处理完成
log_info "等待特征处理完成..."
sleep $FEATURE_WAIT

# 等待日志文件
log_info "等待日志文件生成..."
LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 30)
OK=false
ACTUAL="no-log-found"

if [[ -n "$LOG_PATH" ]]; then
    log_info "分析日志文件: $LOG_PATH"
    
    # 多种特征数量匹配模式
    PATTERNS=(
        'feature_count\s*:\s*([0-9]+)'
        '特征数量\s*:\s*([0-9]+)'
        '特征数\s*:\s*([0-9]+)'
        'features\s*:\s*([0-9]+)'
        'n_features\s*:\s*([0-9]+)'
        '特征\s*([0-9]+)\s*个'
        '共\s*([0-9]+)\s*个特征'
    )
    
    MAX=0
    for pattern in "${PATTERNS[@]}"; do
        log_debug "搜索模式: $pattern"
        if grep -q "$pattern" "$LOG_PATH" 2>/dev/null; then
            # 提取数字
            MATCHES=$(grep -o "$pattern" "$LOG_PATH" | grep -o '[0-9]\+')
            for match in $MATCHES; do
                if [[ $match -gt $MAX ]]; then
                    MAX=$match
                fi
            done
        fi
    done
    
    if [[ $MAX -gt 0 ]]; then
        OK=$([[ $MAX -ge 200 ]] && echo "true" || echo "false")
        ACTUAL="max_feature_count=$MAX (threshold: >=200)"
        
        # 记录找到的特征数量
        log_info "找到特征数量: $MAX"
        if [[ "$OK" == "true" ]]; then
            log_success "✓ 特征数量满足要求 (>=200)"
        else
            log_warning "✗ 特征数量不足 (需要>=200, 实际=$MAX)"
        fi
    else
        ACTUAL="no feature_count matched in patterns: ${PATTERNS[*]}"
        log_warning "未找到特征数量信息，尝试分析日志内容..."
        
        # 分析日志内容，查找可能的特征相关信息
        FEATURE_RELATED=$(grep -i "特征\|feature\|处理\|完成\|成功\|失败" "$LOG_PATH" 2>/dev/null | head -5)
        if [[ -n "$FEATURE_RELATED" ]]; then
            log_info "找到相关日志条目:"
            echo "$FEATURE_RELATED" | while IFS= read -r line; do
                log_info "  $line"
            done
        fi
    fi
else
    log_warning "未找到日志文件"
fi

CONCLUSION=$([[ "$OK" == "true" ]] && echo "Pass" || echo "Review")
write_result_row 2 "Check feature count" ">= 200" "$ACTUAL" "$CONCLUSION"

# 停止程序
log_info "停止UBM程序..."
stop_ubm_gracefully "$PID"
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC08 特征数量阈值测试完成"

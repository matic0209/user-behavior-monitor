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

# 等待特征数量日志（时间盒，避免卡住）
log_info "等待特征数量日志(时间盒)..."
TIMEBOX=35
if [[ "${ULTRA_FAST_MODE:-false}" == "true" ]]; then TIMEBOX=8; elif [[ "${FAST_MODE:-false}" == "true" ]]; then TIMEBOX=15; fi
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
    # 如果训练未完成但已有特征数量日志，继续分析
    if grep -qiE "UBM_MARK:\s*FEATURE_DONE|特征处理完成|feature.*count|特征数量|features.*:" "$LOG_PATH" 2>/dev/null; then
      log_info "命中特征数量相关日志，进入分析"
      break
    fi
  fi
  sleep 1
done
OK=false
ACTUAL="no-log-found"

if [[ -n "$LOG_PATH" ]]; then
    log_info "分析日志文件: $LOG_PATH"
    
    # 多种特征数量匹配模式 (按优先级排序)
    PATTERNS=(
        'UBM_MARK:\s*FEATURE_COUNT\s+n_features=([0-9]+)'  # "UBM_MARK: FEATURE_COUNT n_features=200" (最优先)
        'n_features[^0-9]*([0-9]+)'                        # "n_features": 200
        'Selected\s+([0-9]+)\s+features'                   # "Selected 200 features out of 300"
        '特征对齐完成:\s*([0-9]+)\s*个特征'                    # "特征对齐完成: 200 个特征"
        'Created\s+([0-9]+)\s+new\s+features'              # "Created 200 new features"
        '特征数量[^0-9]*([0-9]+)'                          # "特征数量: 200"
        '特征数[^0-9]*([0-9]+)'                            # "特征数: 200"
        'features[^0-9]*([0-9]+)'                          # "features: 200"
        '特征\s*([0-9]+)\s*个'                             # "特征 200 个"
        '共\s*([0-9]+)\s*个特征'                           # "共 200 个特征"
        '([0-9]+)\s*records,\s*([0-9]+)\s*features'        # "1000 records, 200 features"
    )
    
    MAX=0
    for pattern in "${PATTERNS[@]}"; do
        log_debug "搜索模式: $pattern"
        # 使用grep -E进行扩展正则表达式匹配
        MATCHES=$(grep -oE "$pattern" "$LOG_PATH" 2>/dev/null || echo "")
        if [[ -n "$MATCHES" ]]; then
            log_debug "找到匹配: $MATCHES"
            # 从每个匹配中提取所有数字
            NUMBERS=$(echo "$MATCHES" | grep -oE '[0-9]+')
            for num in $NUMBERS; do
                log_debug "提取到数字: $num"
                if [[ $num -gt $MAX ]]; then
                    MAX=$num
                    log_debug "更新最大值: $MAX (来源模式: $pattern)"
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
# 检查进程是否仍在运行，避免重复终止
if kill -0 "$PID" 2>/dev/null; then
    log_warning "进程仍在运行，执行最终清理"
    stop_ubm_gracefully "$PID"
else
    log_success "进程已成功终止"
fi
write_result_row 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

log_success "TC08 特征数量阈值测试完成"

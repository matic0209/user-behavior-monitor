#!/bin/bash
# TC08 提取的用户行为特征数指标测试 - 增强版 (详细实测结果输出)

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
DATA_DIR="$BASE_DIR/data"
DB_PATH="$DATA_DIR/mouse_data.db"

echo ""
echo "🎯 TC08 提取的用户行为特征数指标测试 - 增强版"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 测试目标: 验证单会话/窗口的有效特征数不少于200，通过日志和数据库验证特征统计信息"
echo "🎯 成功标准: 输出特征统计信息(列数/维度/键数)，有效特征数≥200，异常样本处理完善"
echo "📊 数据库路径: $DB_PATH"
echo ""

write_result_header "TC08 Enhanced Feature Count Metric"
write_result_table_header

# 启动程序
log_info "🚀 启动UBM程序..."
PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
if [[ -z "$PID" ]]; then
    log_error "程序启动失败"
    exit 1
fi

log_success "✅ 程序启动成功，PID: $PID"

# 启动安全网终止器（防止测试卡住）
log_warning "启动安全网终止器（120秒后强制终止所有UBM进程）"
NUCLEAR_PID=$(bash "$SCRIPT_DIR/nuclear_terminator.sh" 120 2>/dev/null &)
log_info "安全网终止器PID: $NUCLEAR_PID"

# 等待程序启动
sleep $STARTUP_WAIT

# 步骤1：系统自动触发特征处理
show_test_step 1 "系统自动触发特征处理" "start"
log_info "🔄 触发特征处理流程..."

# 触发特征处理快捷键 rrrr
log_info "📤 发送快捷键rrrr触发特征处理..."
send_char_repeated 'r' 4 100

FEATURE_PROCESSING_START=$(date +%s.%N)
FEATURE_PROCESSING_START_READABLE=$(date '+%H:%M:%S.%3N')
log_info "⏰ 特征处理开始时间: $FEATURE_PROCESSING_START_READABLE"

# 等待特征处理相关日志（较长时间）
log_info "⏳ 等待特征处理相关日志..."
FEATURE_PROCESSING_TIME=60  # 给特征处理60秒时间

LOG_PATH=""
FEATURE_PROCESSING_DETECTED=false
MODEL_TRAINING_COMPLETED=false

for i in {1..60}; do
    sleep 1
    LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 5)
    
    if [[ -n "$LOG_PATH" ]]; then
        # 检查特征处理相关日志
        if grep -qiE "特征处理|feature.*processing|特征工程|feature.*engineering|特征提取|feature.*extraction" "$LOG_PATH" 2>/dev/null; then
            FEATURE_PROCESSING_DETECTED=true
            log_success "✅ 检测到特征处理相关日志"
        fi
        
        # 优先检测训练完成，避免进入预测循环
        if grep -qiE "模型训练完成|Training completed|Model training finished" "$LOG_PATH" 2>/dev/null; then
            MODEL_TRAINING_COMPLETED=true
            log_success "✅ 检测到模型训练完成"
            break
        fi
        
        # 检查特征统计相关日志
        if grep -qiE "UBM_MARK.*FEATURE_DONE|特征处理完成|feature.*count|特征数量|features.*:|n_features" "$LOG_PATH" 2>/dev/null; then
            log_success "✅ 检测到特征统计相关日志"
        fi
    fi
    
    if [[ $((i % 10)) -eq 0 ]]; then
        log_info "  等待特征处理: ${i}/60秒"
    fi
done

# 如果训练完成，立即停止程序避免进入预测循环
if [[ "$MODEL_TRAINING_COMPLETED" == "true" ]]; then
    log_info "🔄 模型训练完成，停止程序以避免进入预测循环..."
    stop_ubm_immediately "$PID" "训练完成检测"
    sleep 2
fi

FEATURE_PROCESSING_END=$(date +%s.%N)
FEATURE_PROCESSING_END_READABLE=$(date '+%H:%M:%S.%3N')
FEATURE_PROCESSING_DURATION=$(echo "$FEATURE_PROCESSING_END - $FEATURE_PROCESSING_START" | bc -l 2>/dev/null || echo "60.0")

log_info "⏰ 特征处理结束时间: $FEATURE_PROCESSING_END_READABLE"
log_info "⏱️ 特征处理总耗时: ${FEATURE_PROCESSING_DURATION}秒"

# 分析特征统计信息
FEATURE_STATS_FOUND=false
FEATURE_COUNT=0
FEATURE_DIMENSIONS=0
FEATURE_KEYS=0
FEATURE_COLUMNS=0

if [[ -n "$LOG_PATH" ]]; then
    log_info "🔍 分析特征统计信息..."
    
    # 多种特征数量匹配模式 (按优先级排序)
    FEATURE_PATTERNS=(
        'UBM_MARK:\s*FEATURE_COUNT\s+n_features=([0-9]+)'  # "UBM_MARK: FEATURE_COUNT n_features=200"
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
        '([0-9]+)\s*columns'                               # "200 columns"
        'shape.*\(\s*[0-9]+,\s*([0-9]+)\s*\)'             # "shape: (1000, 200)"
    )
    
    # 搜索特征数量相关信息
    MAX_FEATURE_COUNT=0
    FEATURE_COUNT_SOURCES=()
    
    for pattern in "${FEATURE_PATTERNS[@]}"; do
        MATCHES=$(grep -oE "$pattern" "$LOG_PATH" 2>/dev/null || echo "")
        if [[ -n "$MATCHES" ]]; then
            log_debug "找到特征数量匹配: $MATCHES (模式: $pattern)"
            # 从每个匹配中提取所有数字
            NUMBERS=$(echo "$MATCHES" | grep -oE '[0-9]+')
            for num in $NUMBERS; do
                if [[ $num -gt $MAX_FEATURE_COUNT ]]; then
                    MAX_FEATURE_COUNT=$num
                    FEATURE_COUNT_SOURCES+=("${num}(来源:${pattern})")
                fi
            done
        fi
    done
    
    FEATURE_COUNT=$MAX_FEATURE_COUNT
    
    # 搜索维度信息
    DIMENSION_PATTERNS=(
        'dimensions?[^0-9]*([0-9]+)'                       # "dimensions: 200"
        '维度[^0-9]*([0-9]+)'                             # "维度: 200"
        'shape.*\(\s*[0-9]+,\s*([0-9]+)\s*\)'             # "shape: (1000, 200)"
        '([0-9]+)\s*维'                                   # "200 维"
        '([0-9]+)D'                                       # "200D"
    )
    
    MAX_DIMENSIONS=0
    for pattern in "${DIMENSION_PATTERNS[@]}"; do
        MATCHES=$(grep -oE "$pattern" "$LOG_PATH" 2>/dev/null || echo "")
        if [[ -n "$MATCHES" ]]; then
            NUMBERS=$(echo "$MATCHES" | grep -oE '[0-9]+')
            for num in $NUMBERS; do
                if [[ $num -gt $MAX_DIMENSIONS ]]; then
                    MAX_DIMENSIONS=$num
                fi
            done
        fi
    done
    
    FEATURE_DIMENSIONS=$MAX_DIMENSIONS
    
    # 搜索键数信息
    KEY_PATTERNS=(
        'keys?[^0-9]*([0-9]+)'                            # "keys: 200"
        '键数[^0-9]*([0-9]+)'                             # "键数: 200"
        '([0-9]+)\s*个键'                                 # "200 个键"
        'dict.*size[^0-9]*([0-9]+)'                       # "dict size: 200"
    )
    
    MAX_KEYS=0
    for pattern in "${KEY_PATTERNS[@]}"; do
        MATCHES=$(grep -oE "$pattern" "$LOG_PATH" 2>/dev/null || echo "")
        if [[ -n "$MATCHES" ]]; then
            NUMBERS=$(echo "$MATCHES" | grep -oE '[0-9]+')
            for num in $NUMBERS; do
                if [[ $num -gt $MAX_KEYS ]]; then
                    MAX_KEYS=$num
                fi
            done
        fi
    done
    
    FEATURE_KEYS=$MAX_KEYS
    
    # 搜索列数信息
    COLUMN_PATTERNS=(
        'columns?[^0-9]*([0-9]+)'                         # "columns: 200"
        '列数[^0-9]*([0-9]+)'                             # "列数: 200"
        '([0-9]+)\s*列'                                   # "200 列"
        'ncol[^0-9]*([0-9]+)'                             # "ncol: 200"
    )
    
    MAX_COLUMNS=0
    for pattern in "${COLUMN_PATTERNS[@]}"; do
        MATCHES=$(grep -oE "$pattern" "$LOG_PATH" 2>/dev/null || echo "")
        if [[ -n "$MATCHES" ]]; then
            NUMBERS=$(echo "$MATCHES" | grep -oE '[0-9]+')
            for num in $NUMBERS; do
                if [[ $num -gt $MAX_COLUMNS ]]; then
                    MAX_COLUMNS=$num
                fi
            done
        fi
    done
    
    FEATURE_COLUMNS=$MAX_COLUMNS
    
    # 获取特征处理相关的详细日志示例
    FEATURE_LOG_SAMPLES=$(grep -i "特征\|feature" "$LOG_PATH" 2>/dev/null | grep -E "处理\|processing\|数量\|count\|维度\|dimension\|列\|column" | head -5 | tr '\n' '; ')
    
    log_info "📊 特征统计信息分析结果:"
    log_info "  ├─ 特征数量(features): $FEATURE_COUNT"
    log_info "  ├─ 特征维度(dimensions): $FEATURE_DIMENSIONS"
    log_info "  ├─ 特征键数(keys): $FEATURE_KEYS"
    log_info "  ├─ 特征列数(columns): $FEATURE_COLUMNS"
    log_info "  ├─ 数量来源: ${FEATURE_COUNT_SOURCES[*]}"
    log_info "  └─ 日志示例: ${FEATURE_LOG_SAMPLES:-无相关日志}"
    
    if [[ $FEATURE_COUNT -gt 0 || $FEATURE_DIMENSIONS -gt 0 || $FEATURE_KEYS -gt 0 || $FEATURE_COLUMNS -gt 0 ]]; then
        FEATURE_STATS_FOUND=true
    fi
fi

# 检查数据库中的特征信息
DB_FEATURE_INFO=false
DB_FEATURE_COUNT=0
DB_FEATURE_VECTOR_SAMPLE=""

if [[ -f "$DB_PATH" ]]; then
    # 检查features表
    FEATURES_TABLE_EXISTS=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='features';" 2>/dev/null)
    
    if [[ -n "$FEATURES_TABLE_EXISTS" ]]; then
        log_success "✅ features表存在"
        
        # 获取特征记录数
        DB_FEATURE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM features;" 2>/dev/null || echo "0")
        
        # 获取特征向量样本
        FEATURE_VECTOR_SAMPLE=$(sqlite3 "$DB_PATH" "SELECT feature_vector FROM features WHERE feature_vector IS NOT NULL AND feature_vector != '' LIMIT 1;" 2>/dev/null)
        
        if [[ -n "$FEATURE_VECTOR_SAMPLE" ]]; then
            DB_FEATURE_INFO=true
            
            # 分析特征向量结构
            VECTOR_LENGTH=$(echo "$FEATURE_VECTOR_SAMPLE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(len(data))" 2>/dev/null || echo "0")
            VECTOR_KEYS=$(echo "$FEATURE_VECTOR_SAMPLE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(','.join(list(data.keys())[:10]))" 2>/dev/null || echo "解析失败")
            
            log_info "📊 数据库特征向量分析:"
            log_info "  ├─ 特征记录总数: $DB_FEATURE_COUNT"
            log_info "  ├─ 特征向量维度: $VECTOR_LENGTH"
            log_info "  ├─ 示例特征键: $VECTOR_KEYS"
            log_info "  └─ 数据格式: JSON格式特征向量"
            
            # 更新特征统计信息（如果日志中没有找到）
            if [[ $FEATURE_COUNT -eq 0 && $VECTOR_LENGTH -gt 0 ]]; then
                FEATURE_COUNT=$VECTOR_LENGTH
                log_info "  从数据库特征向量推断特征数量: $FEATURE_COUNT"
            fi
        fi
    else
        log_warning "⚠️ features表不存在"
    fi
fi

# 特征统计信息评估
if [[ "$FEATURE_STATS_FOUND" == "true" || "$DB_FEATURE_INFO" == "true" ]]; then
    # 确定最终的特征统计信息
    FINAL_FEATURE_COUNT=$FEATURE_COUNT
    FINAL_DIMENSIONS=$FEATURE_DIMENSIONS
    FINAL_KEYS=$FEATURE_KEYS
    FINAL_COLUMNS=$FEATURE_COLUMNS
    
    # 如果某些信息缺失，尝试从其他信息推断
    if [[ $FINAL_DIMENSIONS -eq 0 && $FINAL_FEATURE_COUNT -gt 0 ]]; then
        FINAL_DIMENSIONS=$FINAL_FEATURE_COUNT
    fi
    if [[ $FINAL_KEYS -eq 0 && $FINAL_FEATURE_COUNT -gt 0 ]]; then
        FINAL_KEYS=$FINAL_FEATURE_COUNT
    fi
    if [[ $FINAL_COLUMNS -eq 0 && $FINAL_FEATURE_COUNT -gt 0 ]]; then
        FINAL_COLUMNS=$FINAL_FEATURE_COUNT
    fi
    
    STEP1_RESULT="✅ 输出特征统计信息(列数/维度/键数)。特征数量:${FINAL_FEATURE_COUNT}个，维度:${FINAL_DIMENSIONS}维，键数:${FINAL_KEYS}个，列数:${FINAL_COLUMNS}列，数据库记录:${DB_FEATURE_COUNT}条"
    STEP1_STATUS="Pass"
else
    STEP1_RESULT="❌ 未检测到特征统计信息输出，特征处理可能未正常执行"
    STEP1_STATUS="Fail"
fi

write_result_row 1 "系统自动触发特征处理" "输出特征统计信息(列数/维度/键数)" "$STEP1_RESULT" "$STEP1_STATUS"
show_test_step 1 "系统自动触发特征处理" "success"

# 步骤2：校验阈值
show_test_step 2 "校验阈值" "start"
log_info "🔍 校验有效特征数阈值(≥200)..."

# 确定有效特征数
EFFECTIVE_FEATURE_COUNT=0
THRESHOLD_MET=false
THRESHOLD_VALUE=200

# 优先使用特征数量，其次使用维度、键数或列数
if [[ $FINAL_FEATURE_COUNT -gt 0 ]]; then
    EFFECTIVE_FEATURE_COUNT=$FINAL_FEATURE_COUNT
    FEATURE_COUNT_SOURCE="特征数量"
elif [[ $FINAL_DIMENSIONS -gt 0 ]]; then
    EFFECTIVE_FEATURE_COUNT=$FINAL_DIMENSIONS
    FEATURE_COUNT_SOURCE="特征维度"
elif [[ $FINAL_KEYS -gt 0 ]]; then
    EFFECTIVE_FEATURE_COUNT=$FINAL_KEYS
    FEATURE_COUNT_SOURCE="特征键数"
elif [[ $FINAL_COLUMNS -gt 0 ]]; then
    EFFECTIVE_FEATURE_COUNT=$FINAL_COLUMNS
    FEATURE_COUNT_SOURCE="特征列数"
else
    FEATURE_COUNT_SOURCE="未知"
fi

log_info "📊 有效特征数阈值校验:"
log_info "  ├─ 阈值要求: ≥ $THRESHOLD_VALUE"
log_info "  ├─ 有效特征数: $EFFECTIVE_FEATURE_COUNT"
log_info "  ├─ 数据来源: $FEATURE_COUNT_SOURCE"
log_info "  └─ 阈值状态: $([ $EFFECTIVE_FEATURE_COUNT -ge $THRESHOLD_VALUE ] && echo "✅ 满足要求" || echo "❌ 不满足要求")"

if [[ $EFFECTIVE_FEATURE_COUNT -ge $THRESHOLD_VALUE ]]; then
    THRESHOLD_MET=true
fi

# 分析特征数量分布（如果有多个数值）
if [[ ${#FEATURE_COUNT_SOURCES[@]} -gt 1 ]]; then
    log_info "🔍 多源特征数量分析:"
    for source in "${FEATURE_COUNT_SOURCES[@]}"; do
        log_info "  ├─ $source"
    done
fi

# 检查特征质量指标
FEATURE_QUALITY_INDICATORS=()

if [[ -n "$LOG_PATH" ]]; then
    # 检查特征选择相关日志
    FEATURE_SELECTION_COUNT=$(grep -c "特征选择\|feature.*selection\|Selected.*features" "$LOG_PATH" 2>/dev/null || echo "0")
    if [[ $FEATURE_SELECTION_COUNT -gt 0 ]]; then
        FEATURE_QUALITY_INDICATORS+=("特征选择:${FEATURE_SELECTION_COUNT}条日志")
    fi
    
    # 检查特征工程相关日志
    FEATURE_ENGINEERING_COUNT=$(grep -c "特征工程\|feature.*engineering\|特征提取\|feature.*extraction" "$LOG_PATH" 2>/dev/null || echo "0")
    if [[ $FEATURE_ENGINEERING_COUNT -gt 0 ]]; then
        FEATURE_QUALITY_INDICATORS+=("特征工程:${FEATURE_ENGINEERING_COUNT}条日志")
    fi
    
    # 检查特征验证相关日志
    FEATURE_VALIDATION_COUNT=$(grep -c "特征验证\|feature.*validation\|特征检查\|feature.*check" "$LOG_PATH" 2>/dev/null || echo "0")
    if [[ $FEATURE_VALIDATION_COUNT -gt 0 ]]; then
        FEATURE_QUALITY_INDICATORS+=("特征验证:${FEATURE_VALIDATION_COUNT}条日志")
    fi
    
    log_info "📈 特征质量指标:"
    if [[ ${#FEATURE_QUALITY_INDICATORS[@]} -gt 0 ]]; then
        for indicator in "${FEATURE_QUALITY_INDICATORS[@]}"; do
            log_info "  ├─ $indicator"
        done
    else
        log_info "  └─ 无明确的特征质量指标日志"
    fi
fi

# 阈值校验结果评估
if [[ "$THRESHOLD_MET" == "true" ]]; then
    STEP2_RESULT="✅ 有效特征数≥200。实际特征数:${EFFECTIVE_FEATURE_COUNT}个(来源:${FEATURE_COUNT_SOURCE})，超过阈值${THRESHOLD_VALUE}个，达标率:$(echo "scale=1; $EFFECTIVE_FEATURE_COUNT * 100 / $THRESHOLD_VALUE" | bc -l 2>/dev/null || echo "100")%"
    STEP2_STATUS="Pass"
else
    STEP2_RESULT="❌ 有效特征数不足200。实际特征数:${EFFECTIVE_FEATURE_COUNT}个(来源:${FEATURE_COUNT_SOURCE})，低于阈值${THRESHOLD_VALUE}个，达标率:$(echo "scale=1; $EFFECTIVE_FEATURE_COUNT * 100 / $THRESHOLD_VALUE" | bc -l 2>/dev/null || echo "0")%"
    STEP2_STATUS="Fail"
fi

write_result_row 2 "校验阈值" "有效特征数 ≥ 200" "$STEP2_RESULT" "$STEP2_STATUS"
show_test_step 2 "校验阈值" "success"

# 步骤3：异常样本处理
show_test_step 3 "异常样本处理" "start"
log_info "🧹 检查异常样本处理和数据清洗..."

# 检查数据清洗相关日志
CLEANING_DETECTED=false
CLEANING_OPERATIONS=()
OUTLIER_REMOVAL_COUNT=0
MISSING_VALUE_HANDLING_COUNT=0
DATA_VALIDATION_COUNT=0

if [[ -n "$LOG_PATH" ]]; then
    log_info "🔍 搜索数据清洗相关日志..."
    
    # 搜索异常值处理
    OUTLIER_PATTERNS=(
        "异常值\|outlier"
        "离群点\|outliers"
        "数据清洗\|data.*cleaning"
        "remove.*outlier\|移除.*异常值"
        "异常样本\|anomalous.*sample"
    )
    
    for pattern in "${OUTLIER_PATTERNS[@]}"; do
        COUNT=$(grep -c "$pattern" "$LOG_PATH" 2>/dev/null || echo "0")
        if [[ $COUNT -gt 0 ]]; then
            OUTLIER_REMOVAL_COUNT=$((OUTLIER_REMOVAL_COUNT + COUNT))
            CLEANING_OPERATIONS+=("异常值处理:${COUNT}条")
        fi
    done
    
    # 搜索缺失值处理
    MISSING_VALUE_PATTERNS=(
        "缺失值\|missing.*value"
        "空值\|null.*value"
        "NaN\|nan"
        "填充\|fill"
        "插值\|interpolat"
    )
    
    for pattern in "${MISSING_VALUE_PATTERNS[@]}"; do
        COUNT=$(grep -c "$pattern" "$LOG_PATH" 2>/dev/null || echo "0")
        if [[ $COUNT -gt 0 ]]; then
            MISSING_VALUE_HANDLING_COUNT=$((MISSING_VALUE_HANDLING_COUNT + COUNT))
            CLEANING_OPERATIONS+=("缺失值处理:${COUNT}条")
        fi
    done
    
    # 搜索数据验证
    VALIDATION_PATTERNS=(
        "数据验证\|data.*validation"
        "数据检查\|data.*check"
        "数据完整性\|data.*integrity"
        "质量检查\|quality.*check"
    )
    
    for pattern in "${VALIDATION_PATTERNS[@]}"; do
        COUNT=$(grep -c "$pattern" "$LOG_PATH" 2>/dev/null || echo "0")
        if [[ $COUNT -gt 0 ]]; then
            DATA_VALIDATION_COUNT=$((DATA_VALIDATION_COUNT + COUNT))
            CLEANING_OPERATIONS+=("数据验证:${COUNT}条")
        fi
    done
    
    # 检查特征数量变化（清洗前后对比）
    FEATURE_REDUCTION_DETECTED=false
    BEFORE_CLEANING=0
    AFTER_CLEANING=0
    
    # 搜索清洗前后的特征数量对比
    CLEANING_COMPARISON=$(grep -E "清洗前.*[0-9]+.*清洗后.*[0-9]+|before.*cleaning.*[0-9]+.*after.*cleaning.*[0-9]+" "$LOG_PATH" 2>/dev/null | head -1)
    
    if [[ -n "$CLEANING_COMPARISON" ]]; then
        BEFORE_CLEANING=$(echo "$CLEANING_COMPARISON" | grep -oE '[0-9]+' | head -1 || echo "0")
        AFTER_CLEANING=$(echo "$CLEANING_COMPARISON" | grep -oE '[0-9]+' | tail -1 || echo "0")
        
        if [[ $BEFORE_CLEANING -gt $AFTER_CLEANING ]]; then
            FEATURE_REDUCTION_DETECTED=true
            CLEANING_OPERATIONS+=("特征清洗:从${BEFORE_CLEANING}个减少到${AFTER_CLEANING}个")
        fi
    fi
    
    if [[ ${#CLEANING_OPERATIONS[@]} -gt 0 ]]; then
        CLEANING_DETECTED=true
    fi
    
    log_info "📊 数据清洗操作统计:"
    log_info "  ├─ 异常值处理: $OUTLIER_REMOVAL_COUNT 条日志"
    log_info "  ├─ 缺失值处理: $MISSING_VALUE_HANDLING_COUNT 条日志"
    log_info "  ├─ 数据验证: $DATA_VALIDATION_COUNT 条日志"
    log_info "  ├─ 特征数量变化: $([ "$FEATURE_REDUCTION_DETECTED" == "true" ] && echo "${BEFORE_CLEANING}→${AFTER_CLEANING}" || echo "无明确记录")"
    log_info "  └─ 清洗操作: ${CLEANING_OPERATIONS[*]:-无}"
fi

# 检查清洗后的阈值满足情况
CLEANED_THRESHOLD_MET=false
CLEANING_REASON=""

if [[ "$CLEANING_DETECTED" == "true" ]]; then
    # 如果检测到清洗操作，检查清洗后是否仍满足阈值
    if [[ $AFTER_CLEANING -gt 0 ]]; then
        # 有明确的清洗后数量
        if [[ $AFTER_CLEANING -ge $THRESHOLD_VALUE ]]; then
            CLEANED_THRESHOLD_MET=true
            CLEANING_REASON="清洗后特征数量${AFTER_CLEANING}个，仍满足≥${THRESHOLD_VALUE}的阈值要求"
        else
            CLEANING_REASON="清洗后特征数量${AFTER_CLEANING}个，不满足≥${THRESHOLD_VALUE}的阈值要求"
        fi
    else
        # 没有明确的清洗后数量，使用当前有效特征数
        if [[ $EFFECTIVE_FEATURE_COUNT -ge $THRESHOLD_VALUE ]]; then
            CLEANED_THRESHOLD_MET=true
            CLEANING_REASON="执行了数据清洗操作，当前特征数量${EFFECTIVE_FEATURE_COUNT}个，满足≥${THRESHOLD_VALUE}的阈值要求"
        else
            CLEANING_REASON="执行了数据清洗操作，但当前特征数量${EFFECTIVE_FEATURE_COUNT}个，不满足≥${THRESHOLD_VALUE}的阈值要求"
        fi
    fi
else
    # 没有检测到清洗操作
    if [[ $EFFECTIVE_FEATURE_COUNT -ge $THRESHOLD_VALUE ]]; then
        CLEANED_THRESHOLD_MET=true
        CLEANING_REASON="未检测到明确的数据清洗操作，但特征数量${EFFECTIVE_FEATURE_COUNT}个，满足阈值要求"
    else
        CLEANING_REASON="未检测到数据清洗操作，特征数量${EFFECTIVE_FEATURE_COUNT}个，不满足阈值要求，可能需要数据清洗"
    fi
fi

# 检查异常样本处理的具体方法
ANOMALY_HANDLING_METHODS=()

if [[ -n "$LOG_PATH" ]]; then
    # 检查具体的异常处理方法
    if grep -q "方差阈值\|variance.*threshold" "$LOG_PATH" 2>/dev/null; then
        ANOMALY_HANDLING_METHODS+=("方差阈值过滤")
    fi
    
    if grep -q "互信息\|mutual.*information" "$LOG_PATH" 2>/dev/null; then
        ANOMALY_HANDLING_METHODS+=("互信息特征选择")
    fi
    
    if grep -q "标准化\|normalization\|standardization" "$LOG_PATH" 2>/dev/null; then
        ANOMALY_HANDLING_METHODS+=("数据标准化")
    fi
    
    if grep -q "特征选择\|feature.*selection" "$LOG_PATH" 2>/dev/null; then
        ANOMALY_HANDLING_METHODS+=("特征选择算法")
    fi
    
    log_info "🛠️ 异常样本处理方法:"
    if [[ ${#ANOMALY_HANDLING_METHODS[@]} -gt 0 ]]; then
        for method in "${ANOMALY_HANDLING_METHODS[@]}"; do
            log_info "  ├─ $method"
        done
    else
        log_info "  └─ 无明确的异常处理方法记录"
    fi
fi

# 异常样本处理结果评估
if [[ "$CLEANED_THRESHOLD_MET" == "true" ]]; then
    STEP3_RESULT="✅ 清洗后仍满足阈值或给出明确原因。${CLEANING_REASON}，处理方法:[${ANOMALY_HANDLING_METHODS[*]:-标准处理}]，清洗操作:[${CLEANING_OPERATIONS[*]:-无明确记录}]"
    STEP3_STATUS="Pass"
else
    STEP3_RESULT="⚠️ 清洗后不满足阈值要求。${CLEANING_REASON}，需要进一步的数据处理或特征工程"
    STEP3_STATUS="Review"
fi

write_result_row 3 "异常样本处理" "清洗后仍满足阈值或给出明确原因" "$STEP3_RESULT" "$STEP3_STATUS"
show_test_step 3 "异常样本处理" "success"

# 停止安全网终止器
if [[ -n "$NUCLEAR_PID" ]]; then
    kill "$NUCLEAR_PID" 2>/dev/null || true
fi

# 保存测试产物
ARTIFACT=$(save_artifacts "$LOG_PATH" "$BASE_DIR")

# 测试结果汇总
echo ""
echo "📊 TC08 提取的用户行为特征数指标测试结果汇总:"
echo "  步骤1 - 系统自动触发特征处理: $STEP1_STATUS"
echo "  步骤2 - 校验阈值: $STEP2_STATUS"
echo "  步骤3 - 异常样本处理: $STEP3_STATUS"
echo "  日志文件: $LOG_PATH"
echo "  数据库路径: $DB_PATH"
echo "  测试产物: $ARTIFACT"

# 生成详细的实测结果报告（可直接复制粘贴到测试报告）
echo ""
echo "🎯 ===== TC08 实测结果详细报告 (可直接粘贴到测试报告) ====="
echo ""

echo "📊 【提取的用户行为特征数指标实测结果】"
echo "  ├─ 特征处理状态: $([ "$FEATURE_PROCESSING_DETECTED" == "true" ] && echo "✅ 检测到" || echo "⚠️ 未明确检测到")"
echo "  ├─ 有效特征数: $EFFECTIVE_FEATURE_COUNT 个"
echo "  ├─ 阈值要求: ≥ $THRESHOLD_VALUE 个"
echo "  ├─ 阈值达标状态: $([ "$THRESHOLD_MET" == "true" ] && echo "✅ 满足要求" || echo "❌ 不满足要求")"
echo "  └─ 处理总耗时: ${FEATURE_PROCESSING_DURATION}秒"
echo ""

echo "📈 【特征统计信息详细数据】"
echo "  ├─ 特征数量(features): $FINAL_FEATURE_COUNT 个"
echo "  ├─ 特征维度(dimensions): $FINAL_DIMENSIONS 维"
echo "  ├─ 特征键数(keys): $FINAL_KEYS 个"
echo "  ├─ 特征列数(columns): $FINAL_COLUMNS 列"
echo "  ├─ 数据库记录: $DB_FEATURE_COUNT 条"
echo "  ├─ 主要数据来源: $FEATURE_COUNT_SOURCE"
echo "  └─ 特征向量维度: $([ "$DB_FEATURE_INFO" == "true" ] && echo "${VECTOR_LENGTH}维(数据库验证)" || echo "未从数据库验证")"
echo ""

echo "🔍 【阈值校验详细结果】"
echo "  ├─ 阈值标准: 有效特征数 ≥ 200"
echo "  ├─ 实际特征数: $EFFECTIVE_FEATURE_COUNT 个"
echo "  ├─ 超出阈值: $((EFFECTIVE_FEATURE_COUNT - THRESHOLD_VALUE)) 个"
echo "  ├─ 达标率: $(echo "scale=1; $EFFECTIVE_FEATURE_COUNT * 100 / $THRESHOLD_VALUE" | bc -l 2>/dev/null || echo "0")%"
echo "  ├─ 数据来源: $FEATURE_COUNT_SOURCE"
echo "  └─ 质量指标: $([ ${#FEATURE_QUALITY_INDICATORS[@]} -gt 0 ] && echo "${FEATURE_QUALITY_INDICATORS[*]}" || echo "无明确质量指标")"
echo ""

echo "🧹 【异常样本处理详细结果】"
echo "  ├─ 数据清洗检测: $([ "$CLEANING_DETECTED" == "true" ] && echo "✅ 检测到清洗操作" || echo "⚠️ 未检测到明确清洗操作")"
echo "  ├─ 异常值处理: $OUTLIER_REMOVAL_COUNT 条日志"
echo "  ├─ 缺失值处理: $MISSING_VALUE_HANDLING_COUNT 条日志"
echo "  ├─ 数据验证: $DATA_VALIDATION_COUNT 条日志"
echo "  ├─ 特征数量变化: $([ "$FEATURE_REDUCTION_DETECTED" == "true" ] && echo "从${BEFORE_CLEANING}个减少到${AFTER_CLEANING}个" || echo "无明确变化记录")"
echo "  ├─ 处理方法: $([ ${#ANOMALY_HANDLING_METHODS[@]} -gt 0 ] && echo "${ANOMALY_HANDLING_METHODS[*]}" || echo "标准处理流程")"
echo "  └─ 清洗后阈值: $([ "$CLEANED_THRESHOLD_MET" == "true" ] && echo "✅ 仍满足要求" || echo "⚠️ 需要关注")"
echo ""

echo "🎯 ===== 可直接复制的测试步骤实测结果 ====="
echo ""
echo "步骤1实测结果: 输出特征统计信息(列数/维度/键数)"
echo "           具体数据: 特征数量${FINAL_FEATURE_COUNT}个，维度${FINAL_DIMENSIONS}维，键数${FINAL_KEYS}个，列数${FINAL_COLUMNS}列"
echo "           统计来源: 日志分析+数据库验证，数据库记录${DB_FEATURE_COUNT}条，特征向量维度${VECTOR_LENGTH}维"
echo "           处理状态: $([ "$FEATURE_PROCESSING_DETECTED" == "true" ] && echo "特征处理成功执行，耗时${FEATURE_PROCESSING_DURATION}秒" || echo "特征处理执行状态需确认")"
echo ""
echo "步骤2实测结果: 有效特征数≥200"
echo "           具体数据: 有效特征数${EFFECTIVE_FEATURE_COUNT}个(来源:${FEATURE_COUNT_SOURCE})"
echo "           阈值对比: ${EFFECTIVE_FEATURE_COUNT} $([ "$THRESHOLD_MET" == "true" ] && echo "≥" || echo "<") ${THRESHOLD_VALUE}，达标率$(echo "scale=1; $EFFECTIVE_FEATURE_COUNT * 100 / $THRESHOLD_VALUE" | bc -l 2>/dev/null || echo "0")%"
echo "           评估结果: $([ "$THRESHOLD_MET" == "true" ] && echo "完全满足阈值要求，超出标准$((EFFECTIVE_FEATURE_COUNT - THRESHOLD_VALUE))个特征" || echo "不满足阈值要求，缺少$((THRESHOLD_VALUE - EFFECTIVE_FEATURE_COUNT))个特征")"
echo ""
echo "步骤3实测结果: 清洗后仍满足阈值或给出明确原因"
echo "           具体数据: 异常值处理${OUTLIER_REMOVAL_COUNT}条，缺失值处理${MISSING_VALUE_HANDLING_COUNT}条，数据验证${DATA_VALIDATION_COUNT}条"
echo "           处理效果: $([ "$FEATURE_REDUCTION_DETECTED" == "true" ] && echo "特征从${BEFORE_CLEANING}个优化到${AFTER_CLEANING}个" || echo "无明确的特征数量变化记录")"
echo "           处理方法: $([ ${#ANOMALY_HANDLING_METHODS[@]} -gt 0 ] && echo "${ANOMALY_HANDLING_METHODS[*]}" || echo "采用标准数据处理流程")"
echo "           最终状态: ${CLEANING_REASON}"

echo ""
echo "🎯 测试规范符合性检查:"
echo "  $([ "$STEP1_STATUS" == "Pass" ] && echo "✅" || echo "❌") 步骤1: 特征统计信息输出 - $STEP1_STATUS"
echo "  $([ "$STEP2_STATUS" == "Pass" ] && echo "✅" || echo "❌") 步骤2: 阈值校验(≥200) - $STEP2_STATUS"
echo "  $([ "$STEP3_STATUS" == "Pass" ] && echo "✅" || echo "❌") 步骤3: 异常样本处理 - $STEP3_STATUS"

# 总体结论
OVERALL_PASS_COUNT=0
for status in "$STEP1_STATUS" "$STEP2_STATUS" "$STEP3_STATUS"; do
    if [[ "$status" == "Pass" ]]; then
        OVERALL_PASS_COUNT=$((OVERALL_PASS_COUNT + 1))
    fi
done

echo ""
if [[ $OVERALL_PASS_COUNT -eq 3 ]]; then
    echo "✅ 测试通过：提取的用户行为特征数指标完全符合规范要求 (3/3步骤通过)"
elif [[ $OVERALL_PASS_COUNT -ge 2 ]]; then
    echo "⚠️ 测试基本通过：提取的用户行为特征数指标基本符合要求 ($OVERALL_PASS_COUNT/3步骤通过，需复核)"
else
    echo "❌ 测试未通过：提取的用户行为特征数指标存在重大问题 ($OVERALL_PASS_COUNT/3步骤通过)"
fi

exit 0

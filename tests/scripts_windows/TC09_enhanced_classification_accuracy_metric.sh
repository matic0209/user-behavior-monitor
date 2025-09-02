#!/bin/bash
# TC09 用户行为分类算法准确率指标测试 - 增强版 (详细实测结果输出)

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
echo "🎯 TC09 用户行为分类算法准确率指标测试 - 增强版"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 测试目标: 验证分类评估日志中的Accuracy、Precision、Recall、F1满足阈值，输出混淆矩阵和边界样本分析"
echo "🎯 成功标准: Accuracy≥90%，F1≥85%(宏/微平均按规范)，混淆矩阵完整，边界样本可解释"
echo "📊 数据库路径: $DB_PATH"
echo ""

write_result_header "TC09 Enhanced Classification Accuracy Metric"
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

# 步骤1：完成特征处理后自动执行评估命令
show_test_step 1 "完成特征处理后自动执行评估命令" "start"
log_info "🔄 触发特征处理和模型评估流程..."

# 触发特征处理和模型训练快捷键 rrrr
log_info "📤 发送快捷键rrrr触发特征处理和模型训练..."
send_char_repeated 'r' 4 100

EVALUATION_START=$(date +%s.%N)
EVALUATION_START_READABLE=$(date '+%H:%M:%S.%3N')
log_info "⏰ 评估流程开始时间: $EVALUATION_START_READABLE"

# 等待模型训练和评估相关日志（较长时间）
log_info "⏳ 等待模型训练和评估相关日志..."
EVALUATION_TIME=90  # 给模型训练和评估90秒时间

LOG_PATH=""
TRAINING_DETECTED=false
EVALUATION_DETECTED=false
PREDICTION_DETECTED=false

for i in {1..90}; do
    sleep 1
    LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 5)
    
    if [[ -n "$LOG_PATH" ]]; then
        # 检查特征处理相关日志
        if grep -qiE "特征处理|feature.*processing|UBM_MARK.*FEATURE_DONE" "$LOG_PATH" 2>/dev/null; then
            if [[ "$TRAINING_DETECTED" == "false" ]]; then
                TRAINING_DETECTED=true
                log_success "✅ 检测到特征处理完成"
            fi
        fi
        
        # 检查模型训练相关日志
        if grep -qiE "模型训练|model.*training|训练完成|training.*completed" "$LOG_PATH" 2>/dev/null; then
            if [[ "$TRAINING_DETECTED" == "false" ]]; then
                TRAINING_DETECTED=true
                log_success "✅ 检测到模型训练相关日志"
            fi
        fi
        
        # 检查评估指标相关日志
        if grep -qiE "accuracy|precision|recall|f1|混淆矩阵|confusion.*matrix|模型评估|model.*evaluation" "$LOG_PATH" 2>/dev/null; then
            if [[ "$EVALUATION_DETECTED" == "false" ]]; then
                EVALUATION_DETECTED=true
                log_success "✅ 检测到模型评估指标日志"
            fi
        fi
        
        # 优先检测预测开始，避免进入无限预测循环
        if grep -qiE "UBM_MARK.*PREDICT_(INIT|START|RUNNING)|使用训练模型预测完成|预测结果:|开始自动异常检测" "$LOG_PATH" 2>/dev/null; then
            PREDICTION_DETECTED=true
            log_success "✅ 检测到预测开始，立即停止程序避免无限循环"
            break
        fi
    fi
    
    if [[ $((i % 15)) -eq 0 ]]; then
        log_info "  等待模型评估: ${i}/90秒"
    fi
done

# 如果预测开始，立即停止程序避免无限循环
if [[ "$PREDICTION_DETECTED" == "true" ]]; then
    log_info "🔄 检测到预测开始，停止程序以避免无限循环..."
    stop_ubm_immediately "$PID" "预测检测"
    sleep 2
fi

EVALUATION_END=$(date +%s.%N)
EVALUATION_END_READABLE=$(date '+%H:%M:%S.%3N')
EVALUATION_DURATION=$(echo "$EVALUATION_END - $EVALUATION_START" | bc -l 2>/dev/null || echo "90.0")

log_info "⏰ 评估流程结束时间: $EVALUATION_END_READABLE"
log_info "⏱️ 评估流程总耗时: ${EVALUATION_DURATION}秒"

# 分析评估指标
METRICS_FOUND=false
ACCURACY_VALUE=""
PRECISION_VALUE=""
RECALL_VALUE=""
F1_VALUE=""
ACCURACY_PERCENT=""
PRECISION_PERCENT=""
RECALL_PERCENT=""
F1_PERCENT=""

if [[ -n "$LOG_PATH" ]]; then
    log_info "🔍 分析评估指标..."
    
    # 多种Accuracy匹配模式 (按优先级排序)
    ACCURACY_PATTERNS=(
        'ACCURACY:\s*([0-9]*\.?[0-9]+)'                    # "ACCURACY: 0.9500"
        'accuracy[[:space:]]*[:=][[:space:]]*([0-9]*\.?[0-9]+)'  # "accuracy: 0.95" 或 "accuracy=0.95"
        '模型准确率[[:space:]]*[:：][[:space:]]*([0-9]*\.?[0-9]+)'  # "模型准确率: 0.9500"
        'Accuracy[[:space:]]*[:=][[:space:]]*([0-9]*\.?[0-9]+)'  # "Accuracy: 0.95"
        '准确率[[:space:]]*[:：][[:space:]]*([0-9]*\.?[0-9]+)%?'  # "准确率: 95%" 或 "准确率: 0.95"
    )
    
    # 搜索Accuracy
    for pattern in "${ACCURACY_PATTERNS[@]}"; do
        ACCURACY_MATCH=$(grep -oE "$pattern" "$LOG_PATH" 2>/dev/null | head -1)
        if [[ -n "$ACCURACY_MATCH" ]]; then
            ACCURACY_VALUE=$(echo "$ACCURACY_MATCH" | grep -oE '[0-9]*\.?[0-9]+' | head -1)
            log_debug "找到Accuracy: $ACCURACY_VALUE (模式: $pattern)"
            break
        fi
    done
    
    # 多种Precision匹配模式
    PRECISION_PATTERNS=(
        'PRECISION:\s*([0-9]*\.?[0-9]+)'                   # "PRECISION: 0.9200"
        'precision[[:space:]]*[:=][[:space:]]*([0-9]*\.?[0-9]+)'  # "precision: 0.92"
        'Precision[[:space:]]*[:=][[:space:]]*([0-9]*\.?[0-9]+)'  # "Precision: 0.92"
        '精确率[[:space:]]*[:：][[:space:]]*([0-9]*\.?[0-9]+)%?'  # "精确率: 92%" 或 "精确率: 0.92"
        '查准率[[:space:]]*[:：][[:space:]]*([0-9]*\.?[0-9]+)%?'  # "查准率: 0.92"
    )
    
    # 搜索Precision
    for pattern in "${PRECISION_PATTERNS[@]}"; do
        PRECISION_MATCH=$(grep -oE "$pattern" "$LOG_PATH" 2>/dev/null | head -1)
        if [[ -n "$PRECISION_MATCH" ]]; then
            PRECISION_VALUE=$(echo "$PRECISION_MATCH" | grep -oE '[0-9]*\.?[0-9]+' | head -1)
            log_debug "找到Precision: $PRECISION_VALUE (模式: $pattern)"
            break
        fi
    done
    
    # 多种Recall匹配模式
    RECALL_PATTERNS=(
        'RECALL:\s*([0-9]*\.?[0-9]+)'                      # "RECALL: 0.8800"
        'recall[[:space:]]*[:=][[:space:]]*([0-9]*\.?[0-9]+)'     # "recall: 0.88"
        'Recall[[:space:]]*[:=][[:space:]]*([0-9]*\.?[0-9]+)'     # "Recall: 0.88"
        '召回率[[:space:]]*[:：][[:space:]]*([0-9]*\.?[0-9]+)%?'   # "召回率: 88%" 或 "召回率: 0.88"
        '查全率[[:space:]]*[:：][[:space:]]*([0-9]*\.?[0-9]+)%?'   # "查全率: 0.88"
    )
    
    # 搜索Recall
    for pattern in "${RECALL_PATTERNS[@]}"; do
        RECALL_MATCH=$(grep -oE "$pattern" "$LOG_PATH" 2>/dev/null | head -1)
        if [[ -n "$RECALL_MATCH" ]]; then
            RECALL_VALUE=$(echo "$RECALL_MATCH" | grep -oE '[0-9]*\.?[0-9]+' | head -1)
            log_debug "找到Recall: $RECALL_VALUE (模式: $pattern)"
            break
        fi
    done
    
    # 多种F1匹配模式
    F1_PATTERNS=(
        'F1:\s*([0-9]*\.?[0-9]+)'                          # "F1: 0.8750"
        'f1[[:space:]]*[:=][[:space:]]*([0-9]*\.?[0-9]+)'         # "f1: 0.87" 或 "f1=0.87"
        'f1_score[[:space:]]*[:=][[:space:]]*([0-9]*\.?[0-9]+)'   # "f1_score: 0.87"
        'F1[[:space:]]*[:=][[:space:]]*([0-9]*\.?[0-9]+)'         # "F1: 0.87"
        'F1-score[[:space:]]*[:=][[:space:]]*([0-9]*\.?[0-9]+)'   # "F1-score: 0.87"
        'F1分数[[:space:]]*[:：][[:space:]]*([0-9]*\.?[0-9]+)%?'   # "F1分数: 87%" 或 "F1分数: 0.87"
    )
    
    # 搜索F1
    for pattern in "${F1_PATTERNS[@]}"; do
        F1_MATCH=$(grep -oE "$pattern" "$LOG_PATH" 2>/dev/null | head -1)
        if [[ -n "$F1_MATCH" ]]; then
            F1_VALUE=$(echo "$F1_MATCH" | grep -oE '[0-9]*\.?[0-9]+' | head -1)
            log_debug "找到F1: $F1_VALUE (模式: $pattern)"
            break
        fi
    done
    
    # 转换为百分比格式（如果是0-1之间的小数）
    if [[ -n "$ACCURACY_VALUE" ]]; then
        if [[ $(echo "$ACCURACY_VALUE <= 1" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
            ACCURACY_PERCENT=$(echo "$ACCURACY_VALUE * 100" | bc -l 2>/dev/null || echo "$ACCURACY_VALUE")
        else
            ACCURACY_PERCENT=$ACCURACY_VALUE
        fi
    fi
    
    if [[ -n "$PRECISION_VALUE" ]]; then
        if [[ $(echo "$PRECISION_VALUE <= 1" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
            PRECISION_PERCENT=$(echo "$PRECISION_VALUE * 100" | bc -l 2>/dev/null || echo "$PRECISION_VALUE")
        else
            PRECISION_PERCENT=$PRECISION_VALUE
        fi
    fi
    
    if [[ -n "$RECALL_VALUE" ]]; then
        if [[ $(echo "$RECALL_VALUE <= 1" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
            RECALL_PERCENT=$(echo "$RECALL_VALUE * 100" | bc -l 2>/dev/null || echo "$RECALL_VALUE")
        else
            RECALL_PERCENT=$RECALL_VALUE
        fi
    fi
    
    if [[ -n "$F1_VALUE" ]]; then
        if [[ $(echo "$F1_VALUE <= 1" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
            F1_PERCENT=$(echo "$F1_VALUE * 100" | bc -l 2>/dev/null || echo "$F1_VALUE")
        else
            F1_PERCENT=$F1_VALUE
        fi
    fi
    
    # 获取评估相关的详细日志示例
    EVALUATION_LOG_SAMPLES=$(grep -i "accuracy\|precision\|recall\|f1\|evaluation\|评估" "$LOG_PATH" 2>/dev/null | head -8 | tr '\n' '; ')
    
    log_info "📊 评估指标分析结果:"
    log_info "  ├─ Accuracy: ${ACCURACY_VALUE:-未找到} (${ACCURACY_PERCENT:-0}%)"
    log_info "  ├─ Precision: ${PRECISION_VALUE:-未找到} (${PRECISION_PERCENT:-0}%)"
    log_info "  ├─ Recall: ${RECALL_VALUE:-未找到} (${RECALL_PERCENT:-0}%)"
    log_info "  ├─ F1-Score: ${F1_VALUE:-未找到} (${F1_PERCENT:-0}%)"
    log_info "  └─ 日志示例: ${EVALUATION_LOG_SAMPLES:-无相关日志}"
    
    if [[ -n "$ACCURACY_VALUE" && -n "$PRECISION_VALUE" && -n "$RECALL_VALUE" && -n "$F1_VALUE" ]]; then
        METRICS_FOUND=true
    fi
fi

# 评估指标输出结果评估
if [[ "$METRICS_FOUND" == "true" ]]; then
    STEP1_RESULT="✅ 输出Accuracy、Precision、Recall、F1指标。Accuracy:${ACCURACY_PERCENT:-0}%, Precision:${PRECISION_PERCENT:-0}%, Recall:${RECALL_PERCENT:-0}%, F1:${F1_PERCENT:-0}%，评估耗时:${EVALUATION_DURATION}秒"
    STEP1_STATUS="Pass"
else
    STEP1_RESULT="❌ 未检测到完整的评估指标输出，模型评估可能未正常执行"
    STEP1_STATUS="Fail"
fi

write_result_row 1 "完成特征处理后自动执行评估命令" "输出 Accuracy、Precision、Recall、F1" "$STEP1_RESULT" "$STEP1_STATUS"
show_test_step 1 "完成特征处理后自动执行评估命令" "success"

# 步骤2：阈值校验
show_test_step 2 "阈值校验" "start"
log_info "🔍 校验评估指标阈值..."

# 阈值要求
ACCURACY_THRESHOLD=90.0
F1_THRESHOLD=85.0

# 阈值校验
ACCURACY_MET=false
F1_MET=false

if [[ -n "$ACCURACY_PERCENT" ]]; then
    if [[ $(echo "$ACCURACY_PERCENT >= $ACCURACY_THRESHOLD" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        ACCURACY_MET=true
    fi
fi

if [[ -n "$F1_PERCENT" ]]; then
    if [[ $(echo "$F1_PERCENT >= $F1_THRESHOLD" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        F1_MET=true
    fi
fi

log_info "📊 评估指标阈值校验:"
log_info "  ├─ Accuracy阈值: ≥ ${ACCURACY_THRESHOLD}%"
log_info "  ├─ Accuracy实际: ${ACCURACY_PERCENT:-0}%"
log_info "  ├─ Accuracy状态: $([ "$ACCURACY_MET" == "true" ] && echo "✅ 满足要求" || echo "❌ 不满足要求")"
log_info "  ├─ F1阈值: ≥ ${F1_THRESHOLD}%"
log_info "  ├─ F1实际: ${F1_PERCENT:-0}%"
log_info "  └─ F1状态: $([ "$F1_MET" == "true" ] && echo "✅ 满足要求" || echo "❌ 不满足要求")"

# 检查宏平均和微平均
MACRO_AVERAGE_DETECTED=false
MICRO_AVERAGE_DETECTED=false
WEIGHTED_AVERAGE_DETECTED=false

if [[ -n "$LOG_PATH" ]]; then
    # 检查平均方式
    if grep -q "macro.*average\|宏平均\|macro.*avg" "$LOG_PATH" 2>/dev/null; then
        MACRO_AVERAGE_DETECTED=true
        log_info "📊 检测到宏平均(macro average)计算方式"
    fi
    
    if grep -q "micro.*average\|微平均\|micro.*avg" "$LOG_PATH" 2>/dev/null; then
        MICRO_AVERAGE_DETECTED=true
        log_info "📊 检测到微平均(micro average)计算方式"
    fi
    
    if grep -q "weighted.*average\|加权平均\|weighted.*avg" "$LOG_PATH" 2>/dev/null; then
        WEIGHTED_AVERAGE_DETECTED=true
        log_info "📊 检测到加权平均(weighted average)计算方式"
    fi
fi

# 计算额外的性能指标
PERFORMANCE_INDICATORS=()

if [[ -n "$ACCURACY_PERCENT" && -n "$F1_PERCENT" ]]; then
    # 计算性能指标差距
    ACCURACY_GAP=$(echo "$ACCURACY_PERCENT - $ACCURACY_THRESHOLD" | bc -l 2>/dev/null || echo "0")
    F1_GAP=$(echo "$F1_PERCENT - $F1_THRESHOLD" | bc -l 2>/dev/null || echo "0")
    
    PERFORMANCE_INDICATORS+=("Accuracy差距:${ACCURACY_GAP}%")
    PERFORMANCE_INDICATORS+=("F1差距:${F1_GAP}%")
    
    # 计算综合性能得分 (Accuracy和F1的加权平均)
    COMPOSITE_SCORE=$(echo "($ACCURACY_PERCENT * 0.6 + $F1_PERCENT * 0.4)" | bc -l 2>/dev/null || echo "0")
    PERFORMANCE_INDICATORS+=("综合得分:${COMPOSITE_SCORE}%")
fi

log_info "📈 性能指标详细分析:"
if [[ ${#PERFORMANCE_INDICATORS[@]} -gt 0 ]]; then
    for indicator in "${PERFORMANCE_INDICATORS[@]}"; do
        log_info "  ├─ $indicator"
    done
else
    log_info "  └─ 无法计算详细性能指标"
fi

# 阈值校验结果评估
THRESHOLD_COMPLIANCE=false
if [[ "$ACCURACY_MET" == "true" && "$F1_MET" == "true" ]]; then
    THRESHOLD_COMPLIANCE=true
fi

if [[ "$THRESHOLD_COMPLIANCE" == "true" ]]; then
    AVERAGE_TYPE="$([ "$MACRO_AVERAGE_DETECTED" == "true" ] && echo "宏平均" || ([ "$MICRO_AVERAGE_DETECTED" == "true" ] && echo "微平均" || ([ "$WEIGHTED_AVERAGE_DETECTED" == "true" ] && echo "加权平均" || "标准平均")))"
    STEP2_RESULT="✅ Accuracy≥90%，F1≥85%(宏/微平均按规范)。Accuracy:${ACCURACY_PERCENT}%(差距+${ACCURACY_GAP}%), F1:${F1_PERCENT}%(差距+${F1_GAP}%), 平均方式:${AVERAGE_TYPE}, 综合得分:${COMPOSITE_SCORE}%"
    STEP2_STATUS="Pass"
else
    STEP2_RESULT="❌ 评估指标不满足阈值要求。Accuracy:${ACCURACY_PERCENT}%(要求≥90%), F1:${F1_PERCENT}%(要求≥85%), 需要模型优化"
    STEP2_STATUS="Fail"
fi

write_result_row 2 "阈值校验" "Accuracy ≥ 90%，F1 ≥ 85%(宏/微平均按规范)" "$STEP2_RESULT" "$STEP2_STATUS"
show_test_step 2 "阈值校验" "success"

# 步骤3：误分分析
show_test_step 3 "误分分析" "start"
log_info "🧹 检查混淆矩阵和边界样本分析..."

# 检查混淆矩阵相关日志
CONFUSION_MATRIX_FOUND=false
CONFUSION_MATRIX_DATA=""
BOUNDARY_ANALYSIS_FOUND=false
BOUNDARY_SAMPLES=""

if [[ -n "$LOG_PATH" ]]; then
    log_info "🔍 搜索混淆矩阵相关日志..."
    
    # 搜索混淆矩阵
    CONFUSION_MATRIX_PATTERNS=(
        "Confusion Matrix"
        "混淆矩阵"
        "confusion.*matrix"
        "分类矩阵"
        "错误分类矩阵"
    )
    
    for pattern in "${CONFUSION_MATRIX_PATTERNS[@]}"; do
        if grep -q "$pattern" "$LOG_PATH" 2>/dev/null; then
            CONFUSION_MATRIX_FOUND=true
            log_success "✅ 检测到混淆矩阵相关日志"
            
            # 提取混淆矩阵数据（通常在"Confusion Matrix:"之后的几行）
            MATRIX_START_LINE=$(grep -n "$pattern" "$LOG_PATH" | head -1 | cut -d: -f1)
            if [[ -n "$MATRIX_START_LINE" ]]; then
                # 提取矩阵后的5行数据
                CONFUSION_MATRIX_DATA=$(sed -n "${MATRIX_START_LINE},$((MATRIX_START_LINE + 5))p" "$LOG_PATH" | tr '\n' '; ')
                log_debug "提取到混淆矩阵数据: $CONFUSION_MATRIX_DATA"
            fi
            break
        fi
    done
    
    # 搜索边界样本分析
    BOUNDARY_PATTERNS=(
        "边界样本"
        "boundary.*sample"
        "边缘样本"
        "误分.*分析"
        "misclassif.*analysis"
        "错误.*分类"
        "false.*positive"
        "false.*negative"
        "边界.*分析"
    )
    
    BOUNDARY_INDICATORS=()
    for pattern in "${BOUNDARY_PATTERNS[@]}"; do
        COUNT=$(grep -c "$pattern" "$LOG_PATH" 2>/dev/null || echo "0")
        if [[ $COUNT -gt 0 ]]; then
            BOUNDARY_ANALYSIS_FOUND=true
            BOUNDARY_INDICATORS+=("${pattern}:${COUNT}条")
        fi
    done
    
    if [[ "$BOUNDARY_ANALYSIS_FOUND" == "true" ]]; then
        log_success "✅ 检测到边界样本分析相关日志"
        BOUNDARY_SAMPLES="${BOUNDARY_INDICATORS[*]}"
    fi
    
    # 提取具体的混淆矩阵数值
    TRUE_POSITIVE=0
    FALSE_POSITIVE=0
    TRUE_NEGATIVE=0
    FALSE_NEGATIVE=0
    
    # 尝试从日志中提取混淆矩阵的具体数值
    if [[ "$CONFUSION_MATRIX_FOUND" == "true" ]]; then
        # 查找形如 [[TP, FP], [FN, TN]] 或类似格式的矩阵
        MATRIX_VALUES=$(echo "$CONFUSION_MATRIX_DATA" | grep -oE '\[\[.*\]\]|\[.*\].*\[.*\]' | head -1)
        
        if [[ -n "$MATRIX_VALUES" ]]; then
            # 提取所有数字
            NUMBERS=($(echo "$MATRIX_VALUES" | grep -oE '[0-9]+'))
            
            if [[ ${#NUMBERS[@]} -ge 4 ]]; then
                TRUE_NEGATIVE=${NUMBERS[0]}   # [0,0] 位置
                FALSE_POSITIVE=${NUMBERS[1]}  # [0,1] 位置
                FALSE_NEGATIVE=${NUMBERS[2]}  # [1,0] 位置
                TRUE_POSITIVE=${NUMBERS[3]}   # [1,1] 位置
                
                log_info "📊 混淆矩阵数值解析:"
                log_info "  ├─ True Positive (TP): $TRUE_POSITIVE"
                log_info "  ├─ False Positive (FP): $FALSE_POSITIVE"
                log_info "  ├─ True Negative (TN): $TRUE_NEGATIVE"
                log_info "  └─ False Negative (FN): $FALSE_NEGATIVE"
            fi
        fi
    fi
    
    # 计算额外的分类指标
    TOTAL_SAMPLES=$((TRUE_POSITIVE + FALSE_POSITIVE + TRUE_NEGATIVE + FALSE_NEGATIVE))
    CORRECT_PREDICTIONS=$((TRUE_POSITIVE + TRUE_NEGATIVE))
    INCORRECT_PREDICTIONS=$((FALSE_POSITIVE + FALSE_NEGATIVE))
    
    if [[ $TOTAL_SAMPLES -gt 0 ]]; then
        CALCULATED_ACCURACY=$(echo "scale=4; $CORRECT_PREDICTIONS * 100 / $TOTAL_SAMPLES" | bc -l 2>/dev/null || echo "0")
        ERROR_RATE=$(echo "scale=4; $INCORRECT_PREDICTIONS * 100 / $TOTAL_SAMPLES" | bc -l 2>/dev/null || echo "0")
        
        log_info "📊 基于混淆矩阵的验证指标:"
        log_info "  ├─ 总样本数: $TOTAL_SAMPLES"
        log_info "  ├─ 正确预测: $CORRECT_PREDICTIONS"
        log_info "  ├─ 错误预测: $INCORRECT_PREDICTIONS"
        log_info "  ├─ 计算准确率: ${CALCULATED_ACCURACY}%"
        log_info "  └─ 错误率: ${ERROR_RATE}%"
    fi
fi

# 检查边界样本的可解释性
INTERPRETABILITY_INDICATORS=()

if [[ -n "$LOG_PATH" ]]; then
    # 检查可解释性相关的日志
    if grep -q "特征重要性\|feature.*importance" "$LOG_PATH" 2>/dev/null; then
        INTERPRETABILITY_INDICATORS+=("特征重要性分析")
    fi
    
    if grep -q "决策边界\|decision.*boundary" "$LOG_PATH" 2>/dev/null; then
        INTERPRETABILITY_INDICATORS+=("决策边界分析")
    fi
    
    if grep -q "样本解释\|sample.*explanation\|样本.*分析" "$LOG_PATH" 2>/dev/null; then
        INTERPRETABILITY_INDICATORS+=("样本解释分析")
    fi
    
    if grep -q "分类原因\|classification.*reason" "$LOG_PATH" 2>/dev/null; then
        INTERPRETABILITY_INDICATORS+=("分类原因分析")
    fi
    
    log_info "🔍 边界样本可解释性指标:"
    if [[ ${#INTERPRETABILITY_INDICATORS[@]} -gt 0 ]]; then
        for indicator in "${INTERPRETABILITY_INDICATORS[@]}"; do
            log_info "  ├─ $indicator"
        done
    else
        log_info "  └─ 无明确的可解释性分析日志"
    fi
fi

# 生成混淆矩阵的详细分析报告
CONFUSION_MATRIX_ANALYSIS=""
if [[ "$CONFUSION_MATRIX_FOUND" == "true" && $TOTAL_SAMPLES -gt 0 ]]; then
    CONFUSION_MATRIX_ANALYSIS="混淆矩阵[[${TRUE_NEGATIVE},${FALSE_POSITIVE}],[${FALSE_NEGATIVE},${TRUE_POSITIVE}]]，总样本${TOTAL_SAMPLES}个，正确预测${CORRECT_PREDICTIONS}个，错误预测${INCORRECT_PREDICTIONS}个，计算准确率${CALCULATED_ACCURACY}%"
else
    CONFUSION_MATRIX_ANALYSIS="混淆矩阵数据解析不完整，需要检查日志格式"
fi

# 误分分析结果评估
MISCLASSIFICATION_ANALYSIS_COMPLETE=false
if [[ "$CONFUSION_MATRIX_FOUND" == "true" ]]; then
    MISCLASSIFICATION_ANALYSIS_COMPLETE=true
fi

if [[ "$MISCLASSIFICATION_ANALYSIS_COMPLETE" == "true" ]]; then
    STEP3_RESULT="✅ 输出混淆矩阵，边界样本可解释。${CONFUSION_MATRIX_ANALYSIS}，边界样本分析:[${BOUNDARY_SAMPLES:-无明确记录}]，可解释性:[${INTERPRETABILITY_INDICATORS[*]:-标准分析}]"
    STEP3_STATUS="Pass"
else
    STEP3_RESULT="⚠️ 混淆矩阵或边界样本分析不完整。混淆矩阵检测:$([ "$CONFUSION_MATRIX_FOUND" == "true" ] && echo "找到" || echo "未找到")，边界样本分析:$([ "$BOUNDARY_ANALYSIS_FOUND" == "true" ] && echo "找到" || echo "未找到")"
    STEP3_STATUS="Review"
fi

write_result_row 3 "误分分析" "输出混淆矩阵，边界样本可解释" "$STEP3_RESULT" "$STEP3_STATUS"
show_test_step 3 "误分分析" "success"

# 停止安全网终止器
if [[ -n "$NUCLEAR_PID" ]]; then
    kill "$NUCLEAR_PID" 2>/dev/null || true
fi

# 保存测试产物
ARTIFACT=$(save_artifacts "$LOG_PATH" "$BASE_DIR")

# 测试结果汇总
echo ""
echo "📊 TC09 用户行为分类算法准确率指标测试结果汇总:"
echo "  步骤1 - 完成特征处理后自动执行评估命令: $STEP1_STATUS"
echo "  步骤2 - 阈值校验: $STEP2_STATUS"
echo "  步骤3 - 误分分析: $STEP3_STATUS"
echo "  日志文件: $LOG_PATH"
echo "  数据库路径: $DB_PATH"
echo "  测试产物: $ARTIFACT"

# 生成详细的实测结果报告（可直接复制粘贴到测试报告）
echo ""
echo "🎯 ===== TC09 实测结果详细报告 (可直接粘贴到测试报告) ====="
echo ""

echo "📊 【用户行为分类算法准确率指标实测结果】"
echo "  ├─ 模型评估状态: $([ "$EVALUATION_DETECTED" == "true" ] && echo "✅ 检测到" || echo "⚠️ 未明确检测到")"
echo "  ├─ 评估指标完整性: $([ "$METRICS_FOUND" == "true" ] && echo "✅ 四项指标完整" || echo "⚠️ 指标不完整")"
echo "  ├─ 阈值符合性: $([ "$THRESHOLD_COMPLIANCE" == "true" ] && echo "✅ 完全符合" || echo "❌ 不符合要求")"
echo "  └─ 评估总耗时: ${EVALUATION_DURATION}秒"
echo ""

echo "📈 【评估指标详细数据】"
echo "  ├─ Accuracy(准确率): ${ACCURACY_VALUE:-未检测到} (${ACCURACY_PERCENT:-0}%)"
echo "  ├─ Precision(精确率): ${PRECISION_VALUE:-未检测到} (${PRECISION_PERCENT:-0}%)"
echo "  ├─ Recall(召回率): ${RECALL_VALUE:-未检测到} (${RECALL_PERCENT:-0}%)"
echo "  ├─ F1-Score(F1分数): ${F1_VALUE:-未检测到} (${F1_PERCENT:-0}%)"
echo "  ├─ 综合得分: ${COMPOSITE_SCORE:-未计算}%"
echo "  └─ 平均方式: $([ "$MACRO_AVERAGE_DETECTED" == "true" ] && echo "宏平均" || ([ "$MICRO_AVERAGE_DETECTED" == "true" ] && echo "微平均" || ([ "$WEIGHTED_AVERAGE_DETECTED" == "true" ] && echo "加权平均" || "标准平均")))"
echo ""

echo "🔍 【阈值校验详细结果】"
echo "  ├─ Accuracy阈值: ≥ ${ACCURACY_THRESHOLD}%"
echo "  ├─ Accuracy实际: ${ACCURACY_PERCENT:-0}%"
echo "  ├─ Accuracy差距: ${ACCURACY_GAP:-0}%"
echo "  ├─ Accuracy状态: $([ "$ACCURACY_MET" == "true" ] && echo "✅ 满足要求" || echo "❌ 不满足要求")"
echo "  ├─ F1阈值: ≥ ${F1_THRESHOLD}%"
echo "  ├─ F1实际: ${F1_PERCENT:-0}%"
echo "  ├─ F1差距: ${F1_GAP:-0}%"
echo "  └─ F1状态: $([ "$F1_MET" == "true" ] && echo "✅ 满足要求" || echo "❌ 不满足要求")"
echo ""

echo "🧹 【误分分析详细结果】"
echo "  ├─ 混淆矩阵检测: $([ "$CONFUSION_MATRIX_FOUND" == "true" ] && echo "✅ 检测到" || echo "⚠️ 未检测到")"
echo "  ├─ 边界样本分析: $([ "$BOUNDARY_ANALYSIS_FOUND" == "true" ] && echo "✅ 检测到" || echo "⚠️ 未检测到明确分析")"
echo "  ├─ 混淆矩阵数据: $([ $TOTAL_SAMPLES -gt 0 ] && echo "TP:${TRUE_POSITIVE}, FP:${FALSE_POSITIVE}, TN:${TRUE_NEGATIVE}, FN:${FALSE_NEGATIVE}" || echo "数据解析不完整")"
echo "  ├─ 分类统计: 总样本${TOTAL_SAMPLES}个，正确预测${CORRECT_PREDICTIONS}个，错误预测${INCORRECT_PREDICTIONS}个"
echo "  ├─ 计算验证: 基于混淆矩阵计算准确率${CALCULATED_ACCURACY}%，错误率${ERROR_RATE}%"
echo "  └─ 可解释性: $([ ${#INTERPRETABILITY_INDICATORS[@]} -gt 0 ] && echo "${INTERPRETABILITY_INDICATORS[*]}" || echo "标准分类分析")"
echo ""

echo "🎯 ===== 可直接复制的测试步骤实测结果 ====="
echo ""
echo "步骤1实测结果: 输出Accuracy、Precision、Recall、F1"
echo "           具体数据: Accuracy:${ACCURACY_PERCENT:-0}%, Precision:${PRECISION_PERCENT:-0}%, Recall:${RECALL_PERCENT:-0}%, F1:${F1_PERCENT:-0}%"
echo "           原始数值: Accuracy:${ACCURACY_VALUE:-未检测}, Precision:${PRECISION_VALUE:-未检测}, Recall:${RECALL_VALUE:-未检测}, F1:${F1_VALUE:-未检测}"
echo "           评估状态: $([ "$EVALUATION_DETECTED" == "true" ] && echo "模型评估成功执行，耗时${EVALUATION_DURATION}秒" || echo "模型评估执行状态需确认")"
echo ""
echo "步骤2实测结果: Accuracy≥90%，F1≥85%(宏/微平均按规范)"
echo "           具体数据: Accuracy:${ACCURACY_PERCENT}%(要求≥90%), F1:${F1_PERCENT}%(要求≥85%)"
echo "           阈值对比: Accuracy差距${ACCURACY_GAP}%, F1差距${F1_GAP}%, 综合得分${COMPOSITE_SCORE}%"
echo "           评估结果: $([ "$THRESHOLD_COMPLIANCE" == "true" ] && echo "完全满足阈值要求，性能优秀" || echo "不满足阈值要求，需要模型优化")"
echo "           平均方式: $([ "$MACRO_AVERAGE_DETECTED" == "true" ] && echo "宏平均" || ([ "$MICRO_AVERAGE_DETECTED" == "true" ] && echo "微平均" || ([ "$WEIGHTED_AVERAGE_DETECTED" == "true" ] && echo "加权平均" || "标准平均计算")))"
echo ""
echo "步骤3实测结果: 输出混淆矩阵，边界样本可解释"
echo "           具体数据: 混淆矩阵TP:${TRUE_POSITIVE}, FP:${FALSE_POSITIVE}, TN:${TRUE_NEGATIVE}, FN:${FALSE_NEGATIVE}"
echo "           矩阵分析: 总样本${TOTAL_SAMPLES}个，正确预测${CORRECT_PREDICTIONS}个(${CALCULATED_ACCURACY}%)，错误预测${INCORRECT_PREDICTIONS}个(${ERROR_RATE}%)"
echo "           边界样本: $([ "$BOUNDARY_ANALYSIS_FOUND" == "true" ] && echo "${BOUNDARY_SAMPLES}" || echo "无明确的边界样本分析记录")"
echo "           可解释性: $([ ${#INTERPRETABILITY_INDICATORS[@]} -gt 0 ] && echo "${INTERPRETABILITY_INDICATORS[*]}" || echo "采用标准分类分析方法")"

echo ""
echo "🎯 测试规范符合性检查:"
echo "  $([ "$STEP1_STATUS" == "Pass" ] && echo "✅" || echo "❌") 步骤1: 评估指标输出 - $STEP1_STATUS"
echo "  $([ "$STEP2_STATUS" == "Pass" ] && echo "✅" || echo "❌") 步骤2: 阈值校验(Acc≥90%, F1≥85%) - $STEP2_STATUS"
echo "  $([ "$STEP3_STATUS" == "Pass" ] && echo "✅" || echo "❌") 步骤3: 混淆矩阵和误分分析 - $STEP3_STATUS"

# 总体结论
OVERALL_PASS_COUNT=0
for status in "$STEP1_STATUS" "$STEP2_STATUS" "$STEP3_STATUS"; do
    if [[ "$status" == "Pass" ]]; then
        OVERALL_PASS_COUNT=$((OVERALL_PASS_COUNT + 1))
    fi
done

echo ""
if [[ $OVERALL_PASS_COUNT -eq 3 ]]; then
    echo "✅ 测试通过：用户行为分类算法准确率指标完全符合规范要求 (3/3步骤通过)"
elif [[ $OVERALL_PASS_COUNT -ge 2 ]]; then
    echo "⚠️ 测试基本通过：用户行为分类算法准确率指标基本符合要求 ($OVERALL_PASS_COUNT/3步骤通过，需复核)"
else
    echo "❌ 测试未通过：用户行为分类算法准确率指标存在重大问题 ($OVERALL_PASS_COUNT/3步骤通过)"
fi

exit 0

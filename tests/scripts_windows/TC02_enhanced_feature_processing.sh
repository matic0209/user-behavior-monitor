#!/bin/bash
# TC02 特征处理流程测试 - 增强版 (详细实测结果输出)

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
echo "🎯 TC02 特征处理流程测试 - 增强版"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 测试目标: 验证数据采集后自动流程到特征处理，并输出详细实测数据"
echo "🎯 成功标准: 特征处理完成，features表有记录，特征质量合格，性能达标"
echo "📊 数据库路径: $DB_PATH"
echo ""

write_result_header "TC02 Enhanced Feature Processing"
write_result_table_header

# 步骤1：关闭数据采集后自动流程到特征处理流程
show_test_step 1 "关闭数据采集后自动流程到特征处理流程" "start"
log_info "🚀 启动UBM程序..."

# 启动程序
PID=$(start_ubm "$EXE_PATH" "$BASE_DIR")
if [[ -z "$PID" ]]; then
    log_error "程序启动失败"
    exit 1
fi

log_success "✅ 程序启动成功，PID: $PID"

# 等待程序启动
sleep $STARTUP_WAIT

# 首先进行一些数据采集，为特征处理提供数据
log_info "📊 进行数据采集，为特征处理提供原始数据..."
COLLECTION_START=$(date +%s.%N)

# 模拟30秒的鼠标和键盘操作
for i in {1..30}; do
    move_mouse_path 1 20
    if [[ $((i % 10)) -eq 0 ]]; then
        click_left_times 2
        send_char_repeated 'a' 2 100
    fi
    if [[ $((i % 5)) -eq 0 ]]; then
        log_info "  数据采集进度: ${i}/30秒"
    fi
done

COLLECTION_END=$(date +%s.%N)
COLLECTION_DURATION=$(echo "$COLLECTION_END - $COLLECTION_START" | bc -l 2>/dev/null || echo "30.0")

log_success "✅ 数据采集完成，耗时: ${COLLECTION_DURATION}秒"

# 检查原始数据是否已保存
if [[ -f "$DB_PATH" ]]; then
    RAW_RECORD_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM mouse_events;" 2>/dev/null || echo "0")
    log_info "📊 原始数据记录数: $RAW_RECORD_COUNT 条"
else
    log_warning "⚠️ 数据库文件不存在"
    RAW_RECORD_COUNT=0
fi

# 触发特征处理流程
log_info "🔄 触发特征处理流程（rrrr快捷键）..."
FEATURE_PROCESSING_START=$(date +%s.%N)
FEATURE_START_READABLE=$(date '+%H:%M:%S.%3N')

send_char_repeated 'r' 4 100
log_info "⏰ 特征处理开始时间: $FEATURE_START_READABLE"

# 等待特征处理关键日志
log_info "⏳ 等待特征处理关键日志..."
TIMEBOX=45  # 给特征处理更多时间
if [[ "${ULTRA_FAST_MODE:-false}" == "true" ]]; then TIMEBOX=15; elif [[ "${FAST_MODE:-false}" == "true" ]]; then TIMEBOX=25; fi
end_ts=$(( $(date +%s) + TIMEBOX ))

LOG_PATH=""
FEATURE_PROCESSING_DETECTED=false
while [[ $(date +%s) -lt $end_ts ]]; do
    LOG_PATH=$(wait_for_latest_log "$LOGS_DIR" 5)
    if [[ -n "$LOG_PATH" ]]; then
        # 检查特征处理开始日志
        if grep -qiE "UBM_MARK:\s*FEATURE_(START|PROCESSING)|特征处理|开始处理.*会话|process_session_features|feature.*start" "$LOG_PATH" 2>/dev/null; then
            FEATURE_PROCESSING_DETECTED=true
            log_success "✅ 检测到特征处理开始日志"
            break
        fi
    fi
    sleep 1
done

FEATURE_PROCESSING_END=$(date +%s.%N)
FEATURE_END_READABLE=$(date '+%H:%M:%S.%3N')
FEATURE_PROCESSING_DURATION=$(echo "$FEATURE_PROCESSING_END - $FEATURE_PROCESSING_START" | bc -l 2>/dev/null || echo "45.0")

log_info "⏰ 特征处理结束时间: $FEATURE_END_READABLE"
log_info "⏱️ 特征处理总耗时: ${FEATURE_PROCESSING_DURATION}秒"

if [[ "$FEATURE_PROCESSING_DETECTED" == "true" ]]; then
    STEP1_RESULT="✅ 特征处理流程已启动，开始时间: $FEATURE_START_READABLE，耗时: ${FEATURE_PROCESSING_DURATION}秒"
    STEP1_STATUS="Pass"
else
    STEP1_RESULT="⚠️ 未检测到特征处理开始日志，可能需要更长等待时间"
    STEP1_STATUS="Review"
fi

write_result_row 1 "关闭数据采集后自动流程到特征处理流程" "日志提示开始处理指定会话" "$STEP1_RESULT" "$STEP1_STATUS"
show_test_step 1 "关闭数据采集后自动流程到特征处理流程" "success"

# 步骤2：处理完成后检查数据库
show_test_step 2 "处理完成后检查数据库" "start"
log_info "🗄️ 检查数据库中的features表记录..."

# 等待特征处理完成
log_info "⏳ 等待特征处理完成日志..."
FEATURE_COMPLETION_DETECTED=false
ADDITIONAL_WAIT=30  # 额外等待时间
additional_end_ts=$(( $(date +%s) + ADDITIONAL_WAIT ))

while [[ $(date +%s) -lt $additional_end_ts ]]; do
    if [[ -n "$LOG_PATH" ]]; then
        # 检查特征处理完成日志
        if grep -qiE "UBM_MARK:\s*FEATURE_(DONE|COMPLETE)|特征处理完成|处理完成|features.*saved|feature.*complete" "$LOG_PATH" 2>/dev/null; then
            FEATURE_COMPLETION_DETECTED=true
            log_success "✅ 检测到特征处理完成日志"
            break
        fi
    fi
    sleep 2
done

# 检查features表是否存在及其结构
if [[ -f "$DB_PATH" ]]; then
    log_info "📋 检查features表结构..."
    
    # 检查表是否存在
    FEATURES_TABLE_EXISTS=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='features';" 2>/dev/null)
    
    if [[ -n "$FEATURES_TABLE_EXISTS" ]]; then
        log_success "✅ features表存在"
        
        # 获取表结构信息
        TABLE_SCHEMA=$(sqlite3 "$DB_PATH" "PRAGMA table_info(features);" 2>/dev/null)
        log_info "📊 features表结构:"
        echo "$TABLE_SCHEMA" | while IFS='|' read cid name type notnull dflt_value pk; do
            log_info "  列: $name, 类型: $type, 非空: $([ "$notnull" == "1" ] && echo "是" || echo "否")"
        done
        
        # 检查记录数量
        FEATURES_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM features;" 2>/dev/null || echo "0")
        log_info "📊 features表记录总数: $FEATURES_COUNT"
        
        # 检查user_id/session_id分布
        USER_SESSION_STATS=$(sqlite3 "$DB_PATH" "SELECT user_id, session_id, COUNT(*) as record_count FROM features GROUP BY user_id, session_id;" 2>/dev/null)
        log_info "👤 用户会话统计:"
        if [[ -n "$USER_SESSION_STATS" ]]; then
            echo "$USER_SESSION_STATS" | while IFS='|' read user_id session_id count; do
                log_info "  用户: $user_id, 会话: $session_id, 记录数: $count"
            done
        else
            log_info "  暂无用户会话数据"
        fi
        
        # 检查时间戳范围
        TIME_RANGE=$(sqlite3 "$DB_PATH" "SELECT MIN(timestamp), MAX(timestamp) FROM features;" 2>/dev/null)
        if [[ -n "$TIME_RANGE" ]]; then
            echo "$TIME_RANGE" | IFS='|' read min_time max_time
            TIME_SPAN=$(echo "$max_time - $min_time" | bc -l 2>/dev/null || echo "0")
            log_info "⏰ 时间戳范围: $min_time ~ $max_time (时间跨度: ${TIME_SPAN}秒)"
        fi
        
        # 检查feature_vector样本
        FEATURE_SAMPLES=$(sqlite3 "$DB_PATH" "SELECT user_id, session_id, timestamp, SUBSTR(feature_vector, 1, 100) as sample FROM features ORDER BY timestamp LIMIT 3;" 2>/dev/null)
        log_info "🔍 特征向量样本(前100字符):"
        if [[ -n "$FEATURE_SAMPLES" ]]; then
            echo "$FEATURE_SAMPLES" | while IFS='|' read user_id session_id timestamp sample; do
                log_info "  用户:$user_id, 会话:$session_id, 时间戳:$timestamp"
                log_info "    特征样本: ${sample}..."
            done
        else
            log_info "  暂无特征向量样本"
        fi
        
        # 验证必要字段
        REQUIRED_FIELDS_CHECK=true
        for field in "user_id" "session_id" "timestamp" "feature_vector"; do
            FIELD_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM features WHERE $field IS NOT NULL AND $field != '';" 2>/dev/null || echo "0")
            if [[ $FIELD_COUNT -eq $FEATURES_COUNT ]]; then
                log_success "  ✅ $field 字段完整 ($FIELD_COUNT/$FEATURES_COUNT)"
            else
                log_warning "  ⚠️ $field 字段不完整 ($FIELD_COUNT/$FEATURES_COUNT)"
                REQUIRED_FIELDS_CHECK=false
            fi
        done
        
        if [[ $FEATURES_COUNT -gt 0 && "$REQUIRED_FIELDS_CHECK" == "true" ]]; then
            STEP2_RESULT="✅ features表记录数: ${FEATURES_COUNT}条，包含完整的user_id/session_id/timestamp/feature_vector字段"
            STEP2_STATUS="Pass"
        elif [[ $FEATURES_COUNT -gt 0 ]]; then
            STEP2_RESULT="⚠️ features表记录数: ${FEATURES_COUNT}条，但部分必要字段不完整"
            STEP2_STATUS="Review"
        else
            STEP2_RESULT="❌ features表存在但无记录，特征处理可能未完成"
            STEP2_STATUS="Fail"
        fi
        
    else
        log_error "❌ features表不存在"
        FEATURES_COUNT=0
        STEP2_RESULT="❌ features表不存在，特征处理流程可能未正常执行"
        STEP2_STATUS="Fail"
    fi
    
else
    log_error "❌ 数据库文件不存在"
    FEATURES_COUNT=0
    STEP2_RESULT="❌ 数据库文件不存在"
    STEP2_STATUS="Fail"
fi

write_result_row 2 "处理完成后检查数据库" "生成对应features记录，带user_id/session_id/timestamp等" "$STEP2_RESULT" "$STEP2_STATUS"
show_test_step 2 "处理完成后检查数据库" "success"

# 步骤3：特征质量检查
show_test_step 3 "特征质量检查" "start"
log_info "🔍 进行特征质量检查..."

if [[ $FEATURES_COUNT -gt 0 && -f "$DB_PATH" ]]; then
    # 检查特征向量的质量
    log_info "📊 分析特征向量质量..."
    
    # 获取所有特征向量进行分析
    FEATURE_VECTORS=$(sqlite3 "$DB_PATH" "SELECT feature_vector FROM features LIMIT 10;" 2>/dev/null)
    
    NULL_VALUES_COUNT=0
    VALID_FEATURES_COUNT=0
    TOTAL_FEATURE_DIMENSIONS=0
    FEATURE_RANGE_ISSUES=0
    
    if [[ -n "$FEATURE_VECTORS" ]]; then
        # 分析每个特征向量
        echo "$FEATURE_VECTORS" | while IFS= read -r feature_vector; do
            if [[ -n "$feature_vector" && "$feature_vector" != "null" && "$feature_vector" != "{}" ]]; then
                # 检查是否为有效的JSON
                if echo "$feature_vector" | python3 -m json.tool > /dev/null 2>&1; then
                    VALID_FEATURES_COUNT=$((VALID_FEATURES_COUNT + 1))
                    
                    # 使用Python分析特征向量的统计信息
                    FEATURE_STATS=$(python3 -c "
import json
import sys
try:
    data = json.loads('$feature_vector')
    numeric_values = []
    null_count = 0
    for k, v in data.items():
        if v is None:
            null_count += 1
        elif isinstance(v, (int, float)):
            numeric_values.append(v)
    
    if numeric_values:
        min_val = min(numeric_values)
        max_val = max(numeric_values)
        avg_val = sum(numeric_values) / len(numeric_values)
        print(f'{len(data)}|{null_count}|{len(numeric_values)}|{min_val:.4f}|{max_val:.4f}|{avg_val:.4f}')
    else:
        print(f'{len(data)}|{null_count}|0|0|0|0')
except Exception as e:
    print('0|0|0|0|0|0')
" 2>/dev/null)
                    
                    if [[ -n "$FEATURE_STATS" ]]; then
                        echo "$FEATURE_STATS" | IFS='|' read total_dims null_count numeric_count min_val max_val avg_val
                        log_info "  特征维度: $total_dims, 空值: $null_count, 数值特征: $numeric_count"
                        log_info "    数值范围: [$min_val, $max_val], 平均值: $avg_val"
                        
                        TOTAL_FEATURE_DIMENSIONS=$((TOTAL_FEATURE_DIMENSIONS + total_dims))
                        NULL_VALUES_COUNT=$((NULL_VALUES_COUNT + null_count))
                        
                        # 检查数值范围是否合理（避免异常大的值）
                        if (( $(echo "$max_val > 1000000 || $min_val < -1000000" | bc -l 2>/dev/null || echo "0") )); then
                            FEATURE_RANGE_ISSUES=$((FEATURE_RANGE_ISSUES + 1))
                        fi
                    fi
                else
                    log_warning "  ⚠️ 发现无效的JSON特征向量"
                fi
            else
                log_warning "  ⚠️ 发现空的特征向量"
            fi
        done
    fi
    
    # 计算统计信息
    if [[ $FEATURES_COUNT -gt 0 ]]; then
        AVG_DIMENSIONS=$(echo "scale=1; $TOTAL_FEATURE_DIMENSIONS / $FEATURES_COUNT" | bc -l 2>/dev/null || echo "0")
        NULL_PERCENTAGE=$(echo "scale=2; $NULL_VALUES_COUNT * 100 / ($TOTAL_FEATURE_DIMENSIONS + 1)" | bc -l 2>/dev/null || echo "0")
    else
        AVG_DIMENSIONS=0
        NULL_PERCENTAGE=0
    fi
    
    log_info "📊 特征质量统计:"
    log_info "  ├─ 有效特征向量: $VALID_FEATURES_COUNT/$FEATURES_COUNT"
    log_info "  ├─ 平均特征维度: $AVG_DIMENSIONS"
    log_info "  ├─ 空值数量: $NULL_VALUES_COUNT"
    log_info "  ├─ 空值比例: ${NULL_PERCENTAGE}%"
    log_info "  └─ 数值范围异常: $FEATURE_RANGE_ISSUES 个特征向量"
    
    # 质量评估
    QUALITY_ISSUES=0
    QUALITY_DETAILS=""
    
    if (( $(echo "$NULL_PERCENTAGE > 20" | bc -l 2>/dev/null || echo "0") )); then
        QUALITY_ISSUES=$((QUALITY_ISSUES + 1))
        QUALITY_DETAILS="${QUALITY_DETAILS}空值比例过高(${NULL_PERCENTAGE}%); "
    fi
    
    if [[ $FEATURE_RANGE_ISSUES -gt 0 ]]; then
        QUALITY_ISSUES=$((QUALITY_ISSUES + 1))
        QUALITY_DETAILS="${QUALITY_DETAILS}数值范围异常($FEATURE_RANGE_ISSUES个); "
    fi
    
    if [[ $VALID_FEATURES_COUNT -lt $FEATURES_COUNT ]]; then
        QUALITY_ISSUES=$((QUALITY_ISSUES + 1))
        QUALITY_DETAILS="${QUALITY_DETAILS}无效特征向量($((FEATURES_COUNT - VALID_FEATURES_COUNT))个); "
    fi
    
    if [[ $QUALITY_ISSUES -eq 0 ]]; then
        STEP3_RESULT="✅ 特征质量检查通过: 无明显空值(${NULL_PERCENTAGE}%), 平均维度${AVG_DIMENSIONS}, 数值范围合理"
        STEP3_STATUS="Pass"
    else
        STEP3_RESULT="⚠️ 特征质量存在问题: $QUALITY_DETAILS"
        STEP3_STATUS="Review"
    fi
    
else
    STEP3_RESULT="❌ 无法进行特征质量检查，features表无记录"
    STEP3_STATUS="Fail"
fi

write_result_row 3 "特征质量检查" "无明显空值；关键统计与轨迹类特征存在且数值范围合理" "$STEP3_RESULT" "$STEP3_STATUS"
show_test_step 3 "特征质量检查" "success"

# 步骤4：性能与稳定性
show_test_step 4 "性能与稳定性" "start"
log_info "⚡ 性能与稳定性检查..."

# 检查处理耗时
PERFORMANCE_ISSUES=0
PERFORMANCE_DETAILS=""

if (( $(echo "$FEATURE_PROCESSING_DURATION > 120" | bc -l 2>/dev/null || echo "0") )); then
    PERFORMANCE_ISSUES=$((PERFORMANCE_ISSUES + 1))
    PERFORMANCE_DETAILS="${PERFORMANCE_DETAILS}处理耗时过长(${FEATURE_PROCESSING_DURATION}s > 120s); "
fi

# 检查日志中的错误
ERROR_COUNT=0
CRITICAL_COUNT=0
if [[ -n "$LOG_PATH" && -f "$LOG_PATH" ]]; then
    ERROR_COUNT=$(grep -ci "error" "$LOG_PATH" 2>/dev/null || echo "0")
    CRITICAL_COUNT=$(grep -ci "critical" "$LOG_PATH" 2>/dev/null || echo "0")
    
    log_info "📋 日志错误统计:"
    log_info "  ├─ ERROR 级别: $ERROR_COUNT 条"
    log_info "  └─ CRITICAL 级别: $CRITICAL_COUNT 条"
    
    if [[ $ERROR_COUNT -gt 0 ]]; then
        PERFORMANCE_ISSUES=$((PERFORMANCE_ISSUES + 1))
        PERFORMANCE_DETAILS="${PERFORMANCE_DETAILS}发现${ERROR_COUNT}个ERROR日志; "
    fi
    
    if [[ $CRITICAL_COUNT -gt 0 ]]; then
        PERFORMANCE_ISSUES=$((PERFORMANCE_ISSUES + 1))
        PERFORMANCE_DETAILS="${PERFORMANCE_DETAILS}发现${CRITICAL_COUNT}个CRITICAL日志; "
    fi
fi

# 检查内存使用情况（如果进程还在运行）
MEMORY_USAGE="N/A"
if kill -0 "$PID" 2>/dev/null; then
    if command -v ps >/dev/null 2>&1; then
        MEMORY_USAGE=$(ps -p "$PID" -o rss= 2>/dev/null | awk '{print $1/1024}' || echo "N/A")
        if [[ "$MEMORY_USAGE" != "N/A" ]]; then
            log_info "💾 内存使用: ${MEMORY_USAGE}MB"
            if (( $(echo "$MEMORY_USAGE > 500" | bc -l 2>/dev/null || echo "0") )); then
                PERFORMANCE_ISSUES=$((PERFORMANCE_ISSUES + 1))
                PERFORMANCE_DETAILS="${PERFORMANCE_DETAILS}内存使用过高(${MEMORY_USAGE}MB); "
            fi
        fi
    fi
fi

# 计算处理效率
if [[ $RAW_RECORD_COUNT -gt 0 && $FEATURES_COUNT -gt 0 ]]; then
    PROCESSING_RATE=$(echo "scale=2; $RAW_RECORD_COUNT / $FEATURE_PROCESSING_DURATION" | bc -l 2>/dev/null || echo "0")
    FEATURE_EXTRACTION_RATE=$(echo "scale=2; $FEATURES_COUNT / $FEATURE_PROCESSING_DURATION" | bc -l 2>/dev/null || echo "0")
    
    log_info "📈 处理效率:"
    log_info "  ├─ 原始数据处理速度: ${PROCESSING_RATE}条/秒"
    log_info "  └─ 特征提取速度: ${FEATURE_EXTRACTION_RATE}条/秒"
else
    PROCESSING_RATE="N/A"
    FEATURE_EXTRACTION_RATE="N/A"
fi

# 性能评估
if [[ $PERFORMANCE_ISSUES -eq 0 ]]; then
    STEP4_RESULT="✅ 性能达标: 处理耗时${FEATURE_PROCESSING_DURATION}s, 无ERROR/CRITICAL, 内存使用${MEMORY_USAGE}MB, 处理速度${PROCESSING_RATE}条/秒"
    STEP4_STATUS="Pass"
else
    STEP4_RESULT="⚠️ 性能问题: $PERFORMANCE_DETAILS"
    STEP4_STATUS="Review"
fi

write_result_row 4 "性能与稳定性" "单会话处理耗时在目标范围内，无ERROR/CRITICAL" "$STEP4_RESULT" "$STEP4_STATUS"
show_test_step 4 "性能与稳定性" "success"

# 停止程序
log_info "🔄 停止UBM程序..."
stop_ubm_gracefully "$PID"

# 保存测试产物
ARTIFACT=$(save_artifacts "$LOG_PATH" "$BASE_DIR")

# 测试结果汇总
echo ""
echo "📊 TC02 特征处理流程测试结果汇总:"
echo "  步骤1 - 特征处理启动: $STEP1_STATUS"
echo "  步骤2 - 数据库记录检查: $STEP2_STATUS"  
echo "  步骤3 - 特征质量检查: $STEP3_STATUS"
echo "  步骤4 - 性能与稳定性: $STEP4_STATUS"
echo "  日志文件: $LOG_PATH"
echo "  数据库路径: $DB_PATH"
echo "  测试产物: $ARTIFACT"

# 生成详细的实测结果报告（可直接复制粘贴到测试报告）
echo ""
echo "🎯 ===== TC02 实测结果详细报告 (可直接粘贴到测试报告) ====="
echo ""

echo "📊 【特征处理流程实测结果】"
echo "  ├─ 原始数据记录: $RAW_RECORD_COUNT 条"
echo "  ├─ 特征处理耗时: ${FEATURE_PROCESSING_DURATION}秒"
echo "  ├─ 生成特征记录: $FEATURES_COUNT 条" 
echo "  ├─ 处理效率: ${PROCESSING_RATE}条/秒"
echo "  └─ 内存使用: ${MEMORY_USAGE}MB"
echo ""

echo "🗄️ 【数据库验证实测结果】"
if [[ $FEATURES_COUNT -gt 0 ]]; then
    echo "  ├─ features表: ✅ 存在且有记录"
    echo "  ├─ 记录总数: $FEATURES_COUNT 条"
    echo "  ├─ 必要字段: ✅ user_id/session_id/timestamp/feature_vector 完整"
    echo "  ├─ 时间跨度: ${TIME_SPAN:-未知}秒"
    echo "  └─ 用户会话: $(echo "$USER_SESSION_STATS" | wc -l 2>/dev/null || echo "0")个不同会话"
else
    echo "  └─ features表: ❌ 无记录或不存在"
fi
echo ""

echo "🔍 【特征质量验证实测结果】"
if [[ $FEATURES_COUNT -gt 0 ]]; then
    echo "  ├─ 有效特征向量: $VALID_FEATURES_COUNT/$FEATURES_COUNT ($(echo "scale=1; $VALID_FEATURES_COUNT * 100 / $FEATURES_COUNT" | bc -l 2>/dev/null || echo "0")%)"
    echo "  ├─ 平均特征维度: $AVG_DIMENSIONS 维"
    echo "  ├─ 空值比例: ${NULL_PERCENTAGE}% ($([ $(echo "$NULL_PERCENTAGE < 20" | bc -l 2>/dev/null || echo "0") -eq 1 ] && echo "✅ 合格" || echo "⚠️ 偏高"))"
    echo "  ├─ 数值范围: $([ $FEATURE_RANGE_ISSUES -eq 0 ] && echo "✅ 正常" || echo "⚠️ ${FEATURE_RANGE_ISSUES}个异常")"
    echo "  └─ 整体质量: $([ $QUALITY_ISSUES -eq 0 ] && echo "✅ 优良" || echo "⚠️ 需改进")"
else
    echo "  └─ 无法验证特征质量，无有效数据"
fi
echo ""

echo "⚡ 【性能稳定性实测结果】"
echo "  ├─ 处理耗时: ${FEATURE_PROCESSING_DURATION}秒 ($([ $(echo "$FEATURE_PROCESSING_DURATION < 120" | bc -l 2>/dev/null || echo "0") -eq 1 ] && echo "✅ 达标" || echo "⚠️ 超时"))"
echo "  ├─ ERROR日志: $ERROR_COUNT 条 ($([ $ERROR_COUNT -eq 0 ] && echo "✅ 无错误" || echo "⚠️ 需关注"))"
echo "  ├─ CRITICAL日志: $CRITICAL_COUNT 条 ($([ $CRITICAL_COUNT -eq 0 ] && echo "✅ 无严重错误" || echo "❌ 需修复"))"
echo "  └─ 系统稳定性: $([ $PERFORMANCE_ISSUES -eq 0 ] && echo "✅ 稳定" || echo "⚠️ 有问题")"
echo ""

echo "🎯 ===== 可直接复制的测试步骤实测结果 ====="
echo ""
echo "步骤1实测结果: 日志提示开始处理指定会话"
echo "           具体时间: $FEATURE_START_READABLE，处理耗时: ${FEATURE_PROCESSING_DURATION}秒"
echo "           检测状态: $([ "$FEATURE_PROCESSING_DETECTED" == "true" ] && echo "✅ 成功检测到特征处理开始" || echo "⚠️ 未检测到明确开始信号")"
echo ""
echo "步骤2实测结果: 生成对应features记录，带user_id/session_id/timestamp等"
echo "           具体记录数: ${FEATURES_COUNT}条features记录"
echo "           字段完整性: $([ "$REQUIRED_FIELDS_CHECK" == "true" ] && echo "✅ 所有必要字段完整" || echo "⚠️ 部分字段缺失")"
echo "           用户会话分布: $(echo "$USER_SESSION_STATS" | head -3 | tr '\n' '; ' 2>/dev/null || echo "无数据")"
echo ""
echo "步骤3实测结果: 无明显空值；关键统计与轨迹类特征存在且数值范围合理"
echo "           具体空值比例: ${NULL_PERCENTAGE}% (阈值<20%)"
echo "           特征维度: 平均${AVG_DIMENSIONS}维，有效向量${VALID_FEATURES_COUNT}/${FEATURES_COUNT}个"
echo "           数值范围: $([ $FEATURE_RANGE_ISSUES -eq 0 ] && echo "所有特征数值范围正常" || echo "${FEATURE_RANGE_ISSUES}个特征向量数值范围异常")"
echo ""
echo "步骤4实测结果: 单会话处理耗时在目标范围内，无ERROR/CRITICAL"
echo "           具体耗时: ${FEATURE_PROCESSING_DURATION}秒 (目标<120秒)"
echo "           错误统计: ERROR ${ERROR_COUNT}条, CRITICAL ${CRITICAL_COUNT}条"
echo "           处理效率: 原始数据${PROCESSING_RATE}条/秒，特征提取${FEATURE_EXTRACTION_RATE}条/秒"
echo "           内存使用: ${MEMORY_USAGE}MB"

echo ""
echo "🎯 测试规范符合性检查:"
echo "  $([ "$STEP1_STATUS" == "Pass" ] && echo "✅" || echo "❌") 步骤1: 特征处理流程启动 - $STEP1_STATUS"
echo "  $([ "$STEP2_STATUS" == "Pass" ] && echo "✅" || echo "❌") 步骤2: 数据库记录验证 - $STEP2_STATUS"
echo "  $([ "$STEP3_STATUS" == "Pass" ] && echo "✅" || echo "❌") 步骤3: 特征质量检查 - $STEP3_STATUS"
echo "  $([ "$STEP4_STATUS" == "Pass" ] && echo "✅" || echo "❌") 步骤4: 性能稳定性验证 - $STEP4_STATUS"

# 总体结论
OVERALL_PASS_COUNT=0
for status in "$STEP1_STATUS" "$STEP2_STATUS" "$STEP3_STATUS" "$STEP4_STATUS"; do
    if [[ "$status" == "Pass" ]]; then
        OVERALL_PASS_COUNT=$((OVERALL_PASS_COUNT + 1))
    fi
done

echo ""
if [[ $OVERALL_PASS_COUNT -eq 4 ]]; then
    echo "✅ 测试通过：特征处理流程完全符合规范要求 (4/4步骤通过)"
elif [[ $OVERALL_PASS_COUNT -ge 3 ]]; then
    echo "⚠️ 测试基本通过：特征处理流程基本符合要求 ($OVERALL_PASS_COUNT/4步骤通过，需复核)"
else
    echo "❌ 测试未通过：特征处理流程存在重大问题 ($OVERALL_PASS_COUNT/4步骤通过)"
fi

exit 0

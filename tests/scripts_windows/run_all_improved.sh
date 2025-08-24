#!/bin/bash
# Windows UBM 测试套件 - Git Bash 兼容版本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 参数处理
EXE_PATH=""
WORK_DIR=""
VERBOSE=false
SKIP_FAILED=false
FAST_MODE=false

# 解析命令行参数
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
        -Verbose)
            VERBOSE=true
            shift
            ;;
        -SkipFailed)
            SKIP_FAILED=true
            shift
            ;;
        -FastMode)
            FAST_MODE=true
            shift
            ;;
        *)
            echo "用法: $0 -ExePath <exe_path> -WorkDir <work_dir> [-Verbose] [-SkipFailed] [-FastMode]"
            exit 1
            ;;
    esac
done

# 验证参数
if [[ -z "$EXE_PATH" ]] || [[ -z "$WORK_DIR" ]]; then
    echo "错误: 缺少必要参数"
    echo "用法: $0 -ExePath <exe_path> -WorkDir <work_dir> [-Verbose] [-SkipFailed] [-FastMode]"
    echo ""
    echo "示例:"
    echo "  $0 -ExePath \"../../dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\""
    echo "  $0 -ExePath \"../../dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\" -SkipFailed"
    echo "  $0 -ExePath \"../../dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\" -FastMode"
    echo "  $0 -ExePath \"../../dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\" -FastMode -Verbose"
    echo ""
    echo "选项说明:"
    echo "  -FastMode    启用快速测试模式（减少等待时间）"
    echo "  -Verbose     详细输出模式"
    echo "  -SkipFailed  跳过失败的测试"
    exit 1
fi

# 加载公共函数（在参数验证之后）
source "$SCRIPT_DIR/common.sh"

# 设置快速模式环境变量
export FAST_MODE="$FAST_MODE"

if [[ "$FAST_MODE" == "true" ]]; then
    log_info "🚀 启用快速测试模式"
    log_info "  启动等待: 1秒 (正常: 3秒)"
    log_info "  特征等待: 10秒 (正常: 30秒)"
    log_info "  训练等待: 15秒 (正常: 45秒)"
    log_info "  日志等待: 5秒 (正常: 15秒)"
    log_info "  键盘间隔: 30ms (正常: 60ms)"
    log_info "  预计加速: 2-3倍"
else
    log_info "🐌 使用正常测试模式"
fi

# 验证可执行文件
log_info "验证可执行文件..."
log_info "  相对路径: $EXE_PATH"
log_info "  当前工作目录: $(pwd)"
log_info "  脚本目录: $SCRIPT_DIR"

# 尝试解析绝对路径
EXE_ABS_PATH=""
if [[ "$EXE_PATH" == /* ]] || [[ "$EXE_PATH" == [A-Za-z]:* ]]; then
    # 已经是绝对路径
    EXE_ABS_PATH="$EXE_PATH"
    log_info "  绝对路径: $EXE_ABS_PATH"
else
    # 相对路径，尝试解析
    EXE_ABS_PATH="$(realpath "$EXE_PATH" 2>/dev/null || echo '')"
    if [[ -n "$EXE_ABS_PATH" ]]; then
        log_info "  解析的绝对路径: $EXE_ABS_PATH"
    else
        log_info "  无法解析绝对路径"
    fi
fi

if [[ ! -f "$EXE_PATH" ]]; then
    log_error "可执行文件不存在: $EXE_PATH"
    log_error ""
    log_error "请检查以下路径:"
    log_error "  1. 相对路径: $EXE_PATH"
    log_error "  2. 绝对路径: $EXE_ABS_PATH"
    log_error "  3. 当前工作目录: $(pwd)"
    log_error "  4. 脚本目录: $SCRIPT_DIR"
    log_error ""
    log_error "路径调试信息:"
    log_error "  pwd: $(pwd)"
    log_error "  ls -la .:"
    ls -la . 2>/dev/null || log_error "    无法列出当前目录"
    log_error "  ls -la ..:"
    ls -la .. 2>/dev/null || log_error "    无法列出上级目录"
    log_error "  ls -la ../..:"
    ls -la ../.. 2>/dev/null || log_error "    无法列出上上级目录"
    log_error ""
    log_error "解决方案:"
    log_error "  1. 确保已构建 UserBehaviorMonitor.exe"
    log_error "  2. 检查 -ExePath 参数是否正确"
    log_error "  3. 使用绝对路径，例如:"
    log_error "     C:/path/to/UserBehaviorMonitor.exe"
    log_error "  4. 或者先构建程序:"
    log_error "     python setup.py build"
    log_error "     pyinstaller --onefile user_behavior_monitor.py"
    log_error ""
    log_error "当前可用的构建脚本:"
    if [[ -f "../build_windows.py" ]]; then
        log_error "  - ../build_windows.py (Windows专用构建)"
    fi
    if [[ -f "../build_cross_platform.py" ]]; then
        log_error "  - ../build_cross_platform.py (跨平台构建)"
    fi
    if [[ -f "../simple_build.py" ]]; then
        log_error "  - ../simple_build.py (简单构建)"
    fi
    log_error ""
    log_error "示例用法:"
    log_error "  # 使用绝对路径"
    log_error "  $0 -ExePath \"C:/Users/YourName/project/dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\""
    log_error ""
    log_error "  # 使用相对路径（确保文件存在）"
    log_error "  $0 -ExePath \"../../dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\""
    exit 1
fi

log_success "✓ 找到可执行文件: $EXE_PATH"

# 准备工作目录
WORK_CONFIG=$(prepare_work_dir "$WORK_DIR")
BASE_DIR=$(echo "$WORK_CONFIG" | grep -o '"Base":"[^"]*"' | cut -d'"' -f4)
DATA_DIR=$(echo "$WORK_CONFIG" | grep -o '"Data":"[^"]*"' | cut -d'"' -f4)
LOGS_DIR=$(echo "$WORK_CONFIG" | grep -o '"Logs":"[^"]*"' | cut -d'"' -f4)

log_success "✓ 工作目录已准备: $BASE_DIR"
log_info "  数据目录: $DATA_DIR"
log_info "  日志目录: $LOGS_DIR"

# 测试用例列表 - 包含所有10个测试用例
declare -a TEST_CASES=(
    "TC01:TC01_realtime_input_collection.sh:实时输入采集"
    "TC02:TC02_feature_extraction.sh:特征提取功能"
    "TC03:TC03_deep_learning_classification.sh:深度学习分类"
    "TC04:TC04_anomaly_alert.sh:异常告警"
    "TC05:TC05_anomaly_block.sh:异常阻止"
    "TC06:TC06_behavior_fingerprint_management.sh:行为指纹管理"
    "TC07:TC07_collection_metrics.sh:采集指标"
    "TC08:TC08_feature_count_metric.sh:特征数量阈值"
    "TC09:TC09_classification_accuracy_metric.sh:分类准确率指标"
    "TC10:TC10_anomaly_false_alarm_rate.sh:异常误报率"
)

# 测试结果统计
TOTAL=${#TEST_CASES[@]}
PASSED=0
FAILED=0
SKIPPED=0
START_TIME=$(date +%s)

log_info "开始执行测试用例..."
log_info "总计: $TOTAL 个测试用例"
log_info "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 执行测试用例
for test_case in "${TEST_CASES[@]}"; do
    IFS=':' read -r test_name script_name description <<< "$test_case"
    
    echo "=========================================="
    log_info "执行测试: $test_name - $description"
    log_info "脚本: $script_name"
    echo "=========================================="
    
    script_path="$SCRIPT_DIR/$script_name"
    if [[ ! -f "$script_path" ]]; then
        log_warning "⚠️  测试脚本不存在: $script_path"
        ((SKIPPED++))
        continue
    fi
    
    # 检查脚本权限
    if [[ ! -x "$script_path" ]]; then
        chmod +x "$script_path"
    fi
    
    # 执行测试脚本
    test_start_time=$(date +%s)
    log_info "开始时间: $(date '+%H:%M:%S')"
    
    if "$script_path" -ExePath "$EXE_PATH" -WorkDir "$WORK_DIR"; then
        test_exit_code=0
    else
        test_exit_code=$?
    fi
    
    test_end_time=$(date +%s)
    duration=$((test_end_time - test_start_time))
    
    log_info "完成时间: $(date '+%H:%M:%S')"
    log_info "执行时长: ${duration} 秒"
    
    # 检查测试结果
    if [[ $test_exit_code -eq 0 ]]; then
        log_success "✓ 测试完成"
        ((PASSED++))
    else
        log_warning "⚠️  测试完成但退出码非零: $test_exit_code"
        ((FAILED++))
        
        if [[ "$SKIP_FAILED" == "false" ]]; then
            log_info "是否继续执行下一个测试? (y/N)"
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                log_info "用户选择停止测试"
                break
            fi
        fi
    fi
    
    echo ""
done

# 测试结果汇总
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
TOTAL_MINUTES=$((TOTAL_DURATION / 60))

echo "=========================================="
log_success "测试执行完成"
echo "=========================================="
log_info "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
log_info "总耗时: ${TOTAL_MINUTES} 分钟"
echo ""
log_info "测试结果统计:"
log_info "  总计: $TOTAL"
log_info "  通过: $PASSED"
log_info "  失败: $FAILED"
log_info "  跳过: $SKIPPED"

if [[ $TOTAL -gt 0 ]]; then
    SUCCESS_RATE=$((PASSED * 100 / TOTAL))
    log_info "  成功率: ${SUCCESS_RATE}%"
fi

# 生成测试报告
REPORT_PATH="$BASE_DIR/test_report_$(date '+%Y%m%d_%H%M%S').txt"
cat > "$REPORT_PATH" << EOF
Windows UBM 测试报告 - Git Bash 版本
====================================
测试时间: $(date '+%Y-%m-%d %H:%M:%S')
总耗时: ${TOTAL_MINUTES} 分钟

测试结果:
  总计: $TOTAL
  通过: $PASSED
  失败: $FAILED
  跳过: $SKIPPED
  成功率: ${SUCCESS_RATE}%

测试用例详情:
$(for test_case in "${TEST_CASES[@]}"; do
    IFS=':' read -r test_name script_name description <<< "$test_case"
    echo "  $test_name: $description"
done)

工作目录: $BASE_DIR
可执行文件: $EXE_PATH

详细日志请查看: $LOGS_DIR
EOF

log_success "测试报告已保存: $REPORT_PATH"

echo ""
log_success "测试执行完成！"

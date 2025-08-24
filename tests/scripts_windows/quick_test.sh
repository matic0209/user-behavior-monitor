#!/bin/bash
# 快速测试脚本 - 只运行核心测试用例，大幅减少等待时间

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 参数处理
EXE_PATH=""
WORK_DIR=""
VERBOSE=false

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
        *)
            echo "用法: $0 -ExePath <exe_path> -WorkDir <work_dir> [-Verbose]"
            echo ""
            echo "示例:"
            echo "  $0 -ExePath \"../../dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\""
            echo "  $0 -ExePath \"../../dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\" -Verbose"
            echo ""
            echo "说明: 快速测试模式，只运行核心测试用例，预计时间: 5-10分钟"
            exit 1
            ;;
    esac
done

# 验证参数
if [[ -z "$EXE_PATH" ]] || [[ -z "$WORK_DIR" ]]; then
    echo "错误: 缺少必要参数"
    echo "用法: $0 -ExePath <exe_path> -WorkDir <work_dir> [-Verbose]"
    exit 1
fi

# 设置快速模式
export FAST_MODE="true"

# 加载公共函数
source "$SCRIPT_DIR/common.sh"

log_info "🚀 快速测试模式启动"
log_info "预计总时间: 5-10分钟 (正常模式: 20-40分钟)"

# 验证可执行文件
if [[ ! -f "$EXE_PATH" ]]; then
    log_error "可执行文件不存在: $EXE_PATH"
    exit 1
fi

log_success "✓ 找到可执行文件: $EXE_PATH"

# 准备工作目录
WORK_CONFIG=$(prepare_work_dir "$WORK_DIR")
BASE_DIR=$(echo "$WORK_CONFIG" | grep -o '"Base":"[^"]*"' | cut -d'"' -f4)
DATA_DIR=$(echo "$WORK_CONFIG" | grep -o '"Data":"[^"]*"' | cut -d'"' -f4)
LOGS_DIR=$(echo "$WORK_CONFIG" | grep -o '"Logs":"[^"]*"' | cut -d'"' -f4)

log_success "✓ 工作目录已准备: $BASE_DIR"

# 核心测试用例列表（只运行最重要的测试）
declare -a CORE_TEST_CASES=(
    "TC02:TC02_feature_extraction.sh:特征提取功能"
    "TC03:TC03_deep_learning_classification.sh:深度学习分类"
    "TC04:TC04_anomaly_alert.sh:异常告警"
)

# 测试结果统计
TOTAL=${#CORE_TEST_CASES[@]}
PASSED=0
FAILED=0
START_TIME=$(date +%s)

log_info "开始执行核心测试用例..."
log_info "总计: $TOTAL 个核心测试用例"
log_info "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 执行测试用例
for test_case in "${CORE_TEST_CASES[@]}"; do
    IFS=':' read -r test_name script_name description <<< "$test_case"
    
    echo "=========================================="
    log_info "执行测试: $test_name - $description"
    log_info "脚本: $script_name"
    echo "=========================================="
    
    script_path="$SCRIPT_DIR/$script_name"
    if [[ ! -f "$script_path" ]]; then
        log_warning "⚠️  测试脚本不存在: $script_path"
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
    fi
    
    echo ""
done

# 测试结果汇总
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
TOTAL_MINUTES=$((TOTAL_DURATION / 60))

echo "=========================================="
log_success "快速测试执行完成"
echo "=========================================="
log_info "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
log_info "总耗时: ${TOTAL_MINUTES} 分钟"
echo ""
log_info "测试结果统计:"
log_info "  总计: $TOTAL"
log_info "  通过: $PASSED"
log_info "  失败: $FAILED"

if [[ $TOTAL -gt 0 ]]; then
    SUCCESS_RATE=$((PASSED * 100 / TOTAL))
    log_info "  成功率: ${SUCCESS_RATE}%"
fi

# 生成快速测试报告
REPORT_PATH="$BASE_DIR/quick_test_report_$(date '+%Y%m%d_%H%M%S').txt"
cat > "$REPORT_PATH" << EOF
Windows UBM 快速测试报告
========================
测试时间: $(date '+%Y-%m-%d %H:%M:%S')
总耗时: ${TOTAL_MINUTES} 分钟
测试模式: 快速模式 (FAST_MODE=true)

测试结果:
  总计: $TOTAL
  通过: $PASSED
  失败: $FAILED
  成功率: ${SUCCESS_RATE}%

核心测试用例:
$(for test_case in "${CORE_TEST_CASES[@]}"; do
    IFS=':' read -r test_name script_name description <<< "$test_case"
    echo "  $test_name: $description"
done)

工作目录: $BASE_DIR
可执行文件: $EXE_PATH

注意: 这是快速测试模式，只运行核心功能测试
如需完整测试，请运行: ./run_all_improved.sh
EOF

log_success "快速测试报告已保存: $REPORT_PATH"

echo ""
log_success "🚀 快速测试执行完成！"
log_info "如需运行完整测试套件，请使用:"
log_info "  ./run_all_improved.sh -ExePath \"$EXE_PATH\" -WorkDir \"$WORK_DIR\""

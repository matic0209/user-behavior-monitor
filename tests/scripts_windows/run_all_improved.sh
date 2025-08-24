#!/bin/bash
# Windows UBM 测试套件 - Git Bash 兼容版本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 参数处理
EXE_PATH=""
WORK_DIR=""
VERBOSE=false
SKIP_FAILED=false
FAST_MODE=true  # 默认启用快速模式
ULTRA_FAST_MODE=false  # 新增超快模式

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
        -UltraFastMode)
            ULTRA_FAST_MODE=true
            FAST_MODE=true
            shift
            ;;
        -NormalMode)
            FAST_MODE=false
            ULTRA_FAST_MODE=false
            shift
            ;;
        *)
            echo "用法: $0 -ExePath <exe_path> -WorkDir <work_dir> [-Verbose] [-SkipFailed] [-UltraFastMode|-FastMode|-NormalMode]"
            exit 1
            ;;
    esac
done

# 验证参数
if [[ -z "$EXE_PATH" ]] || [[ -z "$WORK_DIR" ]]; then
    echo "错误: 缺少必要参数"
    echo "用法: $0 -ExePath <exe_path> -WorkDir <work_dir> [-Verbose] [-SkipFailed] [-UltraFastMode|-FastMode|-NormalMode]"
    echo ""
    echo "示例:"
    echo "  $0 -ExePath \"../../dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\""
    echo "  $0 -ExePath \"../../dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\" -SkipFailed"
    echo "  $0 -ExePath \"../../dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\" -UltraFastMode"
    echo "  $0 -ExePath \"../../dist/UserBehaviorMonitor.exe\" -WorkDir \"win_test_run\" -UltraFastMode -Verbose"
    echo ""
    echo "选项说明:"
    echo "  -UltraFastMode  启用超快测试模式（默认，最快速度）"
    echo "  -FastMode       启用快速测试模式（平衡速度和准确性）"
    echo "  -NormalMode     使用正常测试模式（最慢但最准确）"
    echo "  -Verbose        详细输出模式"
    echo "  -SkipFailed     跳过失败的测试"
    echo ""
    echo "默认模式: 超快模式（-UltraFastMode）"
    exit 1
fi

# 加载公共函数（在参数验证之后）
source "$SCRIPT_DIR/common.sh"

# 设置快速模式环境变量
export FAST_MODE="$FAST_MODE"
export ULTRA_FAST_MODE="$ULTRA_FAST_MODE"

if [[ "$ULTRA_FAST_MODE" == "true" ]]; then
    log_info "🚀 启用超快测试模式（默认）"
    log_info "  启动等待: 1秒 (正常: 3秒)"
    log_info "  特征等待: 5秒 (正常: 30秒)"
    log_info "  训练等待: 10秒 (正常: 45秒)"
    log_info "  日志等待: 3秒 (正常: 15秒)"
    log_info "  键盘间隔: 20ms (正常: 60ms)"
    log_info "  预计加速: 4-5倍"
    log_info "  ⚠️  注意: 超快模式可能影响测试准确性，适用于开发调试"
elif [[ "$FAST_MODE" == "true" ]]; then
    log_info "⚡ 启用快速测试模式"
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
    
    echo ""
    show_test_case_status "$test_name" "$description" "start"
    
    script_path="$SCRIPT_DIR/$script_name"
    if [[ ! -f "$script_path" ]]; then
        log_warning "⚠️  测试脚本不存在: $script_path"
        ((SKIPPED++))
        show_test_case_status "$test_name" "$description" "error"
        continue
    fi
    
    # 检查脚本权限
    if [[ ! -x "$script_path" ]]; then
        chmod +x "$script_path"
    fi
    
    # 执行测试脚本
    test_start_time=$(date +%s)
    
    if "$script_path" -ExePath "$EXE_PATH" -WorkDir "$WORK_DIR"; then
        test_exit_code=0
        test_result="success"
    else
        test_exit_code=$?
        test_result="error"
    fi
    
    test_end_time=$(date +%s)
    duration=$((test_end_time - test_start_time))
    
    # 显示测试结果
    if [[ $test_exit_code -eq 0 ]]; then
        log_success "✓ 测试完成"
        ((PASSED++))
        show_test_case_status "$test_name" "$description" "success"
    else
        log_warning "⚠️  测试完成但退出码非零: $test_exit_code"
        ((FAILED++))
        show_test_case_status "$test_name" "$description" "error"
        
        if [[ "$SKIP_FAILED" == "false" ]]; then
            log_info "是否继续执行下一个测试? (y/N)"
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                log_info "用户选择停止测试"
                break
            fi
        fi
    fi
    
    # 显示执行时间
    log_info "执行时长: ${duration} 秒"
    
    echo ""
done

# 测试结果汇总
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
TOTAL_MINUTES=$((TOTAL_DURATION / 60))

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                    🏁 测试执行完成"
echo "╠══════════════════════════════════════════════════════════════════════════════════════════════════════╣"
echo "║  结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "║  总耗时: ${TOTAL_MINUTES} 分钟 (${TOTAL_DURATION} 秒)"
echo "║  测试模式: $(if [[ "$ULTRA_FAST_MODE" == "true" ]]; then echo "超快模式"; elif [[ "$FAST_MODE" == "true" ]]; then echo "快速模式"; else echo "正常模式"; fi)"
echo "╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝"

# 显示详细结果汇总
write_result_summary "$TOTAL" "$PASSED" "$FAILED" "0" "0" "$SKIPPED"

echo ""
echo "📁 测试产物位置:"
echo "  工作目录: $WORK_DIR"
echo "  日志目录: $LOGS_DIR"
echo "  数据目录: $DATA_DIR"

# 如果有失败的测试，显示建议
if [[ $FAILED -gt 0 ]]; then
    echo ""
    echo "⚠️  故障排除建议:"
    echo "  1. 检查日志文件中的错误信息"
    echo "  2. 确认可执行文件路径正确"
    echo "  3. 检查工作目录权限"
    echo "  4. 运行环境检测脚本: ./test_windows_compatibility.sh"
fi

# 如果有跳过的测试，显示信息
if [[ $SKIPPED -gt 0 ]]; then
    echo ""
    echo "⏭️  跳过的测试:"
    echo "  1. 检查测试脚本是否存在"
    echo "  2. 确认脚本有执行权限"
    echo "  3. 检查脚本语法是否正确"
fi

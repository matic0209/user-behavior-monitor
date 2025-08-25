#!/bin/bash
# 专门解决"未检测到预测循环标记"问题的脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

EXE_PATH="${1:-../../dist/UserBehaviorMonitor.exe}"
WORK_DIR="${2:-./fix_prediction_test}"

echo "=== 解决预测循环检测问题 ==="
echo "问题: 未检测到预测循环标记"
echo "原因: 日志文件为空（0行）"
echo ""

# 检查EXE是否存在
if [[ ! -f "$EXE_PATH" ]]; then
    echo "[ERROR] EXE文件不存在: $EXE_PATH"
    echo "请确保:"
    echo "1. 已经构建了EXE文件"
    echo "2. 路径正确"
    exit 1
fi

echo "[OK] EXE文件存在: $EXE_PATH"

# 准备工作目录
WORK_CONFIG=$(prepare_work_dir "$WORK_DIR")
BASE_DIR=$(echo "$WORK_CONFIG" | grep -o '"Base":"[^"]*"' | cut -d'"' -f4)
LOGS_DIR=$(echo "$WORK_CONFIG" | grep -o '"Logs":"[^"]*"' | cut -d'"' -f4)

echo "[OK] 工作目录: $BASE_DIR"
echo "[OK] 日志目录: $LOGS_DIR"

# 清理旧日志
rm -f "$LOGS_DIR"/*.log 2>/dev/null
echo "[OK] 已清理旧日志文件"

# 尝试直接运行EXE看看输出
echo ""
echo "=== 步骤1: 直接测试EXE启动 ==="

# 转换为绝对路径，避免cd后路径错误
if [[ "$EXE_PATH" == /* ]] || [[ "$EXE_PATH" == [A-Za-z]:* ]]; then
    ABS_EXE_PATH="$EXE_PATH"
else
    ABS_EXE_PATH="$(cd "$(dirname "$EXE_PATH")" && pwd)/$(basename "$EXE_PATH")"
fi

echo "[DEBUG] 原始路径: $EXE_PATH"
echo "[DEBUG] 绝对路径: $ABS_EXE_PATH"
echo "[DEBUG] 文件是否存在: $(test -f "$ABS_EXE_PATH" && echo "是" || echo "否")"

cd "$BASE_DIR"
echo "在目录 $BASE_DIR 中运行: $ABS_EXE_PATH"

# 启动程序并捕获所有输出
timeout 10s "$ABS_EXE_PATH" > startup_test.log 2>&1 &
TEST_PID=$!

echo "测试进程PID: $TEST_PID"
sleep 3

if kill -0 "$TEST_PID" 2>/dev/null; then
    echo "[OK] 进程正在运行"
    kill -9 "$TEST_PID" 2>/dev/null
else
    echo "[INFO] 进程已退出，检查输出..."
fi

if [[ -f "startup_test.log" ]]; then
    echo ""
    echo "启动输出:"
    echo "=========="
    cat startup_test.log
    echo "=========="
else
    echo "[WARNING] 没有生成启动日志"
fi

# 检查是否生成了日志文件
echo ""
echo "=== 步骤2: 检查日志文件生成 ==="
LOG_FILES=$(find "$LOGS_DIR" -name "*.log" -type f 2>/dev/null)
if [[ -n "$LOG_FILES" ]]; then
    echo "[OK] 发现日志文件:"
    echo "$LOG_FILES" | while IFS= read -r logfile; do
        size=$(wc -l < "$logfile" 2>/dev/null || echo "0")
        echo "  - $(basename "$logfile"): ${size}行"
        if [[ $size -gt 0 ]]; then
            echo "    内容预览:"
            head -5 "$logfile" | while IFS= read -r line; do
                echo "      > $line"
            done
        else
            echo "    [WARNING] 文件为空"
        fi
    done
else
    echo "[ERROR] 未发现任何日志文件"
    echo ""
    echo "可能的原因:"
    echo "1. 应用程序启动失败"
    echo "2. 日志配置错误"
    echo "3. 权限问题"
    echo "4. 依赖缺失"
fi

# 尝试使用Python直接运行
echo ""
echo "=== 步骤3: 尝试Python直接运行 ==="
PYTHON_MAIN="../../user_behavior_monitor.py"

# 同样转换为绝对路径
echo "[DEBUG] Python原始路径: $PYTHON_MAIN"

if [[ "$PYTHON_MAIN" == /* ]] || [[ "$PYTHON_MAIN" == [A-Za-z]:* ]]; then
    ABS_PYTHON_PATH="$PYTHON_MAIN"
    echo "[DEBUG] 已经是绝对路径"
else
    # 更安全的路径转换方法
    PYTHON_DIR=$(dirname "$PYTHON_MAIN")
    PYTHON_FILE=$(basename "$PYTHON_MAIN")
    echo "[DEBUG] 相对目录: $PYTHON_DIR"
    echo "[DEBUG] 文件名: $PYTHON_FILE"
    
    if cd "$PYTHON_DIR" 2>/dev/null; then
        ABS_PYTHON_PATH="$(pwd)/$PYTHON_FILE"
        cd - >/dev/null
        echo "[DEBUG] 路径转换成功"
    else
        echo "[DEBUG] 路径转换失败，使用原始路径"
        ABS_PYTHON_PATH="$PYTHON_MAIN"
    fi
fi

echo "[DEBUG] Python绝对路径: $ABS_PYTHON_PATH"
echo "[DEBUG] Python文件是否存在: $(test -f "$ABS_PYTHON_PATH" && echo "是" || echo "否")"

if [[ -f "$ABS_PYTHON_PATH" ]]; then
    echo "尝试Python版本: $ABS_PYTHON_PATH"
    cd "$BASE_DIR"
    timeout 10s python3 "$ABS_PYTHON_PATH" > python_test.log 2>&1 &
    PYTHON_PID=$!
    
    sleep 3
    if kill -0 "$PYTHON_PID" 2>/dev/null; then
        echo "[OK] Python版本正在运行"
        kill -9 "$PYTHON_PID" 2>/dev/null
    fi
    
    if [[ -f "python_test.log" ]]; then
        echo "Python输出:"
        echo "==========="
        cat python_test.log
        echo "==========="
    fi
    
    # 检查Python版本是否生成日志
    LOG_FILES=$(find "$LOGS_DIR" -name "*.log" -type f -newer startup_test.log 2>/dev/null)
    if [[ -n "$LOG_FILES" ]]; then
        echo "[OK] Python版本生成了日志文件"
    else
        echo "[WARNING] Python版本也没有生成日志"
    fi
else
    echo "[INFO] 未找到Python主文件"
    echo "  原始路径: $PYTHON_MAIN"
    echo "  绝对路径: $ABS_PYTHON_PATH"
    echo "  请检查文件是否存在"
fi

# 检查依赖
echo ""
echo "=== 步骤4: 检查Python依赖 ==="
MISSING_DEPS=""
for dep in "numpy" "pandas" "sklearn" "pynput"; do
    if python3 -c "import $dep" 2>/dev/null; then
        echo "[OK] $dep 已安装"
    else
        echo "[ERROR] $dep 未安装"
        MISSING_DEPS="$MISSING_DEPS $dep"
    fi
done

if [[ -n "$MISSING_DEPS" ]]; then
    echo ""
    echo "[ERROR] 缺少依赖:$MISSING_DEPS"
    echo "请运行: pip install$MISSING_DEPS"
fi

# 给出解决建议
echo ""
echo "=== 解决建议 ==="
if [[ -z "$LOG_FILES" ]]; then
    echo "由于没有生成任何日志文件，建议:"
    echo "1. 检查EXE是否正确构建: python build_cross_platform.py"
    echo "2. 安装缺失的依赖: pip install -r requirements.txt"
    echo "3. 尝试Python版本: python user_behavior_monitor.py"
    echo "4. 检查系统权限和防火墙设置"
else
    echo "日志文件已生成，但可能为空，建议:"
    echo "1. 检查应用程序配置"
    echo "2. 增加日志级别"
    echo "3. 检查启动参数"
fi

echo ""
echo "完成诊断。请根据上述信息解决问题后重新运行测试。"

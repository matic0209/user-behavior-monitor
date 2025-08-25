#!/bin/bash
# 检查并构建EXE文件（如果不存在）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== 检查和构建EXE文件 ==="
echo "项目根目录: $PROJECT_ROOT"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 检查EXE是否存在
EXE_PATH="dist/UserBehaviorMonitor.exe"
if [[ -f "$EXE_PATH" ]]; then
    echo "[OK] EXE文件已存在: $EXE_PATH"
    echo "文件大小: $(du -h "$EXE_PATH" | cut -f1)"
    echo "修改时间: $(stat -c %y "$EXE_PATH" 2>/dev/null || stat -f %Sm "$EXE_PATH" 2>/dev/null || echo "未知")"
    exit 0
fi

echo "[INFO] EXE文件不存在，开始构建..."

# 检查构建脚本
BUILD_SCRIPTS=(
    "build_cross_platform.py"
    "build_windows.py" 
    "simple_build.py"
)

BUILD_SCRIPT=""
for script in "${BUILD_SCRIPTS[@]}"; do
    if [[ -f "$script" ]]; then
        BUILD_SCRIPT="$script"
        echo "[DEBUG] 找到构建脚本: $script"
        break
    fi
done

if [[ -z "$BUILD_SCRIPT" ]]; then
    echo "[ERROR] 未找到构建脚本"
    echo "请确保以下文件之一存在："
    for script in "${BUILD_SCRIPTS[@]}"; do
        echo "  - $script"
    done
    exit 1
fi

# 检查Python环境
echo "[INFO] 检查Python环境..."
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "[ERROR] 未找到Python"
    echo "请安装Python 3.7+"
    exit 1
fi

PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "[OK] Python命令: $PYTHON_CMD"

# 检查依赖
echo "[INFO] 检查依赖..."
MISSING_DEPS=""
REQUIRED_DEPS=("pandas" "scikit-learn" "pynput" "pyinstaller")

for dep in "${REQUIRED_DEPS[@]}"; do
    if ! $PYTHON_CMD -c "import ${dep//-/_}" 2>/dev/null; then
        echo "[MISSING] $dep"
        MISSING_DEPS="$MISSING_DEPS $dep"
    else
        echo "[OK] $dep"
    fi
done

if [[ -n "$MISSING_DEPS" ]]; then
    echo ""
    echo "[INFO] 安装缺失依赖..."
    if [[ -f "requirements.txt" ]]; then
        echo "运行: $PYTHON_CMD -m pip install -r requirements.txt"
        $PYTHON_CMD -m pip install -r requirements.txt
    else
        echo "运行: $PYTHON_CMD -m pip install$MISSING_DEPS"
        $PYTHON_CMD -m pip install$MISSING_DEPS
    fi
    
    if [[ $? -ne 0 ]]; then
        echo "[ERROR] 依赖安装失败"
        echo "请手动运行: pip install -r requirements.txt"
        exit 1
    fi
fi

# 构建EXE
echo ""
echo "[INFO] 开始构建EXE..."
echo "构建脚本: $BUILD_SCRIPT"
echo "命令: $PYTHON_CMD $BUILD_SCRIPT"

$PYTHON_CMD "$BUILD_SCRIPT"
BUILD_EXIT_CODE=$?

if [[ $BUILD_EXIT_CODE -eq 0 ]] && [[ -f "$EXE_PATH" ]]; then
    echo ""
    echo "[SUCCESS] EXE构建成功!"
    echo "位置: $EXE_PATH"
    echo "大小: $(du -h "$EXE_PATH" | cut -f1)"
    echo ""
    echo "现在可以运行测试脚本了:"
    echo "  bash tests/scripts_windows/fix_prediction_detection.sh"
    echo "  bash tests/scripts_windows/run_all_improved.sh"
else
    echo ""
    echo "[ERROR] EXE构建失败"
    echo "退出代码: $BUILD_EXIT_CODE"
    echo ""
    echo "故障排除："
    echo "1. 检查构建日志中的错误信息"
    echo "2. 确保所有依赖已安装: pip install -r requirements.txt"
    echo "3. 尝试不同的构建脚本"
    echo "4. 检查Python版本: python --version"
    exit 1
fi

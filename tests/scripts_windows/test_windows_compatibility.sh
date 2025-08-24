#!/bin/bash
# Windows兼容性测试脚本

echo "🖥️  Windows兼容性测试"
echo "=========================================="

# 检测操作系统
echo "检测操作系统环境..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    echo "✅ 检测到Windows环境 (Git Bash)"
    echo "  OSTYPE: $OSTYPE"
    echo "  OS: Windows"
else
    echo "⚠️  非Windows环境: $OSTYPE"
fi

echo ""

# 检测PowerShell可用性
echo "检测PowerShell可用性..."
if command -v powershell.exe &> /dev/null; then
    echo "✅ PowerShell可用"
    POWERSHELL_VERSION=$(powershell.exe -Command "Get-Host | Select-Object Version | Format-Table -HideTableHeaders" 2>/dev/null | tr -d ' ')
    echo "  版本: $POWERSHELL_VERSION"
else
    echo "❌ PowerShell不可用"
fi

echo ""

# 检测Python可用性
echo "检测Python可用性..."
if command -v python3 &> /dev/null; then
    echo "✅ Python3可用"
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "  版本: $PYTHON_VERSION"
    
    # 检测pyautogui
    if python3 -c "import pyautogui" 2>/dev/null; then
        echo "✅ pyautogui库可用"
    else
        echo "⚠️  pyautogui库不可用"
    fi
else
    echo "❌ Python3不可用"
fi

echo ""

# 检测xdotool可用性
echo "检测xdotool可用性..."
if command -v xdotool &> /dev/null; then
    echo "✅ xdotool可用"
    XDOTOOL_VERSION=$(xdotool version 2>&1)
    echo "  版本: $XDOTOOL_VERSION"
else
    echo "❌ xdotool不可用"
fi

echo ""

# 加载公共函数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

echo "测试鼠标和键盘模拟函数..."
echo "=========================================="

# 测试鼠标移动
echo "测试鼠标移动函数..."
if move_mouse_path 2 100; then
    echo "✅ 鼠标移动测试成功"
else
    echo "❌ 鼠标移动测试失败"
fi

echo ""

# 测试鼠标点击
echo "测试鼠标点击函数..."
if click_left_times 2; then
    echo "✅ 鼠标点击测试成功"
else
    echo "❌ 鼠标点击测试失败"
fi

echo ""

# 测试滚动
echo "测试滚动函数..."
if scroll_vertical 2; then
    echo "✅ 滚动测试成功"
else
    echo "❌ 滚动测试失败"
fi

echo ""

# 测试键盘输入
echo "测试键盘输入函数..."
if send_char_repeated 't' 2 100; then
    echo "✅ 键盘输入测试成功"
else
    echo "❌ 键盘输入测试失败"
fi

echo ""
echo "=========================================="
echo "Windows兼容性测试完成！"
echo ""
echo "如果测试失败，请检查："
echo "1. PowerShell是否可用"
echo "2. 是否有足够的权限运行PowerShell命令"
echo "3. 是否在Windows环境下运行"
echo "4. Git Bash是否正确配置"

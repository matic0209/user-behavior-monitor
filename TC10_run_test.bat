@echo off
REM TC10 预警误报率测试 - Windows批处理脚本
echo ========================================
echo TC10 异常行为告警误报率测试
echo ========================================
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

echo Python环境检查通过
echo.

REM 检查脚本文件是否存在
if not exist "TC10_simple_calculator.py" (
    echo 错误: 未找到TC10_simple_calculator.py脚本文件
    pause
    exit /b 1
)

echo 脚本文件检查通过
echo.

REM 运行TC10测试
echo 开始运行TC10测试...
echo.
python TC10_simple_calculator.py

REM 检查测试结果
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo TC10 测试完成 - 结果: 通过
    echo ========================================
) else (
    echo.
    echo ========================================
    echo TC10 测试完成 - 结果: 失败
    echo ========================================
)

echo.
echo 按任意键退出...
pause >nul

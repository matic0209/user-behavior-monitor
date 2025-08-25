#!/bin/bash
# 应用程序启动诊断脚本
# 专门诊断为什么应用程序启动后日志为空

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

EXE_PATH="${1:-../../dist/UserBehaviorMonitor.exe}"
WORK_DIR="${2:-./startup_diagnosis}"

echo "=== 应用程序启动诊断 ==="
echo "EXE路径: $EXE_PATH"
echo "工作目录: $WORK_DIR"
echo ""

# 检查EXE文件
echo "[STEP 1] 检查EXE文件"
echo "----------------------"
if [[ ! -f "$EXE_PATH" ]]; then
    echo "[ERROR] EXE文件不存在: $EXE_PATH"
    exit 1
fi

EXE_SIZE=$(stat -c%s "$EXE_PATH" 2>/dev/null || echo "unknown")
echo "[OK] EXE文件存在，大小: $EXE_SIZE 字节"

# 检查文件权限
if [[ -x "$EXE_PATH" ]]; then
    echo "[OK] EXE文件有执行权限"
else
    echo "[WARNING] EXE文件可能没有执行权限"
fi

# 准备工作目录
echo ""
echo "[STEP 2] 准备工作目录"
echo "--------------------"
WORK_CONFIG=$(prepare_work_dir "$WORK_DIR")
BASE_DIR=$(echo "$WORK_CONFIG" | grep -o '"Base":"[^"]*"' | cut -d'"' -f4)
LOGS_DIR=$(echo "$WORK_CONFIG" | grep -o '"Logs":"[^"]*"' | cut -d'"' -f4)

echo "[OK] 工作目录: $BASE_DIR"
echo "[OK] 日志目录: $LOGS_DIR"

# 检查目录权限
if [[ -w "$BASE_DIR" ]]; then
    echo "[OK] 工作目录可写"
else
    echo "[ERROR] 工作目录不可写"
fi

if [[ -w "$LOGS_DIR" ]]; then
    echo "[OK] 日志目录可写"
else
    echo "[ERROR] 日志目录不可写"
fi

# 尝试启动应用程序
echo ""
echo "[STEP 3] 启动应用程序"
echo "--------------------"
echo "启动命令: $EXE_PATH"
echo "工作目录: $BASE_DIR"

# 清理旧的日志文件
rm -f "$LOGS_DIR"/*.log 2>/dev/null

# 启动程序并捕获输出
echo "[INFO] 启动应用程序..."
# 转换为绝对路径，避免cd后路径错误
ABS_EXE_PATH=$(cd "$(dirname "$EXE_PATH")" && pwd)/$(basename "$EXE_PATH")
echo "[DEBUG] 绝对EXE路径: $ABS_EXE_PATH"
cd "$BASE_DIR"
"$ABS_EXE_PATH" > "$LOGS_DIR/startup_output.txt" 2> "$LOGS_DIR/startup_error.txt" &
PID=$!

echo "[OK] 应用程序已启动，PID: $PID"

# 检查进程是否存在
sleep 2
if kill -0 "$PID" 2>/dev/null; then
    echo "[OK] 进程仍在运行"
else
    echo "[ERROR] 进程可能已经退出"
    echo ""
    echo "检查启动输出:"
    if [[ -f "$LOGS_DIR/startup_output.txt" ]]; then
        echo "--- 标准输出 ---"
        cat "$LOGS_DIR/startup_output.txt"
    fi
    if [[ -f "$LOGS_DIR/startup_error.txt" ]]; then
        echo "--- 错误输出 ---"
        cat "$LOGS_DIR/startup_error.txt"
    fi
fi

# 等待并检查日志文件生成
echo ""
echo "[STEP 4] 检查日志文件生成"
echo "------------------------"
for i in {1..10}; do
    echo "检查第 $i 次..."
    
    # 列出所有日志文件
    LOG_FILES=$(find "$LOGS_DIR" -name "*.log" -type f 2>/dev/null | head -5)
    if [[ -n "$LOG_FILES" ]]; then
        echo "[OK] 发现日志文件:"
        echo "$LOG_FILES" | while IFS= read -r logfile; do
            if [[ -f "$logfile" ]]; then
                size=$(wc -l < "$logfile" 2>/dev/null || echo "0")
                mtime=$(stat -c %y "$logfile" 2>/dev/null || echo "unknown")
                echo "  - $(basename "$logfile"): ${size}行, 修改时间: $mtime"
                
                # 显示前几行内容
                if [[ $size -gt 0 ]]; then
                    echo "    前3行内容:"
                    head -3 "$logfile" | while IFS= read -r line; do
                        echo "      > $line"
                    done
                fi
            fi
        done
        break
    else
        echo "  未发现日志文件，等待..."
        sleep 2
    fi
done

# 检查进程状态
echo ""
echo "[STEP 5] 检查进程状态"
echo "--------------------"
if kill -0 "$PID" 2>/dev/null; then
    echo "[OK] 进程正在运行"
    
    # 尝试发送rrrr快捷键
    echo ""
    echo "[STEP 6] 测试快捷键功能"
    echo "----------------------"
    echo "发送 rrrr 快捷键..."
    send_char_repeated 'r' 4 100
    
    # 等待并检查日志变化
    sleep 5
    echo "检查日志变化..."
    LOG_FILES=$(find "$LOGS_DIR" -name "*.log" -type f 2>/dev/null)
    if [[ -n "$LOG_FILES" ]]; then
        echo "$LOG_FILES" | while IFS= read -r logfile; do
            if [[ -f "$logfile" ]]; then
                size=$(wc -l < "$logfile" 2>/dev/null || echo "0")
                echo "  - $(basename "$logfile"): ${size}行"
                if [[ $size -gt 0 ]]; then
                    echo "    最后3行:"
                    tail -3 "$logfile" | while IFS= read -r line; do
                        echo "      > $line"
                    done
                fi
            fi
        done
    fi
    
    # 清理
    echo ""
    echo "清理进程..."
    stop_ubm_gracefully "$PID"
else
    echo "[ERROR] 进程已退出"
    
    # 检查退出原因
    if [[ -f "$LOGS_DIR/startup_error.txt" ]]; then
        echo ""
        echo "错误信息:"
        cat "$LOGS_DIR/startup_error.txt"
    fi
fi

echo ""
echo "=== 诊断完成 ==="
echo "日志目录: $LOGS_DIR"
echo "请检查生成的日志文件以获取更多信息"

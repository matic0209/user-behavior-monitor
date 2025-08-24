#!/bin/bash
# Windows UBM 测试套件 - Git Bash 兼容版本

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# 计算项目根目录与默认路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$TESTS_DIR")"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${GRAY}[DEBUG]${NC} $1"
    fi
}

# 工具函数
ensure_dir() {
    local path="$1"
    if [[ ! -d "$path" ]]; then
        mkdir -p "$path"
        log_debug "创建目录: $path"
    fi
}

get_timestamp() {
    date '+%Y-%m-%d_%H-%M-%S'
}

resolve_exe_path() {
    local path="$1"
    if [[ -z "$path" ]]; then
        log_error "ExePath 为空"
        exit 1
    fi
    
    if [[ ! -f "$path" ]]; then
        log_error "可执行文件不存在: $path"
        exit 1
    fi
    
    echo "$(realpath "$path")"
}

prepare_work_dir() {
    local base_dir="$1"
    if [[ -z "$base_dir" ]]; then
        base_dir="$PROJECT_ROOT/win_test_run"
    fi
    
    ensure_dir "$base_dir"
    local abs_path="$(realpath "$base_dir")"
    
    local data_dir="$abs_path/data"
    local logs_dir="$abs_path/logs"
    local artifacts_dir="$abs_path/artifacts"
    
    ensure_dir "$data_dir"
    ensure_dir "$logs_dir"
    ensure_dir "$artifacts_dir"
    
    # 设置环境变量
    export UBM_DATABASE="$data_dir/mouse_data.db"
    
    echo "{\"Base\":\"$abs_path\",\"Data\":\"$data_dir\",\"Logs\":\"$logs_dir\",\"Db\":\"$UBM_DATABASE\"}"
}

# 鼠标和键盘模拟函数
move_mouse_path() {
    local duration_sec="${1:-5}"
    local step="${2:-50}"
    
    log_debug "模拟鼠标移动，持续时间: ${duration_sec}秒，步长: ${step}px"
    
    # 使用xdotool（如果可用）或Python脚本
    if command -v xdotool &> /dev/null; then
        # Linux环境下的xdotool
        local width=$(xdotool getdisplaygeometry | cut -d' ' -f1)
        local height=$(xdotool getdisplaygeometry | cut -d' ' -f2)
        local y=$((height / 2))
        
        for ((x=100; x<width-100; x+=step)); do
            xdotool mousemove "$x" "$y"
            sleep 0.03
        done
    else
        # 使用Python脚本模拟
        python3 -c "
import time
import pyautogui
pyautogui.FAILSAFE = False
width, height = pyautogui.size()
y = height // 2
for x in range(100, width-100, $step):
    pyautogui.moveTo(x, y)
    time.sleep(0.03)
" 2>/dev/null || log_warning "无法模拟鼠标移动，跳过"
    fi
}

click_left_times() {
    local times="${1:-3}"
    log_debug "模拟左键点击 $times 次"
    
    if command -v xdotool &> /dev/null; then
        for ((i=0; i<times; i++)); do
            xdotool click 1
            sleep 0.12
        done
    else
        python3 -c "
import time
import pyautogui
pyautogui.FAILSAFE = False
for i in range($times):
    pyautogui.click()
    time.sleep(0.12)
" 2>/dev/null || log_warning "无法模拟鼠标点击，跳过"
    fi
}

scroll_vertical() {
    local notches="${1:-3}"
    log_debug "模拟垂直滚动 $notches 次"
    
    if command -v xdotool &> /dev/null; then
        for ((i=0; i<${notches#-}; i++)); do
            if [[ $notches -ge 0 ]]; then
                xdotool click 4  # 向上滚动
            else
                xdotool click 5  # 向下滚动
            fi
            sleep 0.15
        done
    else
        python3 -c "
import time
import pyautogui
pyautogui.FAILSAFE = False
notches = $notches
for i in range(abs(notches)):
    if notches >= 0:
        pyautogui.scroll(3)
    else:
        pyautogui.scroll(-3)
    time.sleep(0.15)
" 2>/dev/null || log_warning "无法模拟滚动，跳过"
    fi
}

send_char_repeated() {
    local char="${1:-'a'}"
    local times="${2:-4}"
    local interval_ms="${3:-$KEY_INTERVAL}"

    log_debug "发送字符 '$char' 重复 $times 次，间隔 ${interval_ms}ms"

    if command -v xdotool &> /dev/null; then
        for ((i=0; i<times; i++)); do
            xdotool type "$char"
            sleep $((interval_ms / 1000))
        done
    else
        python3 -c "
import time
import pyautogui
pyautogui.FAILSAFE = False
char = '$char'
times = $times
interval = $interval_ms / 1000.0

for i in range(times):
    pyautogui.typewrite(char)
    time.sleep(interval)
" 2>/dev/null || log_warning "无法发送字符，跳过"
    fi

    sleep 2 # Wait for program to process hotkey
    log_info "已发送快捷键: $char 重复 $times 次"
}

# 进程管理函数
start_ubm() {
    local exe="$1"
    local cwd="$2"
    
    log_debug "启动UBM程序: $exe，工作目录: $cwd"
    
    # 检查可执行文件是否存在
    if [[ ! -f "$exe" ]]; then
        log_error "可执行文件不存在: $exe"
        log_error "请检查以下路径:"
        log_error "  1. 相对路径: $exe"
        log_error "  2. 绝对路径: $(realpath "$exe" 2>/dev/null || echo '无法解析')"
        log_error "  3. 当前工作目录: $(pwd)"
        log_error ""
        log_error "解决方案:"
        log_error "  1. 确保已构建 UserBehaviorMonitor.exe"
        log_error "  2. 检查 -ExePath 参数是否正确"
        log_error "  3. 使用绝对路径，例如:"
        log_error "     C:/path/to/UserBehaviorMonitor.exe"
        log_error "  4. 或者先构建程序:"
        log_error "     python setup.py build"
        log_error "     pyinstaller --onefile user_behavior_monitor.py"
        exit 1
    fi
    
    # 检查文件是否可执行
    if [[ ! -x "$exe" ]]; then
        log_warning "文件存在但不可执行，尝试添加执行权限: $exe"
        chmod +x "$exe" 2>/dev/null || log_warning "无法添加执行权限"
    fi
    
    # 在切换工作目录前，先解析可执行文件的绝对路径
    local exe_abs_path=""
    if [[ "$exe" == /* ]] || [[ "$exe" == [A-Za-z]:* ]]; then
        # 已经是绝对路径
        exe_abs_path="$exe"
    else
        # 相对路径，转换为绝对路径
        exe_abs_path="$(realpath "$exe" 2>/dev/null || echo "$exe")"
        if [[ ! -f "$exe_abs_path" ]]; then
            # 如果realpath失败，尝试基于当前目录构建绝对路径
            exe_abs_path="$(pwd)/$exe"
        fi
    fi
    
    log_debug "可执行文件绝对路径: $exe_abs_path"
    
    # 切换到工作目录
    cd "$cwd"
    
    log_info "正在启动程序: $exe_abs_path"
    log_info "工作目录: $(pwd)"
    
    # 启动程序（后台运行）
    "$exe_abs_path" &
    local pid=$!
    
    # 等待程序启动
    sleep $STARTUP_WAIT
    
    # 检查进程是否还在运行
    if kill -0 "$pid" 2>/dev/null; then
        log_success "程序启动成功，PID: $pid"
        echo "$pid"
    else
        log_error "程序启动失败"
        log_error "请检查:"
        log_error "  1. 程序是否有依赖缺失"
        log_error "  2. 是否有权限问题"
        log_error "  3. 程序是否崩溃"
        exit 1
    fi
}

stop_ubm_gracefully() {
    local proc="$1"
    
    log_debug "优雅停止UBM程序，PID: $proc"
    
    # 发送退出快捷键 qqqq
    send_char_repeated 'q' 4 80
    
    # 等待程序退出
    sleep 2
    
    # 如果进程还在运行，强制终止
    if kill -0 "$proc" 2>/dev/null; then
        log_warning "程序未响应退出信号，强制终止"
        kill -9 "$proc" 2>/dev/null || true
    fi
}

# 日志处理函数
get_latest_log_path() {
    local logs_dir="$1"
    
    if [[ ! -d "$logs_dir" ]]; then
        return 1
    fi
    
    # 查找最新的日志文件
    local latest_log=$(find "$logs_dir" -name "*.log" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [[ -n "$latest_log" ]]; then
        echo "$latest_log"
    else
        return 1
    fi
}

wait_for_latest_log() {
    local logs_dir="$1"
    local timeout_sec="${2:-15}"
    local interval_ms="${3:-500}"
    
    log_debug "等待最新日志文件，超时时间: ${timeout_sec}秒"
    
    local deadline=$((SECONDS + timeout_sec))
    
    while [[ $SECONDS -lt $deadline ]]; do
        local log_path=$(get_latest_log_path "$logs_dir")
        if [[ -n "$log_path" ]]; then
            log_debug "找到日志文件: $log_path"
            echo "$log_path"
            return 0
        fi
        
        sleep $((interval_ms / 1000))
    done
    
    log_warning "超时，未找到日志文件"
    return 1
}

wait_log_contains() {
    local log_path="$1"
    local patterns=("${@:2}")
    local timeout_sec="${patterns[-1]:-$LOG_WAIT}"
    local interval_ms="${patterns[-2]:-$PROCESS_CHECK_INTERVAL}"

    # 移除最后两个参数（超时时间和间隔）
    patterns=("${patterns[@]:0:$((${#patterns[@]}-2))}")

    if [[ ! -f "$log_path" ]]; then
        log_warning "日志文件不存在: $log_path"
        return 1
    fi

    log_debug "等待日志包含关键字，超时时间: ${timeout_sec}秒"
    log_debug "搜索模式: ${patterns[*]}"

    local deadline=$((SECONDS + timeout_sec))
    local attempts=0
    local last_hits=()

    # 初始化last_hits数组
    for pattern in "${patterns[@]}"; do
        last_hits+=("0")
    done

    while [[ $SECONDS -lt $deadline ]]; do
        ((attempts++))
        local current_hits=()
        local found_any=false

        for i in "${!patterns[@]}"; do
            local pattern="${patterns[$i]}"
            local count=0

            if grep -q "$pattern" "$log_path" 2>/dev/null; then
                count=$(grep -c "$pattern" "$log_path" 2>/dev/null || echo "0")
            fi

            current_hits+=("$count")

            if [[ $count -gt 0 ]]; then
                found_any=true
                if [[ $attempts -eq 1 ]]; then
                    log_success "找到关键字 '$pattern': $count 次"
                fi
            fi
        done

        local new_matches=false
        for i in "${!patterns[@]}"; do
            if [[ ${current_hits[$i]} -gt ${last_hits[$i]} ]]; then
                new_matches=true
                break
            fi
        done

        if [[ "$found_any" == "true" ]]; then
            if [[ "$new_matches" == "true" ]]; then
                log_info "发现新的日志匹配 (尝试 $attempts)"
            fi

            local all_found=true
            for count in "${current_hits[@]}"; do
                if [[ $count -eq 0 ]]; then
                    all_found=false
                    break
                fi
            done

            if [[ "$all_found" == "true" ]]; then
                log_success "所有关键字都已找到，提前返回"
                return 0
            fi
        fi

        last_hits=("${current_hits[@]}")

        if [[ $((attempts % 5)) -eq 0 ]]; then
            local remaining=$((deadline - SECONDS))
            log_info "等待中... 剩余时间: ${remaining}秒 (尝试 $attempts)"
        fi

        sleep $((interval_ms / 1000))
    done

    log_warning "超时，未找到所有关键字"
    log_info "最终匹配结果:"
    for i in "${!patterns[@]}"; do
        local pattern="${patterns[$i]}"
        local count="${last_hits[$i]}"
        local status="✗"
        if [[ $count -gt 0 ]]; then
            status="✓"
        fi
        log_info "  $status $pattern: $count 次"
    done

    return 1
}

# 结果处理函数
write_result_header() {
    local title="$1"
    echo ""
    echo "=========================================="
    echo "$title"
    echo "=========================================="
}

write_result_table_header() {
    echo "| Index | Action | Expectation | Actual | Conclusion |"
    echo "| --- | --- | --- | --- | --- |"
}

write_result_row() {
    local index="$1"
    local action="$2"
    local expectation="$3"
    local actual="$4"
    local conclusion="$5"
    
    echo "| $index | $action | $expectation | $actual | $conclusion |"
}

save_artifacts() {
    local log_path="$1"
    local work_base="$2"
    
    if [[ ! -f "$log_path" ]]; then
        echo "no-log-found"
        return
    fi
    
    local timestamp=$(get_timestamp)
    local artifacts_dir="$work_base/artifacts/$timestamp"
    ensure_dir "$artifacts_dir"
    
    local log_name=$(basename "$log_path")
    local artifact_path="$artifacts_dir/$log_name"
    
    cp "$log_path" "$artifact_path" 2>/dev/null || echo "copy-failed"
    
    echo "$artifact_path"
}

# 主函数（如果直接运行此脚本）
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    log_info "公共函数库已加载"
    log_info "ExePath: $EXE_PATH"
    log_info "WorkDir: $WORK_DIR"
fi

# 快速测试模式配置
FAST_MODE=${FAST_MODE:-true}  # 默认启用快速模式
ULTRA_FAST_MODE=${ULTRA_FAST_MODE:-false}

if [[ "$ULTRA_FAST_MODE" == "true" ]]; then
    # 超快模式：最小等待时间（开发调试用）
    STARTUP_WAIT=1      # 程序启动等待时间（秒）
    FEATURE_WAIT=5      # 特征处理等待时间（秒）
    TRAINING_WAIT=10    # 模型训练等待时间（秒）
    LOG_WAIT=3          # 日志等待时间（秒）
    KEY_INTERVAL=20     # 键盘输入间隔（毫秒）
    MOUSE_INTERVAL=30   # 鼠标操作间隔（毫秒）
    PROCESS_CHECK_INTERVAL=100  # 进程检查间隔（毫秒）
elif [[ "$FAST_MODE" == "true" ]]; then
    # 快速模式：减少等待时间
    STARTUP_WAIT=1      # 程序启动等待时间（秒）
    FEATURE_WAIT=10     # 特征处理等待时间（秒）
    TRAINING_WAIT=15    # 模型训练等待时间（秒）
    LOG_WAIT=5          # 日志等待时间（秒）
    KEY_INTERVAL=30     # 键盘输入间隔（毫秒）
    MOUSE_INTERVAL=50   # 鼠标操作间隔（毫秒）
    PROCESS_CHECK_INTERVAL=200  # 进程检查间隔（毫秒）
else
    # 正常模式：保持原有等待时间
    STARTUP_WAIT=3      # 程序启动等待时间（秒）
    FEATURE_WAIT=30     # 特征处理等待时间（秒）
    TRAINING_WAIT=45    # 模型训练等待时间（秒）
    LOG_WAIT=15         # 日志等待时间（秒）
    KEY_INTERVAL=60     # 键盘输入间隔（毫秒）
    MOUSE_INTERVAL=100  # 鼠标操作间隔（毫秒）
    PROCESS_CHECK_INTERVAL=500  # 进程检查间隔（毫秒）
fi

log_debug "测试模式: ${ULTRA_FAST_MODE:-false} (超快) / ${FAST_MODE:-false} (快速) / ${FAST_MODE:-false} (正常)"
log_debug "启动等待: ${STARTUP_WAIT}秒"
log_debug "特征等待: ${FEATURE_WAIT}秒"
log_debug "训练等待: ${TRAINING_WAIT}秒"

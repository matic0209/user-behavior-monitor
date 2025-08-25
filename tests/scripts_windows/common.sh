#!/bin/bash
# Windows UBM 测试套件 - Git Bash 兼容版本

# 注意：不使用set -e，这样测试脚本不会因为单个测试失败而退出
# set -e  # 遇到错误时退出

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

# 备选模拟函数（当PowerShell失败时使用）
simulate_actions_fallback() {
    local action_type="$1"
    local duration="${2:-2}"
    
    log_warning "使用备选方案模拟 $action_type，持续时间: ${duration}秒"
    log_info "提示: 安装pyautogui可获得更好的输入模拟效果"
    log_info "运行: python3 tests/scripts_windows/install_pyautogui.py"
    
    # 创建模拟日志
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_file="$BASE_DIR/simulated_actions.log"
    
    case "$action_type" in
        "mouse_move")
            echo "[$timestamp] SIMULATED: Mouse moved across screen for ${duration}s" >> "$log_file"
            ;;
        "mouse_click")
            echo "[$timestamp] SIMULATED: Mouse clicked 3 times" >> "$log_file"
            ;;
        "scroll")
            echo "[$timestamp] SIMULATED: Mouse scrolled 3 times" >> "$log_file"
            ;;
        "keyboard")
            echo "[$timestamp] SIMULATED: Keyboard input 'rrrr' sent" >> "$log_file"
            ;;
        *)
            echo "[$timestamp] SIMULATED: Unknown action '$action_type'" >> "$log_file"
            ;;
    esac
    
    # 等待指定时间
    sleep "$duration"
    return 0
}

# 鼠标和键盘模拟函数
move_mouse_path() {
    local duration_sec="${1:-5}"
    local step="${2:-50}"
    
    log_debug "模拟鼠标移动，持续时间: ${duration_sec}秒，步长: ${step}px"
    
    # 检测操作系统
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows环境 (Git Bash)：优先使用 Python(pyautogui)，PowerShell 可选
        
        # 首先检查Python和pyautogui是否可用
        if python3 -c "import pyautogui; print('pyautogui available')" 2>/dev/null >/dev/null; then
            log_debug "使用Python pyautogui进行鼠标模拟"
            if python3 -c "
import time
import pyautogui
pyautogui.FAILSAFE = False
try:
    width, height = pyautogui.size()
    y = height // 2
    for x in range(100, width-100, $step):
        pyautogui.moveTo(x, y)
        time.sleep(0.03)
    print('Mouse movement completed successfully')
except Exception as e:
    print(f'Error: {e}')
    exit(1)
" 2>/dev/null; then
                return 0
            else
                log_warning "pyautogui执行失败，尝试PowerShell方案"
            fi
        else
            log_debug "pyautogui不可用，尝试PowerShell方案"
        fi
        
        # PowerShell方案
        if [[ "$USE_POWERSHELL" == "true" ]] || [[ "$USE_POWERSHELL" == "" ]]; then
            if powershell.exe -Command "
                Add-Type -AssemblyName System.Windows.Forms
                \$screen = [System.Windows.Forms.Screen]::PrimaryScreen
                \$width = \$screen.Bounds.Width
                \$height = \$screen.Bounds.Height
                \$y = \$height / 2
                for (\$x = 100; \$x -lt (\$width - 100); \$x += $step) {
                    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point(\$x, \$y)
                    Start-Sleep -Milliseconds 30
                }
            " 2>/dev/null; then
                return 0
            fi
        fi
        log_warning "Windows下未能模拟鼠标移动，使用备选方案"
        simulate_actions_fallback "mouse_move" "$duration_sec"
        return $?
        
    elif command -v xdotool &> /dev/null; then
        # Linux环境下的xdotool
        local width=$(xdotool getdisplaygeometry | cut -d' ' -f1)
        local height=$(xdotool getdisplaygeometry | cut -d' ' -f2)
        local y=$((height / 2))
        
        for ((x=100; x<width-100; x+=step)); do
            xdotool mousemove "$x" "$y"
            sleep 0.03
        done
        return 0
    else
        # 使用Python脚本模拟
        if python3 -c "
import time
import pyautogui
pyautogui.FAILSAFE = False
width, height = pyautogui.size()
y = height // 2
for x in range(100, width-100, $step):
    pyautogui.moveTo(x, y)
    time.sleep(0.03)
" 2>/dev/null; then
            return 0
        else
            log_warning "Python模拟失败，使用备选方案"
            simulate_actions_fallback "mouse_move" "$duration_sec"
            return $?
        fi
    fi
}

click_left_times() {
    local times="${1:-3}"
    log_debug "模拟左键点击 $times 次"
    
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows环境 (Git Bash)：优先使用 Python(pyautogui)，PowerShell 可选
        if python3 -c "
import time
import pyautogui
pyautogui.FAILSAFE = False
for i in range($times):
    pyautogui.click()
    time.sleep(0.12)
" 2>/dev/null; then
            return 0
        elif [[ "$USE_POWERSHELL" == "true" ]]; then
            if powershell.exe -Command "
                Add-Type -AssemblyName System.Windows.Forms
                for (\$i = 0; \$i -lt $times; \$i++) {
                    [System.Windows.Forms.Cursor]::Position = [System.Windows.Forms.Cursor]::Position
                    Start-Sleep -Milliseconds 120
                }
            " 2>/dev/null; then
                return 0
            fi
        fi
        log_warning "Windows下未能模拟点击，使用备选方案"
        simulate_actions_fallback "mouse_click" 1
        return $?
        
    elif command -v xdotool &> /dev/null; then
        for ((i=0; i<times; i++)); do
            xdotool click 1
            sleep 0.12
        done
        return 0
    else
        if python3 -c "
import time
import pyautogui
pyautogui.FAILSAFE = False
for i in range($times):
    pyautogui.click()
    time.sleep(0.12)
" 2>/dev/null; then
            return 0
        else
            log_warning "Python模拟失败，使用备选方案"
            simulate_actions_fallback "mouse_click" 1
            return $?
        fi
    fi
}

scroll_vertical() {
    local notches="${1:-3}"
    log_debug "模拟垂直滚动 $notches 次"
    
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows环境 (Git Bash)：优先使用 Python(pyautogui)，PowerShell 可选
        if python3 -c "
import time
import pyautogui
pyautogui.FAILSAFE = False
notches = $notches
for i in range(abs(notches)):
    pyautogui.scroll(3 if notches >= 0 else -3)
    time.sleep(0.15)
" 2>/dev/null; then
            return 0
        elif [[ "$USE_POWERSHELL" == "true" ]]; then
            if powershell.exe -Command "
                Add-Type -AssemblyName System.Windows.Forms
                \$notches = $notches
                for (\$i = 0; \$i -lt [Math]::Abs(\$notches); \$i++) {
                    if (\$notches -ge 0) {
                        [System.Windows.Forms.SendKeys]::SendWait('{WHEEL_UP}')
                    } else {
                        [System.Windows.Forms.SendKeys]::SendWait('{WHEEL_DOWN}')
                    }
                    Start-Sleep -Milliseconds 150
                }
            " 2>/dev/null; then
                return 0
            fi
        fi
        log_warning "Windows下未能模拟滚动，使用备选方案"
        simulate_actions_fallback "scroll" 1
        return $?
        
    elif command -v xdotool &> /dev/null; then
        for ((i=0; i<${notches#-}; i++)); do
            if [[ $notches -ge 0 ]]; then
                xdotool click 4  # 向上滚动
            else
                xdotool click 5  # 向下滚动
            fi
            sleep 0.15
        done
        return 0
    else
        if python3 -c "
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
" 2>/dev/null; then
            return 0
        else
            log_warning "Python模拟失败，使用备选方案"
            simulate_actions_fallback "scroll" 1
            return $?
        fi
    fi
}

send_char_repeated() {
    local char="${1:-'a'}"
    local times="${2:-4}"
    local interval_ms="${3:-$KEY_INTERVAL}"

    log_debug "发送字符 '$char' 重复 $times 次，间隔 ${interval_ms}ms"

    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows环境 (Git Bash)：优先使用 Python(pyautogui)，PowerShell 可选
        
        # 首先检查Python和pyautogui是否可用
        if python3 -c "import pyautogui; print('pyautogui available')" 2>/dev/null >/dev/null; then
            log_debug "使用Python pyautogui进行键盘模拟"
            if python3 -c "
import time
import pyautogui
pyautogui.FAILSAFE = False
try:
    char = '$char'
    times = $times
    interval = $interval_ms / 1000.0
    for i in range(times):
        pyautogui.typewrite(char)
        time.sleep(interval)
    print('Keyboard input completed successfully')
except Exception as e:
    print(f'Error: {e}')
    exit(1)
" 2>/dev/null; then
                return 0
            else
                log_warning "pyautogui键盘输入失败，尝试PowerShell方案"
            fi
        else
            log_debug "pyautogui不可用，尝试PowerShell方案"
        fi
        
        # PowerShell方案
        if [[ "$USE_POWERSHELL" == "true" ]] || [[ "$USE_POWERSHELL" == "" ]]; then
            if powershell.exe -Command "
                Add-Type -AssemblyName System.Windows.Forms
                \$char = '$char'
                \$times = $times
                \$interval = $interval_ms
                for (\$i = 0; \$i -lt \$times; \$i++) {
                    [System.Windows.Forms.SendKeys]::SendWait(\$char)
                    Start-Sleep -Milliseconds \$interval
                }
            " 2>/dev/null; then
                return 0
            fi
        fi
        log_warning "Windows下未能模拟键盘输入，使用备选方案"
        simulate_actions_fallback "keyboard" 1
        return $?
        
    elif command -v xdotool &> /dev/null; then
        for ((i=0; i<times; i++)); do
            xdotool type "$char"
            sleep $((interval_ms / 1000))
        done
        return 0
    else
        if python3 -c "
import time
import pyautogui
pyautogui.FAILSAFE = False
char = '$char'
times = $times
interval = $interval_ms / 1000.0

for i in range(times):
    pyautogui.typewrite(char)
    time.sleep(interval)
" 2>/dev/null; then
            return 0
        else
            log_warning "Python模拟失败，使用备选方案"
            simulate_actions_fallback "keyboard" 1
            return $?
        fi
    fi
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

# 专门用于立即终止预测循环的函数
stop_ubm_immediately() {
    local proc="$1"
    local reason="${2:-预测循环检测}"
    
    log_warning "立即终止UBM程序 (原因: $reason)，PID: $proc"
    
    # 无等待，立即强杀
    if kill -0 "$proc" 2>/dev/null; then
        kill -9 "$proc" 2>/dev/null || true
        
        # Windows环境立即使用taskkill
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
            taskkill //PID "$proc" //F 2>/dev/null || true
            taskkill //IM "UserBehaviorMonitor.exe" //F 2>/dev/null || true
        fi
    fi
    
    log_success "进程 $proc 已立即终止"
}

stop_ubm_gracefully() {
    local proc="$1"
    
    log_debug "强制停止UBM程序，PID: $proc (专为预测循环优化)"
    
    # 第一步：立即强制终止主进程
    if kill -0 "$proc" 2>/dev/null; then
        log_warning "立即强制终止主进程 PID: $proc"
        kill -9 "$proc" 2>/dev/null || true
        sleep 0.5
    fi

    # 第二步：Windows环境下使用taskkill确保彻底终止
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        # 尝试通过PID终止
        if kill -0 "$proc" 2>/dev/null; then
            log_warning "使用 taskkill /F 强制终止 PID: $proc"
            taskkill //PID "$proc" //F 2>/dev/null || true
            sleep 0.5
        fi
        
        # 终止所有相关进程（包括可能的子进程和线程）
        log_warning "终止所有 UserBehaviorMonitor 相关进程"
        taskkill //IM "UserBehaviorMonitor.exe" //F 2>/dev/null || true
        taskkill //IM "python.exe" //F //FI "WINDOWTITLE eq *UserBehaviorMonitor*" 2>/dev/null || true
        sleep 0.5
        
        # 额外安全措施：终止所有可能相关的Python进程
        if pgrep -f "UserBehaviorMonitor" >/dev/null 2>&1; then
            log_warning "发现残留的UserBehaviorMonitor进程，强制清理"
            pkill -9 -f "UserBehaviorMonitor" 2>/dev/null || true
        fi
    else
        # Linux/macOS环境
        if kill -0 "$proc" 2>/dev/null; then
            log_warning "Linux/macOS环境下强制终止进程组"
            kill -9 -"$proc" 2>/dev/null || kill -9 "$proc" 2>/dev/null || true
        fi
    fi
    
    # 第三步：等待进程完全退出
    sleep 1
    
    # 第四步：最终验证
    local attempts=0
    while kill -0 "$proc" 2>/dev/null && [[ $attempts -lt 5 ]]; do
        log_warning "进程 $proc 仍在运行，等待终止... (尝试 $((attempts+1))/5)"
        sleep 1
        attempts=$((attempts+1))
    done
    
    if kill -0 "$proc" 2>/dev/null; then
        log_error "严重警告：进程 $proc 无法终止，可能需要手动干预"
        log_error "请手动运行: taskkill //PID $proc //F 或重启系统"
        return 1
    else
        log_success "进程 $proc 及其所有线程已完全终止"
        return 0
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
    
    # 使用更可靠的超时机制
    local end_time=$(( $(date +%s) + timeout_sec ))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        # 添加错误处理，避免 find 命令卡住
        local log_path=""
        if [[ -d "$logs_dir" ]]; then
            # 使用 timeout 命令限制 find 执行时间（如果可用）
            if command -v timeout >/dev/null 2>&1; then
                log_path=$(timeout 3 find "$logs_dir" -name "*.log" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- 2>/dev/null || echo "")
            else
                log_path=$(find "$logs_dir" -name "*.log" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- 2>/dev/null || echo "")
            fi
        fi
        
        if [[ -n "$log_path" && -f "$log_path" ]]; then
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
    echo "╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                    $title"
    echo "╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝"
}

write_result_table_header() {
    echo ""
    echo "┌─────┬──────────────────────────────────────┬──────────────────────────────────────┬──────────────────────────────────────┬────────────┐"
    echo "│ No. │ Action                               │ Expectation                          │ Actual                                │ Status     │"
    echo "├─────┼──────────────────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────┼────────────┤"
}

write_result_row() {
    local index="$1"
    local action="$2"
    local expectation="$3"
    local actual="$4"
    local conclusion="$5"
    
    # 格式化状态显示
    local status_icon=""
    local status_color=""
    
    case "$conclusion" in
        "Pass"|"PASS")
            status_icon="✅"
            status_color="$GREEN"
            ;;
        "Fail"|"FAIL")
            status_icon="❌"
            status_color="$RED"
            ;;
        "Partial"|"PARTIAL")
            status_icon="⚠️"
            status_color="$YELLOW"
            ;;
        "Review"|"REVIEW")
            status_icon="🔍"
            status_color="$BLUE"
            ;;
        "N/A"|"NA")
            status_icon="➖"
            status_color="$GRAY"
            ;;
        *)
            status_icon="❓"
            status_color="$CYAN"
            ;;
    esac
    
    # 格式化实际结果（限制长度，避免表格过宽）
    local actual_formatted="$actual"
    if [[ ${#actual_formatted} -gt 35 ]]; then
        actual_formatted="${actual_formatted:0:32}..."
    fi
    
    # 格式化动作和期望（限制长度）
    local action_formatted="$action"
    local expectation_formatted="$expectation"
    
    if [[ ${#action_formatted} -gt 35 ]]; then
        action_formatted="${action_formatted:0:32}..."
    fi
    
    if [[ ${#expectation_formatted} -gt 35 ]]; then
        expectation_formatted="${expectation_formatted:0:32}..."
    fi
    
    # 输出格式化的行
    printf "│ %3s │ %-36s │ %-36s │ %-36s │ %s%-10s%s │\n" \
        "$index" \
        "$action_formatted" \
        "$expectation_formatted" \
        "$actual_formatted" \
        "$status_color" \
        "$status_icon $conclusion" \
        "$NC"
}

write_result_footer() {
    echo "└─────┴──────────────────────────────────────┴──────────────────────────────────────┴──────────────────────────────────────┴────────────┘"
}

write_result_summary() {
    local total="$1"
    local passed="$2"
    local failed="$3"
    local partial="$4"
    local review="$5"
    local skipped="$6"
    
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                    📊 测试结果汇总"
    echo "╠══════════════════════════════════════════════════════════════════════════════════════════════════════╣"
    
    # 计算通过率
    local pass_rate=0
    if [[ $total -gt 0 ]]; then
        pass_rate=$(echo "scale=1; $passed * 100 / $total" | bc -l 2>/dev/null || echo "0")
    fi
    
    # 状态图标和颜色
    local total_icon="📋"
    local passed_icon="✅"
    local failed_icon="❌"
    local partial_icon="⚠️"
    local review_icon="🔍"
    local skipped_icon="⏭️"
    local rate_icon="📈"
    
    echo "║  $total_icon 总计测试: $total"
    echo "║  $passed_icon 通过: $GREEN$passed$NC"
    echo "║  $failed_icon 失败: $RED$failed$NC"
    echo "║  $partial_icon 部分通过: $YELLOW$partial$NC"
    echo "║  $review_icon 需要复核: $BLUE$review$NC"
    echo "║  $skipped_icon 跳过: $GRAY$skipped$NC"
    echo "║  $rate_icon 通过率: $GREEN${pass_rate}%$NC"
    
    echo "╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝"
    
    # 结果评估
    echo ""
    if [[ $failed -eq 0 ]] && [[ $total -gt 0 ]]; then
        echo "🎉 恭喜！所有测试都通过了！"
    elif [[ $failed -eq 0 ]] && [[ $partial -gt 0 ]]; then
        echo "✅ 测试基本通过，但有部分测试需要关注"
    elif [[ $failed -gt 0 ]]; then
        echo "⚠️  有测试失败，请检查失败原因"
    fi
}

# 测试步骤状态显示
show_test_step() {
    local step_number="$1"
    local step_description="$2"
    local step_status="$3"
    
    case "$step_status" in
        "start")
            echo ""
            echo "🔄 步骤 $step_number: $step_description"
            echo "   └─ 开始执行..."
            ;;
        "success")
            echo "   └─ ✅ 完成"
            ;;
        "warning")
            echo "   └─ ⚠️  警告"
            ;;
        "error")
            echo "   └─ ❌ 错误"
            ;;
        "info")
            echo "   └─ ℹ️  信息"
            ;;
    esac
}

# 测试用例状态显示
show_test_case_status() {
    local test_name="$1"
    local test_description="$2"
    local test_status="$3"
    
    echo ""
    case "$test_status" in
        "start")
            echo "🚀 开始测试: $test_name"
            echo "📝 描述: $test_description"
            echo "⏱️  开始时间: $(date '+%H:%M:%S')"
            ;;
        "success")
            echo "✅ 测试完成: $test_name"
            echo "📝 描述: $test_description"
            echo "⏱️  完成时间: $(date '+%H:%M:%S')"
            ;;
        "warning")
            echo "⚠️  测试警告: $test_name"
            echo "📝 描述: $test_description"
            echo "⏱️  完成时间: $(date '+%H:%M:%S')"
            ;;
        "error")
            echo "❌ 测试失败: $test_name"
            echo "📝 描述: $test_description"
            echo "⏱️  完成时间: $(date '+%H:%M:%S')"
            ;;
    esac
}

# 性能指标显示
show_performance_metrics() {
    local test_name="$1"
    local metrics="$2"
    
    echo ""
    echo "📊 性能指标 - $test_name"
    echo "┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐"
    echo "$metrics" | while IFS= read -r line; do
        echo "│ $line"
    done
    echo "└─────────────────────────────────────────────────────────────────────────────────────────────────────┘"
}

# 错误详情显示
show_error_details() {
    local error_message="$1"
    local error_code="${2:-0}"
    
    echo ""
    echo "❌ 错误详情"
    echo "┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐"
    echo "│ 错误代码: $error_code"
    echo "│ 错误信息: $error_message"
    echo "│ 时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "└─────────────────────────────────────────────────────────────────────────────────────────────────────┘"
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
# 是否允许在 Windows 下调用 PowerShell（默认禁用，以适配纯 Git Bash 环境）
USE_POWERSHELL=${USE_POWERSHELL:-false}

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

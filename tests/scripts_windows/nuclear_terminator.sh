#!/bin/bash
# 核弹级进程终止器 - 强制终止所有UserBehaviorMonitor进程
# 用法: nuclear_terminator.sh <最大运行时间秒数>

MAX_TIME=${1:-30}  # 默认30秒后强制终止
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

log_warning "核弹级终止器启动 - 将在 ${MAX_TIME} 秒后强制终止所有UBM进程"

# 后台监控进程
(
    sleep $MAX_TIME
    log_error "时间到！执行核弹级终止..."
    
    # 终止所有相关进程
    taskkill //IM "UserBehaviorMonitor.exe" //F //T 2>/dev/null || true
    taskkill //IM "python.exe" //F //FI "COMMANDLINE eq *UserBehaviorMonitor*" 2>/dev/null || true
    taskkill //IM "python.exe" //F //FI "COMMANDLINE eq *user_behavior_monitor*" 2>/dev/null || true
    
    # 使用更激进的方法
    pkill -f "UserBehaviorMonitor" 2>/dev/null || true
    pkill -f "user_behavior_monitor" 2>/dev/null || true
    
    log_error "核弹级终止完成！所有UBM进程应已终止"
    
    # 创建终止标记文件
    touch "$SCRIPT_DIR/nuclear_termination_executed"
    
) &

NUCLEAR_PID=$!
log_info "核弹级终止器后台进程启动，PID: $NUCLEAR_PID"

# 返回后台进程PID，供调用脚本使用
echo $NUCLEAR_PID

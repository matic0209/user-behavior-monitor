#!/bin/bash
# 模拟任务管理器的进程终止行为

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

log_info "=== 模拟任务管理器终止UBM进程 ==="

# 1. 先查看所有相关进程
log_info "1. 查找所有UBM相关进程..."
echo "当前运行的UBM进程："

# 使用多种方法查找进程
echo "方法1 - tasklist 查找："
tasklist | grep -i "UserBehaviorMonitor\|python" | grep -i behavior || echo "  未找到"

echo ""
echo "方法2 - wmic 查找："
wmic process where "name like '%UserBehavior%' or (name like '%python%' and commandline like '%behavior%')" get processid,name,commandline 2>/dev/null || echo "  wmic不可用"

echo ""
echo "方法3 - ps 查找："
ps aux | grep -i "UserBehavior\|behavior" | grep -v grep || echo "  未找到"

# 2. 获取所有相关的PID
log_info "2. 收集所有需要终止的PID..."
PIDS_TO_KILL=()

# 方法1：通过tasklist获取
while IFS= read -r line; do
    if [[ -n "$line" ]]; then
        PID=$(echo "$line" | awk '{print $2}')
        if [[ "$PID" =~ ^[0-9]+$ ]]; then
            PIDS_TO_KILL+=("$PID")
            echo "  找到PID: $PID (tasklist)"
        fi
    fi
done < <(tasklist /FI "IMAGENAME eq UserBehaviorMonitor.exe" /FO CSV /NH 2>/dev/null | tr -d '"' || echo "")

# 方法2：通过wmic获取
while IFS= read -r line; do
    if [[ -n "$line" && "$line" != "ProcessId" ]]; then
        PID=$(echo "$line" | tr -d ' ')
        if [[ "$PID" =~ ^[0-9]+$ ]]; then
            PIDS_TO_KILL+=("$PID")
            echo "  找到PID: $PID (wmic)"
        fi
    fi
done < <(wmic process where "name='UserBehaviorMonitor.exe'" get processid /format:csv 2>/dev/null | cut -d',' -f2 | tail -n +2 || echo "")

# 方法3：查找相关的python进程
while IFS= read -r line; do
    if [[ -n "$line" ]]; then
        PID=$(echo "$line" | awk '{print $2}')
        if [[ "$PID" =~ ^[0-9]+$ ]]; then
            PIDS_TO_KILL+=("$PID")
            echo "  找到Python PID: $PID"
        fi
    fi
done < <(tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH 2>/dev/null | tr -d '"' | while read line; do
    if echo "$line" | grep -qi "behavior"; then
        echo "$line"
    fi
done || echo "")

# 去重PID
UNIQUE_PIDS=($(printf "%s\n" "${PIDS_TO_KILL[@]}" | sort -u))

if [[ ${#UNIQUE_PIDS[@]} -eq 0 ]]; then
    log_info "未找到任何UBM进程，可能已经终止"
    return 0
fi

log_info "3. 发现 ${#UNIQUE_PIDS[@]} 个进程需要终止: ${UNIQUE_PIDS[*]}"

# 3. 逐个终止进程，模拟任务管理器
log_info "4. 开始终止进程（模拟任务管理器）..."

for pid in "${UNIQUE_PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
        log_info "终止进程 PID: $pid"
        
        # 模拟任务管理器的终止方式
        taskkill //PID "$pid" //F 2>/dev/null && echo "  taskkill成功" || echo "  taskkill失败"
        
        # 等待一下
        sleep 0.5
        
        # 检查是否成功
        if ! kill -0 "$pid" 2>/dev/null; then
            log_success "  PID $pid 已成功终止"
        else
            log_warning "  PID $pid 仍在运行，尝试更激进的方法"
            kill -9 "$pid" 2>/dev/null || true
            sleep 0.5
            if ! kill -0 "$pid" 2>/dev/null; then
                log_success "  PID $pid 已强制终止"
            else
                log_error "  PID $pid 无法终止！"
            fi
        fi
    else
        log_info "PID $pid 已经不存在"
    fi
done

# 4. 最终验证
log_info "5. 最终验证 - 检查是否还有残留进程..."
sleep 2

REMAINING=$(tasklist | grep -i "UserBehaviorMonitor" | wc -l)
if [[ $REMAINING -eq 0 ]]; then
    log_success "✅ 所有UBM进程已成功终止"
else
    log_warning "⚠️  仍有 $REMAINING 个UBM进程在运行"
    tasklist | grep -i "UserBehaviorMonitor"
fi

log_info "=== 任务管理器模拟终止完成 ==="

#!/bin/bash
# 测试多进程终止功能

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

log_info "=== 多进程终止测试 ==="

# 1. 显示当前所有UserBehaviorMonitor进程
log_info "1. 当前UserBehaviorMonitor进程状态："
echo "任务管理器视图："
tasklist | grep -i "UserBehaviorMonitor" || echo "  未找到UserBehaviorMonitor进程"

echo ""
echo "进程数量统计："
PROCESS_COUNT=$(tasklist | grep -i "UserBehaviorMonitor" | wc -l)
echo "  发现 $PROCESS_COUNT 个UserBehaviorMonitor进程"

if [[ $PROCESS_COUNT -eq 0 ]]; then
    log_info "没有UserBehaviorMonitor进程在运行，测试结束"
    exit 0
fi

if [[ $PROCESS_COUNT -gt 1 ]]; then
    log_warning "⚠️  发现多个UserBehaviorMonitor进程！这可能是无限循环的原因"
    echo "详细信息："
    tasklist /FI "IMAGENAME eq UserBehaviorMonitor.exe" /FO LIST | grep -E "PID|映像名称|会话名"
fi

# 2. 使用我们的killer脚本
log_info "2. 使用task_manager_killer.sh终止所有进程..."
bash "$SCRIPT_DIR/task_manager_killer.sh"

# 3. 验证结果
log_info "3. 验证终止结果..."
sleep 2
REMAINING_COUNT=$(tasklist | grep -i "UserBehaviorMonitor" | wc -l)

if [[ $REMAINING_COUNT -eq 0 ]]; then
    log_success "✅ 成功终止所有UserBehaviorMonitor进程"
else
    log_error "❌ 仍有 $REMAINING_COUNT 个UserBehaviorMonitor进程在运行"
    echo "残留进程："
    tasklist | grep -i "UserBehaviorMonitor"
    
    log_warning "执行最后的清理尝试..."
    # 最后的清理尝试
    taskkill //IM "UserBehaviorMonitor.exe" //F //T 2>/dev/null || true
    wmic process where "name='UserBehaviorMonitor.exe'" delete 2>/dev/null || true
    
    sleep 2
    FINAL_COUNT=$(tasklist | grep -i "UserBehaviorMonitor" | wc -l)
    if [[ $FINAL_COUNT -eq 0 ]]; then
        log_success "✅ 最终清理成功"
    else
        log_error "❌ 最终清理失败，仍有 $FINAL_COUNT 个进程"
    fi
fi

log_info "=== 多进程终止测试完成 ==="

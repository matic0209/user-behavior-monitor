#!/usr/bin/env python3
"""
进程管理工具
用于检查和清理重复的UserBehaviorMonitor进程
"""

import os
import sys
import psutil
import signal
import time
from pathlib import Path
from src.utils.console_encoding import ensure_utf8_console

# 确保控制台UTF-8，防止 GBK 编码报错
ensure_utf8_console()

def find_user_behavior_processes():
    """查找所有UserBehaviorMonitor相关进程"""
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            # 检查进程名称
            if proc.info['name']:
                if 'UserBehaviorMonitor' in proc.info['name'] or 'user_behavior_monitor' in proc.info['name']:
                    processes.append(proc)
                    continue
            
            # 检查命令行参数
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline']).lower()
                if 'userbehaviormonitor' in cmdline or 'user_behavior_monitor' in cmdline:
                    processes.append(proc)
                    continue
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return processes

def kill_process(pid, force=False):
    """终止进程"""
    try:
        process = psutil.Process(pid)
        
        if force:
            process.kill()
            print(f"✓ 强制终止进程 {pid}")
        else:
            process.terminate()
            print(f"✓ 发送终止信号到进程 {pid}")
            
        return True
    except psutil.NoSuchProcess:
        print(f"⚠️ 进程 {pid} 已不存在")
        return True
    except psutil.AccessDenied:
        print(f"❌ 无权限终止进程 {pid}")
        return False
    except Exception as e:
        print(f"❌ 终止进程 {pid} 失败: {e}")
        return False

def cleanup_pid_files():
    """清理PID文件"""
    pid_files = [
        Path(tempfile.gettempdir()) / "user_behavior_monitor.pid",
        Path(".") / "uos20_monitor.pid",
        Path(".") / "monitor.pid"
    ]
    
    cleaned = 0
    for pid_file in pid_files:
        if pid_file.exists():
            try:
                pid_file.unlink()
                print(f"✓ 已清理PID文件: {pid_file}")
                cleaned += 1
            except Exception as e:
                print(f"⚠️ 清理PID文件失败 {pid_file}: {e}")
    
    return cleaned

def show_process_info(processes):
    """显示进程信息"""
    if not processes:
        print("📋 没有找到UserBehaviorMonitor相关进程")
        return
    
    print(f"📋 找到 {len(processes)} 个UserBehaviorMonitor相关进程:")
    print("-" * 80)
    print(f"{'PID':<8} {'名称':<20} {'创建时间':<20} {'命令行'}")
    print("-" * 80)
    
    for proc in processes:
        try:
            create_time = datetime.fromtimestamp(proc.info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
            name = proc.info['name'] or 'Unknown'
            cmdline = ' '.join(proc.info['cmdline'][:3]) + ('...' if len(proc.info['cmdline']) > 3 else '')
            
            print(f"{proc.info['pid']:<8} {name:<20} {create_time:<20} {cmdline}")
        except Exception as e:
            print(f"{proc.info['pid']:<8} {'Error':<20} {'Error':<20} {e}")

def main():
    """主函数"""
    print("🔧 UserBehaviorMonitor 进程管理工具")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python process_manager.py list     - 列出所有相关进程")
        print("  python process_manager.py kill     - 终止所有相关进程")
        print("  python process_manager.py force    - 强制终止所有相关进程")
        print("  python process_manager.py cleanup  - 清理PID文件")
        print("  python process_manager.py all      - 执行完整清理")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        processes = find_user_behavior_processes()
        show_process_info(processes)
        
    elif command == 'kill':
        processes = find_user_behavior_processes()
        if not processes:
            print("📋 没有找到需要终止的进程")
            return
        
        print(f"🔄 正在终止 {len(processes)} 个进程...")
        for proc in processes:
            kill_process(proc.info['pid'], force=False)
        
        # 等待进程终止
        time.sleep(2)
        
        # 检查是否还有进程
        remaining = find_user_behavior_processes()
        if remaining:
            print(f"⚠️ 仍有 {len(remaining)} 个进程未终止，可能需要强制终止")
        else:
            print("✅ 所有进程已成功终止")
            
    elif command == 'force':
        processes = find_user_behavior_processes()
        if not processes:
            print("📋 没有找到需要终止的进程")
            return
        
        print(f"🔄 正在强制终止 {len(processes)} 个进程...")
        for proc in processes:
            kill_process(proc.info['pid'], force=True)
        
        time.sleep(1)
        remaining = find_user_behavior_processes()
        if remaining:
            print(f"❌ 仍有 {len(remaining)} 个进程无法终止")
        else:
            print("✅ 所有进程已强制终止")
            
    elif command == 'cleanup':
        cleaned = cleanup_pid_files()
        if cleaned > 0:
            print(f"✅ 已清理 {cleaned} 个PID文件")
        else:
            print("📋 没有找到需要清理的PID文件")
            
    elif command == 'all':
        print("🔄 执行完整清理...")
        
        # 1. 列出进程
        processes = find_user_behavior_processes()
        show_process_info(processes)
        
        # 2. 终止进程
        if processes:
            print(f"\n🔄 正在终止 {len(processes)} 个进程...")
            for proc in processes:
                kill_process(proc.info['pid'], force=False)
            
            time.sleep(2)
            
            # 检查是否需要强制终止
            remaining = find_user_behavior_processes()
            if remaining:
                print(f"🔄 强制终止剩余的 {len(remaining)} 个进程...")
                for proc in remaining:
                    kill_process(proc.info['pid'], force=True)
        
        # 3. 清理PID文件
        cleaned = cleanup_pid_files()
        
        # 4. 最终检查
        final_check = find_user_behavior_processes()
        if not final_check:
            print("✅ 清理完成！没有发现相关进程")
        else:
            print(f"⚠️ 清理完成，但仍有 {len(final_check)} 个进程无法终止")
            
    else:
        print(f"❌ 未知命令: {command}")
        print("可用命令: list, kill, force, cleanup, all")

if __name__ == "__main__":
    import tempfile
    from datetime import datetime
    main()

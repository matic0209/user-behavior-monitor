#!/usr/bin/env python3
"""
告警监控工具
用于查看和管理告警文件，特别适用于无控制台环境
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

def show_alert_files():
    """显示告警文件列表"""
    alert_dir = Path('logs/alerts')
    
    if not alert_dir.exists():
        print("📁 告警目录不存在: logs/alerts")
        return
    
    print("📁 告警文件列表:")
    print("-" * 80)
    
    alert_files = list(alert_dir.glob('alert_*.txt'))
    alert_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not alert_files:
        print("📋 暂无告警文件")
        return
    
    for i, alert_file in enumerate(alert_files[:10], 1):  # 显示最近10个
        stat = alert_file.stat()
        file_time = datetime.fromtimestamp(stat.st_mtime)
        file_size = stat.st_size
        
        print(f"{i:2d}. {alert_file.name}")
        print(f"    时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    大小: {file_size} 字节")
        print()

def show_realtime_alerts():
    """显示实时告警"""
    realtime_file = Path('logs/alerts/realtime_alerts.txt')
    
    if not realtime_file.exists():
        print("📋 实时告警文件不存在")
        return
    
    print("📋 实时告警记录:")
    print("-" * 80)
    
    try:
        with open(realtime_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 显示最近20条告警
        for line in lines[-20:]:
            print(line.strip())
            
    except Exception as e:
        print(f"❌ 读取实时告警文件失败: {e}")

def show_alert_content(file_index):
    """显示指定告警文件内容"""
    alert_dir = Path('logs/alerts')
    
    if not alert_dir.exists():
        print("📁 告警目录不存在")
        return
    
    alert_files = list(alert_dir.glob('alert_*.txt'))
    alert_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not alert_files:
        print("📋 暂无告警文件")
        return
    
    try:
        file_index = int(file_index) - 1
        if 0 <= file_index < len(alert_files):
            alert_file = alert_files[file_index]
            print(f"📄 告警文件内容: {alert_file.name}")
            print("=" * 80)
            
            with open(alert_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
        else:
            print(f"❌ 文件索引超出范围: {file_index + 1}")
    except ValueError:
        print("❌ 无效的文件索引")
    except Exception as e:
        print(f"❌ 读取告警文件失败: {e}")

def monitor_alerts():
    """实时监控告警"""
    realtime_file = Path('logs/alerts/realtime_alerts.txt')
    
    if not realtime_file.exists():
        print("📋 实时告警文件不存在，等待告警...")
    
    print("🔍 开始实时监控告警...")
    print("按 Ctrl+C 停止监控")
    print("-" * 80)
    
    try:
        last_size = realtime_file.stat().st_size if realtime_file.exists() else 0
        
        while True:
            if realtime_file.exists():
                current_size = realtime_file.stat().st_size
                
                if current_size > last_size:
                    # 有新告警
                    with open(realtime_file, 'r', encoding='utf-8') as f:
                        f.seek(last_size)
                        new_content = f.read()
                        if new_content.strip():
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] 新告警:")
                            print(new_content.strip())
                            print("-" * 40)
                    
                    last_size = current_size
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ 监控已停止")

def clear_old_alerts(days=7):
    """清理旧告警文件"""
    alert_dir = Path('logs/alerts')
    
    if not alert_dir.exists():
        print("📁 告警目录不存在")
        return
    
    cutoff_time = datetime.now() - timedelta(days=days)
    deleted_count = 0
    
    print(f"🧹 清理 {days} 天前的告警文件...")
    
    for alert_file in alert_dir.glob('alert_*.txt'):
        try:
            file_time = datetime.fromtimestamp(alert_file.stat().st_mtime)
            if file_time < cutoff_time:
                alert_file.unlink()
                deleted_count += 1
                print(f"🗑️ 已删除: {alert_file.name}")
        except Exception as e:
            print(f"❌ 删除文件失败 {alert_file.name}: {e}")
    
    print(f"✅ 清理完成，共删除 {deleted_count} 个文件")

def show_alert_stats():
    """显示告警统计信息"""
    alert_dir = Path('logs/alerts')
    
    if not alert_dir.exists():
        print("📁 告警目录不存在")
        return
    
    alert_files = list(alert_dir.glob('alert_*.txt'))
    
    if not alert_files:
        print("📋 暂无告警记录")
        return
    
    # 统计信息
    total_alerts = len(alert_files)
    today_alerts = 0
    week_alerts = 0
    
    today = datetime.now().date()
    week_ago = datetime.now() - timedelta(days=7)
    
    severity_stats = {}
    
    for alert_file in alert_files:
        try:
            file_time = datetime.fromtimestamp(alert_file.stat().st_mtime)
            
            # 时间统计
            if file_time.date() == today:
                today_alerts += 1
            if file_time > week_ago:
                week_alerts += 1
            
            # 严重程度统计
            with open(alert_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'CRITICAL' in content:
                    severity_stats['critical'] = severity_stats.get('critical', 0) + 1
                elif 'WARNING' in content:
                    severity_stats['warning'] = severity_stats.get('warning', 0) + 1
                else:
                    severity_stats['info'] = severity_stats.get('info', 0) + 1
                    
        except Exception:
            pass
    
    print("📊 告警统计信息:")
    print("-" * 40)
    print(f"总告警数: {total_alerts}")
    print(f"今日告警: {today_alerts}")
    print(f"本周告警: {week_alerts}")
    print()
    print("严重程度分布:")
    for severity, count in severity_stats.items():
        print(f"  {severity.upper()}: {count}")
    
    # 最近告警
    if alert_files:
        latest_file = max(alert_files, key=lambda x: x.stat().st_mtime)
        latest_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
        print(f"\n最近告警: {latest_time.strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """主函数"""
    print("🔧 告警监控工具")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python alert_monitor.py list           - 显示告警文件列表")
        print("  python alert_monitor.py realtime       - 显示实时告警")
        print("  python alert_monitor.py show <index>   - 显示指定告警文件内容")
        print("  python alert_monitor.py monitor        - 实时监控告警")
        print("  python alert_monitor.py clear [days]   - 清理旧告警文件")
        print("  python alert_monitor.py stats          - 显示告警统计")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        show_alert_files()
        
    elif command == 'realtime':
        show_realtime_alerts()
        
    elif command == 'show':
        if len(sys.argv) >= 3:
            show_alert_content(sys.argv[2])
        else:
            print("❌ 请指定文件索引")
            
    elif command == 'monitor':
        monitor_alerts()
        
    elif command == 'clear':
        days = int(sys.argv[2]) if len(sys.argv) >= 3 else 7
        clear_old_alerts(days)
        
    elif command == 'stats':
        show_alert_stats()
        
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
System用户告警监控工具
专门用于监控和显示system用户环境下的告警信息
"""

import os
import sys
import time
import json
import subprocess
import platform
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import threading

class SystemAlertMonitor:
    def __init__(self, config_file=None):
        self.project_root = Path(__file__).parent
        self.alert_dir = self.project_root / "logs" / "alerts"
        self.realtime_file = self.alert_dir / "realtime_alerts.txt"
        self.log_dir = self.project_root / "logs"
        
        # 加载配置
        if config_file and Path(config_file).exists():
            self.config = self.load_config(config_file)
        else:
            self.config = self.get_default_config()
        
        # 监控状态
        self.is_monitoring = False
        self.last_check_time = None
        self.alert_count = 0
        
    def load_config(self, config_file):
        """加载配置文件"""
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  加载配置文件失败: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            'alert': {
                'file_alert': {
                    'directory': 'logs/alerts',
                    'realtime_file': 'realtime_alerts.txt'
                },
                'monitoring': {
                    'check_interval': 60,
                    'max_alert_age': 86400
                }
            }
        }
    
    def check_environment(self):
        """检查运行环境"""
        print("🔍 检查运行环境...")
        
        env_info = {
            'platform': platform.system(),
            'user_id': os.getuid() if hasattr(os, 'getuid') else 'unknown',
            'username': os.getenv('USER', os.getenv('USERNAME', 'unknown')),
            'is_system_user': os.getuid() == 0 if hasattr(os, 'getuid') else False,
            'display': os.getenv('DISPLAY', 'not_set'),
            'home': os.getenv('HOME', 'not_set')
        }
        
        print(f"平台: {env_info['platform']}")
        print(f"用户ID: {env_info['user_id']}")
        print(f"用户名: {env_info['username']}")
        print(f"是否system用户: {env_info['is_system_user']}")
        print(f"显示环境: {env_info['display']}")
        print(f"主目录: {env_info['home']}")
        
        return env_info
    
    def get_recent_alerts(self, hours=24):
        """获取最近的告警"""
        alerts = []
        
        if not self.alert_dir.exists():
            print("⚠️  告警目录不存在")
            return alerts
        
        # 检查实时告警文件
        if self.realtime_file.exists():
            try:
                with open(self.realtime_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-50:]:  # 最近50行
                        if line.strip():
                            alerts.append(line.strip())
            except Exception as e:
                print(f"⚠️  读取实时告警文件失败: {e}")
        
        # 检查告警文件
        try:
            alert_files = list(self.alert_dir.glob('*.txt'))
            alert_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for alert_file in alert_files[:10]:  # 最近10个文件
                if alert_file.name != 'realtime_alerts.txt':
                    try:
                        with open(alert_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            alerts.append(f"文件: {alert_file.name}")
                            alerts.append(content[:200] + "..." if len(content) > 200 else content)
                    except Exception as e:
                        print(f"⚠️  读取告警文件失败 {alert_file}: {e}")
        except Exception as e:
            print(f"⚠️  扫描告警文件失败: {e}")
        
        return alerts
    
    def get_system_logs(self):
        """获取系统日志"""
        logs = []
        
        try:
            if platform.system() == 'Linux':
                # 获取syslog中的相关记录
                result = subprocess.run([
                    'journalctl', 
                    '--since', '1 hour ago',
                    '--grep', 'UserBehaviorMonitor',
                    '--no-pager'
                ], capture_output=True, text=True, timeout=30)
                
                if result.stdout:
                    logs.extend(result.stdout.split('\n')[-20:])  # 最近20行
                    
            elif platform.system() == 'Windows':
                # Windows事件日志
                print("ℹ️  Windows事件日志需要管理员权限")
                
        except Exception as e:
            print(f"⚠️  获取系统日志失败: {e}")
        
        return logs
    
    def get_monitor_logs(self):
        """获取监控日志"""
        logs = []
        
        if not self.log_dir.exists():
            return logs
        
        try:
            log_files = list(self.log_dir.glob('*.log'))
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for log_file in log_files[:3]:  # 最近3个日志文件
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 获取包含告警或错误的最新行
                        alert_lines = [line for line in lines[-100:] 
                                     if 'alert' in line.lower() or 
                                        'warning' in line.lower() or 
                                        'error' in line.lower()]
                        logs.extend(alert_lines[-10:])  # 最近10行
                except Exception as e:
                    print(f"⚠️  读取日志文件失败 {log_file}: {e}")
                    
        except Exception as e:
            print(f"⚠️  扫描日志文件失败: {e}")
        
        return logs
    
    def display_alerts(self, alerts, title="告警信息"):
        """显示告警信息"""
        if not alerts:
            print(f"📭 暂无{title}")
            return
        
        print(f"\n📋 {title}:")
        print("=" * 80)
        
        for i, alert in enumerate(alerts, 1):
            print(f"{i:2d}. {alert}")
            if i % 10 == 0:  # 每10条暂停一下
                print("-" * 40)
        
        print("=" * 80)
    
    def monitor_realtime(self, interval=60):
        """实时监控告警"""
        print(f"🔍 开始实时监控告警 (间隔: {interval}秒)")
        print("按 Ctrl+C 停止监控")
        
        self.is_monitoring = True
        last_file_size = 0
        
        try:
            while self.is_monitoring:
                # 检查实时告警文件
                if self.realtime_file.exists():
                    current_size = self.realtime_file.stat().st_size
                    
                    if current_size > last_file_size:
                        # 文件有新内容
                        try:
                            with open(self.realtime_file, 'r', encoding='utf-8') as f:
                                f.seek(last_file_size)
                                new_content = f.read()
                                if new_content.strip():
                                    print(f"\n🚨 新告警 ({datetime.now().strftime('%H:%M:%S')}):")
                                    print(new_content.strip())
                        except Exception as e:
                            print(f"⚠️  读取新告警失败: {e}")
                        
                        last_file_size = current_size
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⏹️  停止实时监控")
            self.is_monitoring = False
    
    def create_alert_summary(self):
        """创建告警摘要"""
        print("\n📊 创建告警摘要...")
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'environment': self.check_environment(),
            'alert_files': [],
            'recent_alerts': [],
            'system_logs': [],
            'monitor_logs': []
        }
        
        # 统计告警文件
        if self.alert_dir.exists():
            alert_files = list(self.alert_dir.glob('*.txt'))
            summary['alert_files'] = [
                {
                    'name': f.name,
                    'size': f.stat().st_size,
                    'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in alert_files
            ]
        
        # 获取最近告警
        summary['recent_alerts'] = self.get_recent_alerts()
        
        # 获取系统日志
        summary['system_logs'] = self.get_system_logs()
        
        # 获取监控日志
        summary['monitor_logs'] = self.get_monitor_logs()
        
        # 保存摘要
        summary_file = self.alert_dir / f"alert_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"✅ 告警摘要已保存: {summary_file}")
        except Exception as e:
            print(f"⚠️  保存告警摘要失败: {e}")
        
        return summary
    
    def run_monitoring(self, mode='summary', interval=60):
        """运行监控"""
        print("🚨 System用户告警监控工具")
        print("=" * 50)
        
        # 检查环境
        env_info = self.check_environment()
        
        if mode == 'summary':
            # 显示摘要
            print("\n📋 告警摘要:")
            alerts = self.get_recent_alerts()
            self.display_alerts(alerts, "最近告警")
            
            system_logs = self.get_system_logs()
            self.display_alerts(system_logs, "系统日志")
            
            monitor_logs = self.get_monitor_logs()
            self.display_alerts(monitor_logs, "监控日志")
            
            # 创建摘要文件
            self.create_alert_summary()
            
        elif mode == 'realtime':
            # 实时监控
            self.monitor_realtime(interval)
            
        elif mode == 'continuous':
            # 连续监控
            while True:
                print(f"\n🔄 检查告警 ({datetime.now().strftime('%H:%M:%S')})")
                alerts = self.get_recent_alerts()
                self.display_alerts(alerts, "最近告警")
                time.sleep(interval)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='System用户告警监控工具')
    parser.add_argument('--mode', choices=['summary', 'realtime', 'continuous'], 
                       default='summary', help='监控模式')
    parser.add_argument('--interval', type=int, default=60, 
                       help='检查间隔（秒）')
    parser.add_argument('--config', type=str, 
                       help='配置文件路径')
    
    args = parser.parse_args()
    
    # 创建监控器
    monitor = SystemAlertMonitor(args.config)
    
    # 运行监控
    try:
        monitor.run_monitoring(args.mode, args.interval)
    except KeyboardInterrupt:
        print("\n⏹️  监控已停止")
    except Exception as e:
        print(f"❌ 监控出错: {e}")

if __name__ == '__main__':
    main()

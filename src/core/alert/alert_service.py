import time
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import sys
import platform
import subprocess
import threading

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

# Windows API导入
try:
    import win32api
    import win32con
    import win32gui
    import win32security
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    print("警告: Windows API不可用")

class AlertService:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        self.db_path = Path(self.config.get_paths()['data']) / 'mouse_data.db'
        
        # 告警配置
        self.alert_config = self.config.get_alert_config()
        self.enable_system_actions = self.alert_config.get('enable_system_actions', True)
        self.lock_screen_threshold = self.alert_config.get('lock_screen_threshold', 0.8)
        self.alert_cooldown = self.alert_config.get('alert_cooldown', 60)  # 60秒冷却时间
        
        # 告警状态
        self.last_alert_time = {}
        self.alert_count = {}
        
        self.logger.info("告警服务初始化完成")
        self.logger.info(f"系统操作: {'启用' if self.enable_system_actions else '禁用'}")
        self.logger.info(f"锁屏阈值: {self.lock_screen_threshold}")

    def send_alert(self, user_id, alert_type, message, severity="warning", data=None):
        """发送告警"""
        try:
            current_time = time.time()
            
            # 检查冷却时间
            if user_id in self.last_alert_time:
                time_since_last = current_time - self.last_alert_time[user_id]
                if time_since_last < self.alert_cooldown:
                    self.logger.debug(f"告警冷却中，剩余 {self.alert_cooldown - time_since_last:.1f} 秒")
                    return False
            
            # 记录告警
            self.last_alert_time[user_id] = current_time
            self.alert_count[user_id] = self.alert_count.get(user_id, 0) + 1
            
            # 保存告警到数据库
            self._save_alert_to_db(user_id, alert_type, message, severity, data)
            
            # 记录日志
            self.logger.warning(f"告警 - 用户: {user_id}, 类型: {alert_type}, 消息: {message}")
            print(f"[告警] {message}")
            
            # 执行系统操作
            if self.enable_system_actions:
                self._execute_system_action(alert_type, severity, data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"发送告警失败: {str(e)}")
            return False

    def _save_alert_to_db(self, user_id, alert_type, message, severity, data):
        """保存告警到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建告警表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    data TEXT,
                    timestamp REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 插入告警记录
            cursor.execute('''
                INSERT INTO alerts (user_id, alert_type, message, severity, data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                alert_type,
                message,
                severity,
                json.dumps(data) if data else None,
                time.time()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"告警已保存到数据库")
            
        except Exception as e:
            self.logger.error(f"保存告警到数据库失败: {str(e)}")

    def _execute_system_action(self, alert_type, severity, data):
        """执行系统操作"""
        try:
            if alert_type == "behavior_anomaly":
                # 检查异常分数是否达到锁屏阈值
                anomaly_score = data.get('anomaly_score', 0) if data else 0
                
                if anomaly_score >= self.lock_screen_threshold:
                    self.logger.warning(f"异常分数 {anomaly_score:.3f} 达到锁屏阈值 {self.lock_screen_threshold}")
                    self._lock_screen()
                else:
                    self.logger.info(f"异常分数 {anomaly_score:.3f} 未达到锁屏阈值 {self.lock_screen_threshold}")
                    
        except Exception as e:
            self.logger.error(f"执行系统操作失败: {str(e)}")

    def _lock_screen(self):
        """锁屏操作"""
        try:
            self.logger.warning("执行锁屏操作...")
            print("[系统] 检测到严重异常行为，正在锁屏...")
            
            if platform.system() == "Windows" and WINDOWS_AVAILABLE:
                # Windows锁屏
                self._lock_screen_windows()
            else:
                # 其他系统锁屏
                self._lock_screen_generic()
                
        except Exception as e:
            self.logger.error(f"锁屏操作失败: {str(e)}")

    def _lock_screen_windows(self):
        """Windows系统锁屏"""
        try:
            # 方法1: 使用rundll32
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=True)
            self.logger.info("Windows锁屏成功 (rundll32)")
            
        except subprocess.CalledProcessError:
            try:
                # 方法2: 使用Windows API
                if WINDOWS_AVAILABLE:
                    win32api.LockWorkStation()
                    self.logger.info("Windows锁屏成功 (API)")
                else:
                    self.logger.error("Windows API不可用")
                    
            except Exception as e:
                self.logger.error(f"Windows锁屏失败: {str(e)}")

    def _lock_screen_generic(self):
        """通用锁屏方法"""
        try:
            if platform.system() == "Linux":
                # Linux锁屏
                subprocess.run(['gnome-screensaver-command', '--lock'], check=True)
                self.logger.info("Linux锁屏成功")
            elif platform.system() == "Darwin":
                # macOS锁屏
                subprocess.run(['pmset', 'displaysleepnow'], check=True)
                self.logger.info("macOS锁屏成功")
            else:
                self.logger.warning(f"不支持的操作系统: {platform.system()}")
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"锁屏命令执行失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"通用锁屏失败: {str(e)}")

    def get_alert_statistics(self, user_id, hours=24):
        """获取告警统计信息"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 统计告警数量
            cursor.execute('''
                SELECT COUNT(*) FROM alerts 
                WHERE user_id = ? AND timestamp > ?
            ''', (user_id, cutoff_time))
            
            total_alerts = cursor.fetchone()[0]
            
            # 按类型统计
            cursor.execute('''
                SELECT alert_type, COUNT(*) FROM alerts 
                WHERE user_id = ? AND timestamp > ?
                GROUP BY alert_type
            ''', (user_id, cutoff_time))
            
            alerts_by_type = dict(cursor.fetchall())
            
            conn.close()
            
            stats = {
                'total_alerts': total_alerts,
                'alerts_by_type': alerts_by_type,
                'time_period_hours': hours
            }
            
            self.logger.info(f"用户 {user_id} 告警统计: {total_alerts} 条告警")
            return stats
            
        except Exception as e:
            self.logger.error(f"获取告警统计失败: {str(e)}")
            return {}

    def clear_alert_history(self, user_id=None):
        """清除告警历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('DELETE FROM alerts WHERE user_id = ?', (user_id,))
                self.logger.info(f"清除用户 {user_id} 的告警历史")
            else:
                cursor.execute('DELETE FROM alerts')
                self.logger.info("清除所有告警历史")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"清除告警历史失败: {str(e)}") 
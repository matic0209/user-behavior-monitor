import os
import time
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

# 平台兼容性处理
import platform
if platform.system() == 'Windows':
    try:
        import ctypes
        import win32api
        import win32security
        import win32con
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
else:
    WINDOWS_AVAILABLE = False

class AlertService:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        self.alert_config = self.config.get_alert_config()
        
        # 初始化告警计数器
        self.alert_counters = {}
        
        # 检查平台兼容性
        if not WINDOWS_AVAILABLE and platform.system() != 'Windows':
            self.logger.warning("当前平台不支持Windows API，强制登出功能将被禁用")

    def send_alert(self, user_id: str, alert_type: str, message: str, severity: str = "warning", data: dict = None):
        """发送告警"""
        try:
            self.logger.warning(f"发送告警 - 用户: {user_id}, 类型: {alert_type}, 消息: {message}")
            
            # 更新告警计数器
            if user_id not in self.alert_counters:
                self.alert_counters[user_id] = 0
            self.alert_counters[user_id] += 1
            
            # 检查是否达到告警阈值
            max_alert_count = self.alert_config.get('max_alert_count', 3)
            if self.alert_counters[user_id] >= max_alert_count:
                self.trigger_alert(user_id)
            
            # 记录告警日志
            self.log_alert(user_id, alert_type, message, severity, data)
            
        except Exception as e:
            self.logger.error(f"发送告警失败: {str(e)}")

    def check_anomaly(self, prediction: float, user_id: str) -> bool:
        """检查是否存在异常"""
        try:
            # 获取预测阈值
            threshold = self.alert_config.get('alert_threshold', 0.8)
            
            # 检查是否超过阈值
            is_anomaly = prediction > threshold
            
            if is_anomaly:
                self.logger.warning(f"检测到用户 {user_id} 的异常行为，预测值: {prediction:.4f}")
                
                # 更新告警计数器
                if user_id not in self.alert_counters:
                    self.alert_counters[user_id] = 0
                self.alert_counters[user_id] += 1
                
                # 检查是否达到告警阈值
                max_alert_count = self.alert_config.get('max_alert_count', 3)
                if self.alert_counters[user_id] >= max_alert_count:
                    self.trigger_alert(user_id)
            
            return is_anomaly
            
        except Exception as e:
            self.logger.error(f"异常检查失败: {str(e)}")
            raise

    def trigger_alert(self, user_id: str):
        """触发告警"""
        try:
            self.logger.warning(f"触发用户 {user_id} 的告警")
            
            # 执行强制登出（如果支持）
            if self.alert_config.get('force_logout', False):
                self.force_logout()
            
            # 重置告警计数器
            self.alert_counters[user_id] = 0
            
        except Exception as e:
            self.logger.error(f"告警触发失败: {str(e)}")
            raise

    def force_logout(self):
        """强制登出当前用户"""
        try:
            if not WINDOWS_AVAILABLE:
                self.logger.warning("当前平台不支持强制登出功能")
                return
            
            self.logger.info("执行强制登出")
            
            # 获取当前用户的安全令牌
            h_token = win32security.OpenProcessToken(
                win32api.GetCurrentProcess(),
                win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
            )
            
            # 获取关机权限
            privilege_id = win32security.LookupPrivilegeValue(
                None,
                win32security.SE_SHUTDOWN_NAME
            )
            
            # 启用关机权限
            win32security.AdjustTokenPrivileges(
                h_token,
                0,
                [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)]
            )
            
            # 执行登出
            win32api.ExitWindowsEx(
                win32con.EWX_LOGOFF | win32con.EWX_FORCE,
                0
            )
            
        except Exception as e:
            self.logger.error(f"强制登出失败: {str(e)}")
            # 不抛出异常，避免影响其他功能
            pass

    def log_alert(self, user_id: str, alert_type: str = "behavior_anomaly", message: str = "", severity: str = "warning", data: dict = None):
        """记录告警日志"""
        try:
            # 创建告警日志目录
            alert_log_dir = Path(self.config.get_paths()['logs']) / 'alerts'
            alert_log_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成告警日志文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = alert_log_dir / f'alert_{user_id}_{timestamp}.log'
            
            # 写入告警信息
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"告警时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"用户ID: {user_id}\n")
                f.write(f"告警类型: {alert_type}\n")
                f.write(f"严重程度: {severity}\n")
                f.write(f"消息: {message}\n")
                f.write(f"处理方式: {'强制登出' if self.alert_config.get('force_logout', False) else '仅记录'}\n")
                f.write(f"平台: {platform.system()}\n")
                if data:
                    f.write(f"数据: {str(data)}\n")
            
            self.logger.info(f"告警日志已保存至 {log_file}")
            
        except Exception as e:
            self.logger.error(f"告警日志记录失败: {str(e)}")
            raise

    def get_alert_summary(self) -> dict:
        """获取告警摘要"""
        return {
            'total_alerts': sum(self.alert_counters.values()),
            'user_alerts': self.alert_counters.copy(),
            'platform_support': WINDOWS_AVAILABLE
        } 
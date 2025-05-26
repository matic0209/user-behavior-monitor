import win32gui
import win32con
import win32api
import win32security
import ctypes
from ctypes import wintypes
import os

class AlertManager:
    def __init__(self):
        self.alert_count = 0
        self.max_alerts = 3  # 最大告警次数
        
    def trigger_alert(self, message, force_logout=False):
        """触发告警"""
        self.alert_count += 1
        
        # 显示告警窗口
        self._show_alert_window(message)
        
        # 如果达到最大告警次数或需要强制登出
        if self.alert_count >= self.max_alerts or force_logout:
            self._force_logout()
            
    def _show_alert_window(self, message):
        """显示告警窗口"""
        win32gui.MessageBox(
            0,
            message,
            "安全警告",
            win32con.MB_ICONWARNING | win32con.MB_OK
        )
        
    def _force_logout(self):
        """强制用户登出"""
        try:
            # 获取当前用户的令牌
            token = win32security.OpenProcessToken(
                win32api.GetCurrentProcess(),
                win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
            )
            
            # 获取关机权限
            shutdown_priv = win32security.LookupPrivilegeValue(
                None,
                win32security.SE_SHUTDOWN_NAME
            )
            
            # 启用关机权限
            win32security.AdjustTokenPrivileges(
                token,
                0,
                [(shutdown_priv, win32security.SE_PRIVILEGE_ENABLED)]
            )
            
            # 执行登出操作
            win32api.ExitWindowsEx(
                win32con.EWX_LOGOFF | win32con.EWX_FORCE,
                0
            )
            
        except Exception as e:
            print(f"登出失败: {str(e)}")
            
    def reset_alert_count(self):
        """重置告警计数"""
        self.alert_count = 0 
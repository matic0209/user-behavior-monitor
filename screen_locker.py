import ctypes
import win32api
import win32con
import win32security
import win32ts
import win32gui
import win32process
import win32event
import winerror
import sys
import os
import logging

class ScreenLocker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def lock_screen(self):
        """锁定屏幕"""
        try:
            # 方法1: 使用Windows API
            ctypes.windll.user32.LockWorkStation()
            self.logger.info("Screen locked using LockWorkStation")
            return True
        except Exception as e:
            self.logger.error(f"Failed to lock screen using LockWorkStation: {str(e)}")
            try:
                # 方法2: 使用Win32 API
                win32api.keybd_event(win32con.VK_LWIN, 0, 0, 0)
                win32api.keybd_event(ord('L'), 0, 0, 0)
                win32api.keybd_event(ord('L'), 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(win32con.VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0)
                self.logger.info("Screen locked using Win32 API")
                return True
            except Exception as e:
                self.logger.error(f"Failed to lock screen using Win32 API: {str(e)}")
                return False

    def force_logout(self):
        """强制注销当前用户"""
        try:
            # 获取当前会话ID
            session_id = win32ts.WTSGetActiveConsoleSessionId()
            
            # 获取当前用户令牌
            token = win32security.OpenProcessToken(
                win32api.GetCurrentProcess(),
                win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
            )
            
            # 设置关机权限
            privilege_id = win32security.LookupPrivilegeValue(
                None, win32security.SE_SHUTDOWN_NAME
            )
            win32security.AdjustTokenPrivileges(
                token, 0, [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)]
            )
            
            # 注销当前用户
            win32ts.WTSLogoffSession(None, session_id, True)
            self.logger.info("User logged out successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to logout user: {str(e)}")
            return False

    def is_screen_locked(self):
        """检查屏幕是否已锁定"""
        try:
            # 获取当前会话状态
            session_id = win32ts.WTSGetActiveConsoleSessionId()
            session_info = win32ts.WTSQuerySessionInformation(
                None, session_id, win32ts.WTSConnectState
            )
            return session_info == win32ts.WTSDisconnected
        except Exception as e:
            self.logger.error(f"Failed to check screen lock status: {str(e)}")
            return False 
#!/usr/bin/env python3
"""
Windows服务包装器
将用户行为监控系统作为Windows服务运行
"""

import sys
import os
import time
import logging
from pathlib import Path
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class UserBehaviorMonitorService(win32serviceutil.ServiceFramework):
    """用户行为监控Windows服务"""
    
    _svc_name_ = "UserBehaviorMonitor"
    _svc_display_name_ = "用户行为异常检测系统"
    _svc_description_ = "基于机器学习的用户行为异常检测和自动锁屏保护系统"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.monitor = None
        
        # 设置日志
        self._setup_logging()
        
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 服务日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "windows_service.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("UserBehaviorMonitorService")
        
    def SvcStop(self):
        """停止服务"""
        self.logger.info("收到停止服务请求")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        
    def SvcDoRun(self):
        """运行服务"""
        try:
            self.logger.info("用户行为监控服务启动")
            
            # 导入监控系统
            from user_behavior_monitor import WindowsBehaviorMonitor
            
            # 创建监控实例
            self.monitor = WindowsBehaviorMonitor()
            
            # 启动监控系统
            if self.monitor.start():
                self.logger.info("监控系统启动成功")
                
                # 服务主循环
                while True:
                    # 检查停止事件
                    if win32event.WaitForSingleObject(self.stop_event, 1000) == win32event.WAIT_OBJECT_0:
                        break
                    
                    # 检查监控系统状态
                    if not self.monitor.is_running:
                        self.logger.warning("监控系统已停止，重新启动")
                        self.monitor.start()
                        
            else:
                self.logger.error("监控系统启动失败")
                
        except Exception as e:
            self.logger.error(f"服务运行异常: {str(e)}")
            import traceback
            self.logger.error(f"异常详情: {traceback.format_exc()}")
            
        finally:
            if self.monitor:
                self.monitor.stop()
            self.logger.info("用户行为监控服务已停止")

def main():
    """主函数"""
    if len(sys.argv) == 1:
        # 直接运行服务
        try:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(UserBehaviorMonitorService)
            servicemanager.StartServiceCtrlDispatcher()
        except win32service.error as e:
            servicemanager.LogErrorMsg(str(e))
    else:
        # 处理服务命令
        win32serviceutil.HandleCommandLine(UserBehaviorMonitorService)

if __name__ == '__main__':
    main() 
#!/usr/bin/env python3
"""
Windows服务管理器
用于以后端服务形式启动和管理exe程序
"""

import os
import sys
import time
import subprocess
import threading
import signal
import psutil
import json
import logging
from pathlib import Path
from datetime import datetime

# Windows服务相关
try:
    import win32service
    import win32serviceutil
    import win32event
    import servicemanager
    import win32api
    import win32con
    WINDOWS_SERVICE_AVAILABLE = True
except ImportError:
    WINDOWS_SERVICE_AVAILABLE = False
    print("警告: Windows服务API不可用")

class UserBehaviorMonitorService:
    """用户行为监控Windows服务"""
    
    _svc_name_ = "UserBehaviorMonitor"
    _svc_display_name_ = "用户行为监控系统"
    _svc_description_ = "基于机器学习的用户行为异常检测系统"
    
    def __init__(self):
        self.is_running = False
        self.process = None
        self.logger = self._setup_logger()
        self.config = self._load_config()
        
    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger('UserBehaviorMonitorService')
        logger.setLevel(logging.INFO)
        
        # 创建日志目录
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # 文件处理器
        handler = logging.FileHandler(log_dir / 'service.log', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _load_config(self):
        """加载配置"""
        config_file = Path('service_config.json')
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"加载配置文件失败: {e}")
        
        # 默认配置
        return {
            "exe_path": "UserBehaviorMonitorOptimized.exe",
            "working_dir": ".",
            "restart_on_crash": True,
            "max_restart_attempts": 3,
            "restart_delay": 30,
            "auto_start": True,
            "log_level": "INFO"
        }
    
    def _start_monitor_process(self):
        """启动监控进程"""
        try:
            exe_path = self.config.get('exe_path', 'UserBehaviorMonitorOptimized.exe')
            working_dir = self.config.get('working_dir', '.')
            
            # 检查exe文件是否存在
            if not Path(exe_path).exists():
                self.logger.error(f"找不到可执行文件: {exe_path}")
                return False
            
            # 启动进程
            self.process = subprocess.Popen(
                [exe_path],
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.logger.info(f"监控进程已启动，PID: {self.process.pid}")
            return True
            
        except Exception as e:
            self.logger.error(f"启动监控进程失败: {e}")
            return False
    
    def _stop_monitor_process(self):
        """停止监控进程"""
        try:
            if self.process and self.process.poll() is None:
                self.logger.info("正在停止监控进程...")
                
                # 尝试优雅停止
                self.process.terminate()
                
                # 等待最多10秒
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.logger.warning("进程未响应，强制终止")
                    self.process.kill()
                    self.process.wait()
                
                self.logger.info("监控进程已停止")
            
        except Exception as e:
            self.logger.error(f"停止监控进程失败: {e}")
    
    def _monitor_process(self):
        """监控进程状态"""
        while self.is_running:
            try:
                if self.process and self.process.poll() is not None:
                    # 进程已退出
                    exit_code = self.process.returncode
                    self.logger.warning(f"监控进程已退出，退出码: {exit_code}")
                    
                    if self.config.get('restart_on_crash', True):
                        self._restart_process()
                    else:
                        self.logger.info("自动重启已禁用，服务将停止")
                        self.is_running = False
                        break
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                self.logger.error(f"监控进程状态时出错: {e}")
                time.sleep(10)
    
    def _restart_process(self):
        """重启进程"""
        restart_count = getattr(self, 'restart_count', 0)
        max_attempts = self.config.get('max_restart_attempts', 3)
        
        if restart_count >= max_attempts:
            self.logger.error(f"重启次数已达上限 ({max_attempts})，停止服务")
            self.is_running = False
            return
        
        restart_count += 1
        setattr(self, 'restart_count', restart_count)
        
        restart_delay = self.config.get('restart_delay', 30)
        self.logger.info(f"准备重启进程 (第{restart_count}次)，等待{restart_delay}秒...")
        
        time.sleep(restart_delay)
        
        if self._start_monitor_process():
            self.logger.info("进程重启成功")
        else:
            self.logger.error("进程重启失败")
    
    def SvcStop(self):
        """停止服务"""
        self.logger.info("收到停止服务信号")
        self.is_running = False
        self._stop_monitor_process()
    
    def SvcDoRun(self):
        """运行服务"""
        self.logger.info("用户行为监控服务启动")
        self.is_running = True
        self.restart_count = 0
        
        # 启动监控进程
        if not self._start_monitor_process():
            self.logger.error("无法启动监控进程，服务将退出")
            return
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=self._monitor_process, daemon=True)
        monitor_thread.start()
        
        # 保持服务运行
        while self.is_running:
            time.sleep(1)
        
        self.logger.info("用户行为监控服务停止")

class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger('ServiceManager')
        self.logger.setLevel(logging.INFO)
        
        # 创建日志目录
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # 文件处理器
        handler = logging.FileHandler(log_dir / 'service_manager.log', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def install_service(self):
        """安装服务"""
        if not WINDOWS_SERVICE_AVAILABLE:
            print("错误: Windows服务API不可用")
            return False
        
        try:
            win32serviceutil.InstallService(
                UserBehaviorMonitorService._svc_name_,
                UserBehaviorMonitorService._svc_display_name_,
                UserBehaviorMonitorService._svc_description_
            )
            print("✓ 服务安装成功")
            return True
        except Exception as e:
            print(f"✗ 服务安装失败: {e}")
            return False
    
    def uninstall_service(self):
        """卸载服务"""
        if not WINDOWS_SERVICE_AVAILABLE:
            print("错误: Windows服务API不可用")
            return False
        
        try:
            win32serviceutil.RemoveService(UserBehaviorMonitorService._svc_name_)
            print("✓ 服务卸载成功")
            return True
        except Exception as e:
            print(f"✗ 服务卸载失败: {e}")
            return False
    
    def start_service(self):
        """启动服务"""
        if not WINDOWS_SERVICE_AVAILABLE:
            print("错误: Windows服务API不可用")
            return False
        
        try:
            win32serviceutil.StartService(UserBehaviorMonitorService._svc_name_)
            print("✓ 服务启动成功")
            return True
        except Exception as e:
            print(f"✗ 服务启动失败: {e}")
            return False
    
    def stop_service(self):
        """停止服务"""
        if not WINDOWS_SERVICE_AVAILABLE:
            print("错误: Windows服务API不可用")
            return False
        
        try:
            win32serviceutil.StopService(UserBehaviorMonitorService._svc_name_)
            print("✓ 服务停止成功")
            return True
        except Exception as e:
            print(f"✗ 服务停止失败: {e}")
            return False
    
    def create_config(self):
        """创建配置文件"""
        config = {
            "exe_path": "UserBehaviorMonitorOptimized.exe",
            "working_dir": ".",
            "restart_on_crash": True,
            "max_restart_attempts": 3,
            "restart_delay": 30,
            "auto_start": True,
            "log_level": "INFO"
        }
        
        config_file = Path('service_config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✓ 配置文件创建成功: service_config.json")
    
    def run_as_service(self):
        """以服务形式运行"""
        if not WINDOWS_SERVICE_AVAILABLE:
            print("错误: Windows服务API不可用")
            return False
        
        try:
            win32serviceutil.HandleCommandLine(UserBehaviorMonitorService)
        except Exception as e:
            print(f"✗ 服务运行失败: {e}")
            return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用户行为监控服务管理器")
        print("=" * 40)
        print("用法:")
        print("  python service_manager.py install    - 安装服务")
        print("  python service_manager.py uninstall  - 卸载服务")
        print("  python service_manager.py start      - 启动服务")
        print("  python service_manager.py stop       - 停止服务")
        print("  python service_manager.py restart    - 重启服务")
        print("  python service_manager.py status     - 查看服务状态")
        print("  python service_manager.py run        - 直接运行服务")
        print("  python service_manager.py config     - 创建配置文件")
        return
    
    manager = ServiceManager()
    command = sys.argv[1].lower()
    
    if command == 'install':
        manager.install_service()
    elif command == 'uninstall':
        manager.uninstall_service()
    elif command == 'start':
        manager.start_service()
    elif command == 'stop':
        manager.stop_service()
    elif command == 'restart':
        manager.stop_service()
        time.sleep(2)
        manager.start_service()
    elif command == 'status':
        try:
            status = win32serviceutil.QueryServiceStatus(UserBehaviorMonitorService._svc_name_)
            print(f"服务状态: {status}")
        except Exception as e:
            print(f"查询服务状态失败: {e}")
    elif command == 'run':
        manager.run_as_service()
    elif command == 'config':
        manager.create_config()
    else:
        print(f"未知命令: {command}")

if __name__ == '__main__':
    main() 
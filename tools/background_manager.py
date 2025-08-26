#!/usr/bin/env python3
"""
后台进程管理器
用于以后台形式启动和管理exe程序
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

class BackgroundManager:
    """后台进程管理器"""
    
    def __init__(self):
        self.is_running = False
        self.process = None
        self.logger = self._setup_logger()
        self.config = self._load_config()
        self.restart_count = 0
        
    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger('BackgroundManager')
        logger.setLevel(logging.INFO)
        
        # 创建日志目录
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # 文件处理器
        handler = logging.FileHandler(log_dir / 'background_manager.log', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _load_config(self):
        """加载配置"""
        config_file = Path('background_config.json')
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
            "max_restart_attempts": 5,
            "restart_delay": 10,
            "auto_start": True,
            "log_level": "INFO",
            "hide_console": True
        }
    
    def _start_monitor_process(self):
        """启动监控进程"""
        try:
            exe_path = self.config.get('exe_path', 'UserBehaviorMonitorOptimized.exe')
            working_dir = self.config.get('working_dir', '.')
            hide_console = self.config.get('hide_console', True)
            
            # 检查exe文件是否存在
            if not Path(exe_path).exists():
                self.logger.error(f"找不到可执行文件: {exe_path}")
                return False
            
            # 设置启动参数
            startupinfo = None
            creationflags = 0
            
            if hide_console and sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW
            
            # 启动进程
            self.process = subprocess.Popen(
                [exe_path],
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=creationflags
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
                        self.logger.info("自动重启已禁用，管理器将停止")
                        self.is_running = False
                        break
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                self.logger.error(f"监控进程状态时出错: {e}")
                time.sleep(10)
    
    def _restart_process(self):
        """重启进程"""
        max_attempts = self.config.get('max_restart_attempts', 5)
        
        if self.restart_count >= max_attempts:
            self.logger.error(f"重启次数已达上限 ({max_attempts})，停止管理器")
            self.is_running = False
            return
        
        self.restart_count += 1
        restart_delay = self.config.get('restart_delay', 10)
        
        self.logger.info(f"准备重启进程 (第{self.restart_count}次)，等待{restart_delay}秒...")
        
        time.sleep(restart_delay)
        
        if self._start_monitor_process():
            self.logger.info("进程重启成功")
        else:
            self.logger.error("进程重启失败")
    
    def start(self):
        """启动管理器"""
        self.logger.info("后台进程管理器启动")
        self.is_running = True
        self.restart_count = 0
        
        # 启动监控进程
        if not self._start_monitor_process():
            self.logger.error("无法启动监控进程，管理器将退出")
            return False
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=self._monitor_process, daemon=True)
        monitor_thread.start()
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 保持管理器运行
        while self.is_running:
            time.sleep(1)
        
        self.logger.info("后台进程管理器停止")
        return True
    
    def stop(self):
        """停止管理器"""
        self.logger.info("收到停止信号")
        self.is_running = False
        self._stop_monitor_process()
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，正在停止...")
        self.stop()
    
    def create_config(self):
        """创建配置文件"""
        config = {
            "exe_path": "UserBehaviorMonitorOptimized.exe",
            "working_dir": ".",
            "restart_on_crash": True,
            "max_restart_attempts": 5,
            "restart_delay": 10,
            "auto_start": True,
            "log_level": "INFO",
            "hide_console": True
        }
        
        config_file = Path('background_config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✓ 配置文件创建成功: background_config.json")
    
    def get_status(self):
        """获取状态"""
        if self.process and self.process.poll() is None:
            return {
                "status": "running",
                "pid": self.process.pid,
                "restart_count": self.restart_count
            }
        else:
            return {
                "status": "stopped",
                "pid": None,
                "restart_count": self.restart_count
            }

def create_startup_script():
    """创建启动脚本"""
    script_content = """@echo off
chcp 65001 >nul
echo 用户行为监控后台管理器
echo ========================

cd /d "%~dp0"

echo 正在启动后台管理器...
python background_manager.py start

if %errorLevel% neq 0 (
    echo 启动失败，按任意键退出...
    pause
) else (
    echo 后台管理器已启动
    echo 进程将在后台运行
    echo 查看日志: logs/background_manager.log
)
"""
    
    script_file = Path('start_background.bat')
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✓ 启动脚本创建成功: start_background.bat")

def create_stop_script():
    """创建停止脚本"""
    script_content = """@echo off
chcp 65001 >nul
echo 停止用户行为监控后台管理器
echo ===========================

cd /d "%~dp0"

echo 正在查找后台管理器进程...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr background_manager') do (
    echo 找到进程 PID: %%i
    taskkill /pid %%i /f
    echo 进程已终止
)

echo 操作完成
pause
"""
    
    script_file = Path('stop_background.bat')
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✓ 停止脚本创建成功: stop_background.bat")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用户行为监控后台管理器")
        print("=" * 40)
        print("用法:")
        print("  python background_manager.py start     - 启动后台管理器")
        print("  python background_manager.py stop      - 停止后台管理器")
        print("  python background_manager.py status    - 查看状态")
        print("  python background_manager.py config    - 创建配置文件")
        print("  python background_manager.py scripts   - 创建启动/停止脚本")
        return
    
    manager = BackgroundManager()
    command = sys.argv[1].lower()
    
    if command == 'start':
        manager.start()
    elif command == 'stop':
        manager.stop()
    elif command == 'status':
        status = manager.get_status()
        print(f"状态: {status['status']}")
        print(f"PID: {status['pid']}")
        print(f"重启次数: {status['restart_count']}")
    elif command == 'config':
        manager.create_config()
    elif command == 'scripts':
        create_startup_script()
        create_stop_script()
    else:
        print(f"未知命令: {command}")

if __name__ == '__main__':
    main() 
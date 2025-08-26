#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UOS20系统后台进程管理工具
支持使用nohup、screen等方式管理后台进程
"""

import os
import sys
import subprocess
import json
import time
import logging
import signal
import psutil
from pathlib import Path

class UOS20BackgroundManager:
    """UOS20系统后台进程管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.python_path = sys.executable
        self.main_script = self.project_root / "user_behavior_monitor_uos20.py"
        self.pid_file = self.project_root / "uos20_monitor.pid"
        self.log_file = self.project_root / "logs" / "uos20_background.log"
        
        # 确保日志目录存在
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_pid(self):
        """获取进程PID"""
        if self.pid_file.exists():
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                return pid
            except (ValueError, IOError):
                return None
        return None
    
    def save_pid(self, pid):
        """保存进程PID"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(pid))
            return True
        except Exception as e:
            self.logger.error(f"保存PID失败: {e}")
            return False
    
    def is_process_running(self, pid):
        """检查进程是否运行"""
        if pid is None:
            return False
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return False
    
    def start_background(self):
        """启动后台进程"""
        if not self.main_script.exists():
            self.logger.error(f"主脚本不存在: {self.main_script}")
            return False
        
        # 检查是否已经在运行
        pid = self.get_pid()
        if pid and self.is_process_running(pid):
            self.logger.info(f"进程已在运行，PID: {pid}")
            return True
        
        try:
            # 使用nohup启动后台进程
            cmd = [
                "nohup", self.python_path, str(self.main_script),
                ">", str(self.log_file), "2>&1", "&"
            ]
            
            # 启动进程
            process = subprocess.Popen(
                [self.python_path, str(self.main_script)],
                stdout=open(self.log_file, 'a'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid  # 创建新进程组
            )
            
            # 保存PID
            if self.save_pid(process.pid):
                self.logger.info(f"后台进程已启动，PID: {process.pid}")
                self.logger.info(f"日志文件: {self.log_file}")
                return True
            else:
                process.terminate()
                return False
                
        except Exception as e:
            self.logger.error(f"启动后台进程失败: {e}")
            return False
    
    def stop_background(self):
        """停止后台进程"""
        pid = self.get_pid()
        if not pid:
            self.logger.info("没有找到运行中的进程")
            return True
        
        if not self.is_process_running(pid):
            self.logger.info("进程未运行")
            self.pid_file.unlink(missing_ok=True)
            return True
        
        try:
            # 发送TERM信号
            os.kill(pid, signal.SIGTERM)
            self.logger.info(f"已发送停止信号到进程 {pid}")
            
            # 等待进程结束
            for i in range(10):
                time.sleep(1)
                if not self.is_process_running(pid):
                    break
            else:
                # 如果进程还在运行，强制终止
                os.kill(pid, signal.SIGKILL)
                self.logger.info(f"强制终止进程 {pid}")
            
            # 删除PID文件
            self.pid_file.unlink(missing_ok=True)
            self.logger.info("后台进程已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止后台进程失败: {e}")
            return False
    
    def restart_background(self):
        """重启后台进程"""
        self.logger.info("重启后台进程...")
        if self.stop_background():
            time.sleep(2)
            return self.start_background()
        return False
    
    def status_background(self):
        """查询后台进程状态"""
        pid = self.get_pid()
        
        if not pid:
            print("状态: 未运行")
            return False
        
        if self.is_process_running(pid):
            try:
                process = psutil.Process(pid)
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                
                print(f"状态: 运行中")
                print(f"PID: {pid}")
                print(f"CPU使用率: {cpu_percent:.1f}%")
                print(f"内存使用: {memory_info.rss / 1024 / 1024:.1f} MB")
                print(f"启动时间: {time.ctime(process.create_time())}")
                print(f"日志文件: {self.log_file}")
                return True
            except Exception as e:
                self.logger.error(f"获取进程信息失败: {e}")
                return False
        else:
            print("状态: 进程已停止")
            self.pid_file.unlink(missing_ok=True)
            return False
    
    def show_logs(self, lines=50):
        """显示日志"""
        if not self.log_file.exists():
            self.logger.error("日志文件不存在")
            return False
        
        try:
            # 显示最后几行日志
            result = subprocess.run(
                ["tail", "-n", str(lines), str(self.log_file)],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            return True
        except Exception as e:
            self.logger.error(f"查看日志失败: {e}")
            return False
    
    def follow_logs(self):
        """实时跟踪日志"""
        if not self.log_file.exists():
            self.logger.error("日志文件不存在")
            return False
        
        try:
            subprocess.run(["tail", "-f", str(self.log_file)])
        except KeyboardInterrupt:
            self.logger.info("日志跟踪已停止")
        except Exception as e:
            self.logger.error(f"跟踪日志失败: {e}")
    
    def create_screen_session(self):
        """创建screen会话"""
        session_name = "user-behavior-monitor"
        
        try:
            # 检查screen是否安装
            subprocess.run(["which", "screen"], check=True)
            
            # 创建screen会话
            cmd = [
                "screen", "-dmS", session_name,
                self.python_path, str(self.main_script)
            ]
            
            subprocess.run(cmd, check=True)
            self.logger.info(f"Screen会话已创建: {session_name}")
            self.logger.info(f"使用 'screen -r {session_name}' 连接到会话")
            self.logger.info(f"使用 'screen -ls' 查看所有会话")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"创建screen会话失败: {e}")
            return False
    
    def attach_screen_session(self):
        """连接到screen会话"""
        session_name = "user-behavior-monitor"
        
        try:
            subprocess.run(["screen", "-r", session_name])
        except KeyboardInterrupt:
            self.logger.info("已退出screen会话")
        except Exception as e:
            self.logger.error(f"连接screen会话失败: {e}")
    
    def list_screen_sessions(self):
        """列出screen会话"""
        try:
            subprocess.run(["screen", "-ls"])
        except Exception as e:
            self.logger.error(f"列出screen会话失败: {e}")
    
    def create_config(self):
        """创建配置文件"""
        config = {
            "python_path": str(self.python_path),
            "main_script": str(self.main_script),
            "project_root": str(self.project_root),
            "pid_file": str(self.pid_file),
            "log_file": str(self.log_file),
            "auto_restart": True,
            "restart_interval": 10
        }
        
        config_file = self.project_root / "uos20_background_config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"配置文件已创建: {config_file}")
            return True
        except Exception as e:
            self.logger.error(f"创建配置文件失败: {e}")
            return False
    
    def create_scripts(self):
        """创建管理脚本"""
        # 创建启动脚本
        start_script = self.project_root / "start_uos20_monitor.sh"
        start_content = f"""#!/bin/bash
cd {self.project_root}
python3 uos20_background_manager.py start
"""
        
        # 创建停止脚本
        stop_script = self.project_root / "stop_uos20_monitor.sh"
        stop_content = f"""#!/bin/bash
cd {self.project_root}
python3 uos20_background_manager.py stop
"""
        
        # 创建状态脚本
        status_script = self.project_root / "status_uos20_monitor.sh"
        status_content = f"""#!/bin/bash
cd {self.project_root}
python3 uos20_background_manager.py status
"""
        
        try:
            # 写入启动脚本
            with open(start_script, 'w') as f:
                f.write(start_content)
            os.chmod(start_script, 0o755)
            
            # 写入停止脚本
            with open(stop_script, 'w') as f:
                f.write(stop_content)
            os.chmod(stop_script, 0o755)
            
            # 写入状态脚本
            with open(status_script, 'w') as f:
                f.write(status_content)
            os.chmod(status_script, 0o755)
            
            self.logger.info("管理脚本已创建:")
            self.logger.info(f"  启动: {start_script}")
            self.logger.info(f"  停止: {stop_script}")
            self.logger.info(f"  状态: {status_script}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建管理脚本失败: {e}")
            return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("UOS20后台进程管理工具")
        print("用法: python3 uos20_background_manager.py <command>")
        print("命令:")
        print("  start       - 启动后台进程")
        print("  stop        - 停止后台进程")
        print("  restart     - 重启后台进程")
        print("  status      - 查询进程状态")
        print("  logs        - 查看日志")
        print("  follow      - 实时跟踪日志")
        print("  screen      - 创建screen会话")
        print("  attach      - 连接到screen会话")
        print("  list        - 列出screen会话")
        print("  config      - 创建配置文件")
        print("  scripts     - 创建管理脚本")
        return
    
    manager = UOS20BackgroundManager()
    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start_background()
    elif command == "stop":
        manager.stop_background()
    elif command == "restart":
        manager.restart_background()
    elif command == "status":
        manager.status_background()
    elif command == "logs":
        manager.show_logs()
    elif command == "follow":
        manager.follow_logs()
    elif command == "screen":
        manager.create_screen_session()
    elif command == "attach":
        manager.attach_screen_session()
    elif command == "list":
        manager.list_screen_sessions()
    elif command == "config":
        manager.create_config()
    elif command == "scripts":
        manager.create_scripts()
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main() 
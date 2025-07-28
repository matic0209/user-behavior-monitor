#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UOS20系统服务管理工具
支持systemd服务安装、启动、停止、状态查询等功能
"""

import os
import sys
import subprocess
import json
import time
import logging
from pathlib import Path

class UOS20ServiceManager:
    """UOS20系统服务管理器"""
    
    def __init__(self):
        self.service_name = "user-behavior-monitor"
        self.service_file = f"/etc/systemd/system/{self.service_name}.service"
        self.project_root = Path(__file__).parent.absolute()
        self.python_path = sys.executable
        self.main_script = self.project_root / "user_behavior_monitor_uos20.py"
        
        # 设置日志
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "uos20_service.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_root_permission(self):
        """检查root权限"""
        if os.geteuid() != 0:
            self.logger.error("需要root权限运行此命令")
            self.logger.error("请使用: sudo python3 uos20_service_manager.py <command>")
            return False
        return True
    
    def create_service_file(self):
        """创建systemd服务文件"""
        service_content = f"""[Unit]
Description=User Behavior Monitor Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={self.project_root}
ExecStart={self.python_path} {self.main_script}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        try:
            with open(self.service_file, 'w', encoding='utf-8') as f:
                f.write(service_content)
            self.logger.info(f"服务文件已创建: {self.service_file}")
            return True
        except Exception as e:
            self.logger.error(f"创建服务文件失败: {e}")
            return False
    
    def install_service(self):
        """安装服务"""
        if not self.check_root_permission():
            return False
            
        if not self.main_script.exists():
            self.logger.error(f"主脚本不存在: {self.main_script}")
            return False
        
        # 创建服务文件
        if not self.create_service_file():
            return False
        
        try:
            # 重新加载systemd配置
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            self.logger.info("systemd配置已重新加载")
            
            # 启用服务
            subprocess.run(["systemctl", "enable", self.service_name], check=True)
            self.logger.info(f"服务已启用: {self.service_name}")
            
            self.logger.info("服务安装完成！")
            self.logger.info(f"使用以下命令管理服务:")
            self.logger.info(f"  启动: sudo systemctl start {self.service_name}")
            self.logger.info(f"  停止: sudo systemctl stop {self.service_name}")
            self.logger.info(f"  状态: sudo systemctl status {self.service_name}")
            self.logger.info(f"  重启: sudo systemctl restart {self.service_name}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"服务安装失败: {e}")
            return False
    
    def uninstall_service(self):
        """卸载服务"""
        if not self.check_root_permission():
            return False
        
        try:
            # 停止服务
            subprocess.run(["systemctl", "stop", self.service_name], check=False)
            
            # 禁用服务
            subprocess.run(["systemctl", "disable", self.service_name], check=False)
            
            # 删除服务文件
            if os.path.exists(self.service_file):
                os.remove(self.service_file)
                self.logger.info(f"服务文件已删除: {self.service_file}")
            
            # 重新加载systemd配置
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            
            self.logger.info("服务卸载完成！")
            return True
            
        except Exception as e:
            self.logger.error(f"服务卸载失败: {e}")
            return False
    
    def start_service(self):
        """启动服务"""
        if not self.check_root_permission():
            return False
        
        try:
            subprocess.run(["systemctl", "start", self.service_name], check=True)
            self.logger.info(f"服务已启动: {self.service_name}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"启动服务失败: {e}")
            return False
    
    def stop_service(self):
        """停止服务"""
        if not self.check_root_permission():
            return False
        
        try:
            subprocess.run(["systemctl", "stop", self.service_name], check=True)
            self.logger.info(f"服务已停止: {self.service_name}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"停止服务失败: {e}")
            return False
    
    def restart_service(self):
        """重启服务"""
        if not self.check_root_permission():
            return False
        
        try:
            subprocess.run(["systemctl", "restart", self.service_name], check=True)
            self.logger.info(f"服务已重启: {self.service_name}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"重启服务失败: {e}")
            return False
    
    def status_service(self):
        """查询服务状态"""
        try:
            result = subprocess.run(
                ["systemctl", "status", self.service_name], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("服务状态:")
                print(result.stdout)
            else:
                self.logger.error("服务未运行或不存在")
                print(result.stderr)
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"查询服务状态失败: {e}")
            return False
    
    def show_logs(self):
        """显示服务日志"""
        try:
            subprocess.run([
                "journalctl", "-u", self.service_name, "-f", "--no-pager"
            ])
        except KeyboardInterrupt:
            self.logger.info("日志查看已停止")
        except Exception as e:
            self.logger.error(f"查看日志失败: {e}")
    
    def create_config(self):
        """创建配置文件"""
        config = {
            "service_name": self.service_name,
            "python_path": str(self.python_path),
            "main_script": str(self.main_script),
            "project_root": str(self.project_root),
            "log_dir": str(self.project_root / "logs"),
            "auto_restart": True,
            "restart_interval": 10
        }
        
        config_file = self.project_root / "uos20_service_config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"配置文件已创建: {config_file}")
            return True
        except Exception as e:
            self.logger.error(f"创建配置文件失败: {e}")
            return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("UOS20服务管理工具")
        print("用法: python3 uos20_service_manager.py <command>")
        print("命令:")
        print("  install     - 安装服务")
        print("  uninstall   - 卸载服务")
        print("  start       - 启动服务")
        print("  stop        - 停止服务")
        print("  restart     - 重启服务")
        print("  status      - 查询服务状态")
        print("  logs        - 查看服务日志")
        print("  config      - 创建配置文件")
        return
    
    manager = UOS20ServiceManager()
    command = sys.argv[1].lower()
    
    if command == "install":
        manager.install_service()
    elif command == "uninstall":
        manager.uninstall_service()
    elif command == "start":
        manager.start_service()
    elif command == "stop":
        manager.stop_service()
    elif command == "restart":
        manager.restart_service()
    elif command == "status":
        manager.status_service()
    elif command == "logs":
        manager.show_logs()
    elif command == "config":
        manager.create_config()
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main() 
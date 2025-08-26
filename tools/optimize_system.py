#!/usr/bin/env python3
"""
用户行为异常检测系统 - 优化脚本
整合所有产品化改进，提升系统成熟度
"""

import sys
import os
import time
import json
from pathlib import Path
import subprocess

def check_system_requirements():
    """检查系统要求"""
    print("=== 检查系统要求 ===")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print(f"✗ Python版本过低: {python_version.major}.{python_version.minor}")
        print("需要Python 3.7或更高版本")
        return False
    else:
        print(f"✓ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查操作系统
    import platform
    system = platform.system()
    if system == "Windows":
        print("✓ 操作系统: Windows")
    elif system == "Linux":
        print("✓ 操作系统: Linux")
    elif system == "Darwin":
        print("✓ 操作系统: macOS")
    else:
        print(f"⚠️  操作系统: {system} (可能不完全支持)")
    
    # 检查内存
    import psutil
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024**3)
    if memory_gb < 2:
        print(f"⚠️  内存不足: {memory_gb:.1f}GB (建议2GB+)")
    else:
        print(f"✓ 内存: {memory_gb:.1f}GB")
    
    # 检查磁盘空间
    disk = psutil.disk_usage('.')
    disk_gb = disk.free / (1024**3)
    if disk_gb < 1:
        print(f"⚠️  磁盘空间不足: {disk_gb:.1f}GB (建议1GB+)")
    else:
        print(f"✓ 磁盘空间: {disk_gb:.1f}GB")
    
    return True

def optimize_configuration():
    """优化配置文件"""
    print("\n=== 优化配置文件 ===")
    
    try:
        config_path = Path("src/utils/config/config.yaml")
        if not config_path.exists():
            print("✗ 配置文件不存在")
            return False
        
        # 读取当前配置
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 优化配置
        optimizations = {
            'prediction': {
                'interval': 5,  # 降低预测间隔
                'anomaly_threshold': 0.3,  # 降低异常阈值
                'batch_size': 50  # 优化批处理大小
            },
            'alert': {
                'lock_screen_threshold': 0.8,  # 锁屏阈值
                'warning_duration': 10,  # 警告持续时间
                'alert_cooldown': 60,  # 告警冷却时间
                'show_warning_dialog': True,  # 显示警告对话框
                'enable_system_actions': True  # 启用系统操作
            },
            'logging': {
                'level': 'INFO',  # 生产环境使用INFO级别
                'console_level': 'INFO',
                'file_level': 'DEBUG'
            },
            'system': {
                'debug_mode': False,  # 生产环境关闭调试模式
                'max_workers': 4,
                'memory_limit': '2GB'
            }
        }
        
        # 应用优化
        for section, settings in optimizations.items():
            if section not in config:
                config[section] = {}
            config[section].update(settings)
        
        # 保存优化后的配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print("✓ 配置文件优化完成")
        return True
        
    except Exception as e:
        print(f"✗ 配置文件优化失败: {e}")
        return False

def create_launcher_scripts():
    """创建启动脚本"""
    print("\n=== 创建启动脚本 ===")
    
    # Windows批处理文件
    windows_bat = """@echo off
echo 用户行为异常检测系统
echo ====================
python user_behavior_monitor.py
pause
"""
    
    # Linux/Mac shell脚本
    linux_sh = """#!/bin/bash
echo "用户行为异常检测系统"
echo "===================="
python3 user_behavior_monitor.py
"""
    
    try:
        # 创建Windows启动脚本
        with open("start_monitor.bat", "w", encoding="utf-8") as f:
            f.write(windows_bat)
        
        # 创建Linux/Mac启动脚本
        with open("start_monitor.sh", "w", encoding="utf-8") as f:
            f.write(linux_sh)
        
        # 设置执行权限
        os.chmod("start_monitor.sh", 0o755)
        
        print("✓ 启动脚本创建完成")
        print("  - Windows: start_monitor.bat")
        print("  - Linux/Mac: ./start_monitor.sh")
        return True
        
    except Exception as e:
        print(f"✗ 启动脚本创建失败: {e}")
        return False

def create_desktop_shortcut():
    """创建桌面快捷方式"""
    print("\n=== 创建桌面快捷方式 ===")
    
    try:
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Windows桌面快捷方式
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "用户行为监控.lnk"
            
            # 使用PowerShell创建快捷方式
            ps_script = f"""
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{os.getcwd()}\\user_behavior_monitor.py"
$Shortcut.WorkingDirectory = "{os.getcwd()}"
$Shortcut.Description = "用户行为异常检测系统"
$Shortcut.Save()
"""
            
            with open("create_shortcut.ps1", "w", encoding="utf-8") as f:
                f.write(ps_script)
            
            # 执行PowerShell脚本
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", "create_shortcut.ps1"], 
                         capture_output=True)
            
            # 清理临时文件
            os.remove("create_shortcut.ps1")
            
            print("✓ Windows桌面快捷方式创建完成")
            
        elif system == "Linux":
            # Linux桌面文件
            desktop = Path.home() / "Desktop"
            desktop_file = desktop / "user-behavior-monitor.desktop"
            
            desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=用户行为监控
Comment=用户行为异常检测系统
Exec={os.getcwd()}/user_behavior_monitor.py
Icon=terminal
Terminal=true
Categories=System;Security;
"""
            
            with open(desktop_file, "w", encoding="utf-8") as f:
                f.write(desktop_content)
            
            os.chmod(desktop_file, 0o755)
            print("✓ Linux桌面快捷方式创建完成")
            
        else:
            print("⚠️  不支持的操作系统，跳过桌面快捷方式创建")
            
        return True
        
    except Exception as e:
        print(f"✗ 桌面快捷方式创建失败: {e}")
        return False

def optimize_database():
    """优化数据库"""
    print("\n=== 优化数据库 ===")
    
    try:
        from src.utils.config.config_loader import ConfigLoader
        config = ConfigLoader()
        db_path = Path(config.get_paths()['database'])
        
        if not db_path.exists():
            print("⚠️  数据库不存在，将在首次运行时创建")
            return True
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建索引优化查询性能
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_mouse_events_user_timestamp ON mouse_events(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_mouse_events_session ON mouse_events(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_features_user ON features(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_user_timestamp ON predictions(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_user_timestamp ON alerts(user_id, timestamp)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # 分析表以优化查询计划
        cursor.execute("ANALYZE")
        
        conn.commit()
        conn.close()
        
        print("✓ 数据库优化完成")
        return True
        
    except Exception as e:
        print(f"✗ 数据库优化失败: {e}")
        return False

def create_system_service():
    """创建系统服务"""
    print("\n=== 创建系统服务 ===")
    
    try:
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Windows服务脚本
            service_script = f"""@echo off
sc create "UserBehaviorMonitor" binPath= "python {os.getcwd()}\\user_behavior_monitor.py" start= auto
sc description "UserBehaviorMonitor" "用户行为异常检测系统"
echo Windows服务创建完成
echo 使用以下命令管理服务:
echo   sc start UserBehaviorMonitor
echo   sc stop UserBehaviorMonitor
echo   sc delete UserBehaviorMonitor
"""
            
            with open("install_service.bat", "w", encoding="utf-8") as f:
                f.write(service_script)
            
            print("✓ Windows服务脚本创建完成")
            print("  运行 install_service.bat 安装服务")
            
        elif system == "Linux":
            # Linux systemd服务
            service_content = f"""[Unit]
Description=User Behavior Monitor
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory={os.getcwd()}
ExecStart=/usr/bin/python3 {os.getcwd()}/user_behavior_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
            
            with open("user-behavior-monitor.service", "w", encoding="utf-8") as f:
                f.write(service_content)
            
            print("✓ Linux systemd服务文件创建完成")
            print("  使用以下命令安装服务:")
            print("  sudo cp user-behavior-monitor.service /etc/systemd/system/")
            print("  sudo systemctl enable user-behavior-monitor")
            print("  sudo systemctl start user-behavior-monitor")
            
        else:
            print("⚠️  不支持的操作系统，跳过服务创建")
            
        return True
        
    except Exception as e:
        print(f"✗ 系统服务创建失败: {e}")
        return False

def create_documentation():
    """创建文档"""
    print("\n=== 创建文档 ===")
    
    try:
        # 创建快速开始指南
        quick_start = """# 用户行为异常检测系统 - 快速开始

## 系统要求
- Windows 10/11 或 Linux/macOS
- Python 3.7+
- 2GB+ RAM
- 1GB+ 磁盘空间

## 快速启动

### 方法一：直接运行
```bash
python user_behavior_monitor.py
```

### 方法二：使用启动脚本
- Windows: 双击 `start_monitor.bat`
- Linux/Mac: 运行 `./start_monitor.sh`

### 方法三：桌面快捷方式
- 双击桌面上的"用户行为监控"图标

## 使用流程

1. **启动系统**: 运行主程序
2. **自动工作流程**: 系统自动执行数据采集 → 特征处理 → 模型训练 → 异常检测
3. **快捷键控制**: 使用快捷键进行额外控制

## 快捷键说明
| 快捷键 | 功能 |
|--------|------|
| `rrrr` | 重新采集和训练 |
| `aaaa` | 手动触发告警弹窗 |
| `qqqq` | 退出系统 |

## 故障排除

### 常见问题
1. **依赖安装失败**: 运行 `python install_dependencies.py`
2. **快捷键无响应**: 以管理员权限运行
3. **数据采集失败**: 检查鼠标权限设置

### 日志文件
- 主日志: `logs/monitor_*.log`
- 错误日志: `logs/error_*.log`
- 调试日志: `logs/debug_*.log`

## 技术支持
- 查看详细文档: `PRODUCT_ARCHITECTURE.md`
- 运行测试: `python test_warning_dialog.py`
- 系统诊断: `python test_system_consistency.py`
"""
        
        with open("QUICK_START.md", "w", encoding="utf-8") as f:
            f.write(quick_start)
        
        # 创建版本信息
        version_info = {
            "version": "1.2.0",
            "build_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.system(),
            "features": [
                "实时鼠标行为监控",
                "机器学习异常检测",
                "自动锁屏保护",
                "自动工作流程",
                "简化快捷键控制",
                "详细日志记录"
            ]
        }
        
        with open("version.json", "w", encoding="utf-8") as f:
            json.dump(version_info, f, indent=2, ensure_ascii=False)
        
        print("✓ 文档创建完成")
        print("  - QUICK_START.md: 快速开始指南")
        print("  - version.json: 版本信息")
        return True
        
    except Exception as e:
        print(f"✗ 文档创建失败: {e}")
        return False

def main():
    """主函数"""
    print("用户行为异常检测系统 - 优化脚本")
    print("=" * 50)
    
    # 检查系统要求
    if not check_system_requirements():
        print("❌ 系统要求检查失败")
        return 1
    
    # 优化配置
    if not optimize_configuration():
        print("❌ 配置优化失败")
        return 1
    
    # 创建启动脚本
    if not create_launcher_scripts():
        print("❌ 启动脚本创建失败")
        return 1
    
    # 创建桌面快捷方式
    create_desktop_shortcut()
    
    # 优化数据库
    optimize_database()
    
    # 创建系统服务
    create_system_service()
    
    # 创建文档
    create_documentation()
    
    print("\n" + "=" * 50)
    print("🎉 系统优化完成！")
    print("\n现在你可以使用以下方式启动系统:")
    print("1. 直接运行: python user_behavior_monitor.py")
    print("2. 启动脚本: start_monitor.bat (Windows) 或 ./start_monitor.sh (Linux/Mac)")
    print("3. 桌面快捷方式: 双击桌面图标")
    print("4. 系统服务: 安装为系统服务自动启动")
    print("\n查看 QUICK_START.md 获取详细使用说明")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
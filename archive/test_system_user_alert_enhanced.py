#!/usr/bin/env python3
"""
增强的system用户告警测试脚本
专门测试UID 0环境下的多模态告警功能
"""

import os
import sys
import time
import subprocess
import platform
from pathlib import Path
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_current_user():
    """检查当前用户信息"""
    print("🔍 检查当前用户信息...")
    
    user_info = {
        'platform': platform.system(),
        'user_id': os.getuid() if hasattr(os, 'getuid') else 'unknown',
        'username': os.getenv('USER', os.getenv('USERNAME', 'unknown')),
        'is_root': os.getuid() == 0 if hasattr(os, 'getuid') else False,
        'display': os.getenv('DISPLAY', 'not_set'),
        'home': os.getenv('HOME', 'not_set'),
        'shell': os.getenv('SHELL', 'not_set')
    }
    
    print(f"平台: {user_info['platform']}")
    print(f"用户ID: {user_info['user_id']}")
    print(f"用户名: {user_info['username']}")
    print(f"是否root: {user_info['is_root']}")
    print(f"显示环境: {user_info['display']}")
    print(f"主目录: {user_info['home']}")
    print(f"Shell: {user_info['shell']}")
    
    return user_info

def test_alert_methods():
    """测试各种告警方法"""
    print("\n🧪 测试各种告警方法...")
    
    # 1. 测试控制台告警
    print("\n1️⃣ 测试控制台告警:")
    console_alert = """
================================================================================
🚨 安全告警 - WARNING
================================================================================
时间: {timestamp}
用户: system_user
类型: 异常行为检测
消息: 检测到异常鼠标行为模式
异常分数: 0.85
严重程度: warning
================================================================================
⚠️  请立即检查系统安全状态
⚠️  此告警已记录到文件
⚠️  如需查看详细日志，请检查: logs/monitor_*.log
================================================================================
""".format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    print(console_alert)
    
    # 2. 测试文件告警
    print("\n2️⃣ 测试文件告警:")
    alert_dir = Path('logs/alerts')
    alert_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建告警文件
    alert_file = alert_dir / f"system_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    alert_content = f"""
================================================================================
🚨 系统用户安全告警 - WARNING
================================================================================
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
用户: system_user (UID: 0)
类型: 异常行为检测
消息: 检测到异常鼠标行为模式，可能为安全威胁
异常分数: 0.85
严重程度: warning
环境: system用户无GUI环境
================================================================================

⚠️  系统用户告警说明:
⚠️  由于当前以system用户(UID 0)运行，无法显示GUI弹窗
⚠️  告警已通过以下方式发送:
⚠️  1. 控制台输出 (如果可见)
⚠️  2. 日志文件记录
⚠️  3. 告警文件写入
⚠️  4. 系统日志 (如果可用)
⚠️  5. 声音告警 (如果可用)

⚠️  建议操作:
⚠️  1. 检查 logs/alerts/ 目录下的告警文件
⚠️  2. 查看系统日志获取详细信息
⚠️  3. 检查监控日志: logs/monitor_*.log
⚠️  4. 考虑切换到有GUI的用户环境

================================================================================
"""
    
    with open(alert_file, 'w', encoding='utf-8') as f:
        f.write(alert_content)
    
    print(f"✅ 告警文件已创建: {alert_file}")
    
    # 3. 测试实时告警文件
    realtime_file = alert_dir / 'realtime_alerts.txt'
    with open(realtime_file, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] WARNING: 系统用户异常行为检测 - 异常分数: 0.85\n")
    
    print(f"✅ 实时告警已写入: {realtime_file}")
    
    # 4. 测试系统日志
    print("\n3️⃣ 测试系统日志:")
    try:
        if platform.system() == 'Linux':
            # Linux syslog
            log_message = f"UserBehaviorMonitor[{os.getpid()}]: 系统用户异常行为检测 - 用户: system_user, 异常分数: 0.85"
            subprocess.run(['logger', '-p', 'user.warning', log_message], check=False)
            print("✅ syslog告警已发送")
        elif platform.system() == 'Windows':
            # Windows事件日志
            print("ℹ️  Windows事件日志需要管理员权限")
        else:
            print("ℹ️  当前平台不支持系统日志")
    except Exception as e:
        print(f"⚠️  系统日志发送失败: {e}")
    
    # 5. 测试声音告警
    print("\n4️⃣ 测试声音告警:")
    try:
        if platform.system() == 'Linux':
            # Linux声音告警
            subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'], check=False)
            print("✅ 声音告警已播放")
        elif platform.system() == 'Windows':
            # Windows声音告警
            import winsound
            winsound.MessageBeep(winsound.MB_ICONWARNING)
            print("✅ 声音告警已播放")
        else:
            print("ℹ️  当前平台不支持声音告警")
    except Exception as e:
        print(f"⚠️  声音告警失败: {e}")

def test_alert_monitoring():
    """测试告警监控功能"""
    print("\n📊 测试告警监控功能...")
    
    # 创建告警监控脚本
    monitor_script = """
#!/bin/bash
# 告警监控脚本 - 适用于system用户环境

ALERT_DIR="logs/alerts"
REALTIME_FILE="$ALERT_DIR/realtime_alerts.txt"
LOG_DIR="logs"

echo "🔍 启动告警监控..."
echo "监控目录: $ALERT_DIR"
echo "实时告警文件: $REALTIME_FILE"

# 监控实时告警文件
if [ -f "$REALTIME_FILE" ]; then
    echo "📋 最近的告警记录:"
    tail -10 "$REALTIME_FILE"
else
    echo "⚠️  实时告警文件不存在"
fi

# 监控告警目录
echo "📁 告警文件列表:"
if [ -d "$ALERT_DIR" ]; then
    ls -la "$ALERT_DIR"/*.txt 2>/dev/null || echo "暂无告警文件"
else
    echo "⚠️  告警目录不存在"
fi

# 监控日志文件
echo "📝 最近的日志记录:"
if [ -d "$LOG_DIR" ]; then
    find "$LOG_DIR" -name "*.log" -type f -exec tail -5 {} \\; 2>/dev/null || echo "暂无日志文件"
else
    echo "⚠️  日志目录不存在"
fi

echo "✅ 告警监控完成"
"""
    
    monitor_file = Path('alert_monitor.sh')
    with open(monitor_file, 'w', encoding='utf-8') as f:
        f.write(monitor_script)
    
    # 设置执行权限
    os.chmod(monitor_file, 0o755)
    
    print(f"✅ 告警监控脚本已创建: {monitor_file}")
    
    # 运行监控脚本
    try:
        result = subprocess.run(['bash', str(monitor_file)], 
                              capture_output=True, text=True, timeout=30)
        print("📊 监控结果:")
        print(result.stdout)
        if result.stderr:
            print("⚠️  监控警告:")
            print(result.stderr)
    except Exception as e:
        print(f"⚠️  监控脚本执行失败: {e}")

def create_system_user_alert_guide():
    """创建system用户告警指南"""
    print("\n📖 创建system用户告警指南...")
    
    guide_content = """
# System用户告警指南

## 概述
当用户行为监控系统以system用户(UID 0)运行时，由于没有GUI环境，无法显示弹窗告警。
本指南介绍如何在system用户环境下实现有效的告警机制。

## 告警方式

### 1. 控制台告警
- **适用场景**: 系统有控制台输出
- **特点**: 实时显示，醒目格式
- **查看方式**: 直接查看控制台输出

### 2. 文件告警
- **位置**: `logs/alerts/`
- **文件类型**: 
  - `alert_YYYYMMDD_HHMMSS.txt`: 详细告警文件
  - `realtime_alerts.txt`: 实时告警记录
- **查看方式**: 定期检查告警目录

### 3. 日志告警
- **位置**: `logs/monitor_*.log`
- **特点**: 详细的系统运行日志
- **查看方式**: 使用日志查看工具

### 4. 系统日志
- **Linux**: syslog (`/var/log/syslog`)
- **Windows**: 事件查看器
- **查看方式**: 系统日志工具

### 5. 声音告警
- **Linux**: 使用paplay播放系统音效
- **Windows**: 使用系统蜂鸣声
- **特点**: 需要音频设备

## 监控脚本

### 告警监控脚本
```bash
# 运行告警监控
bash alert_monitor.sh

# 实时监控告警文件
tail -f logs/alerts/realtime_alerts.txt

# 查看最新告警
ls -la logs/alerts/ | tail -10
```

### 系统日志监控
```bash
# Linux syslog监控
tail -f /var/log/syslog | grep UserBehaviorMonitor

# 查看最近的告警
journalctl -u UserBehaviorMonitor --since "1 hour ago"
```

## 配置建议

### 1. 启用所有告警方式
```yaml
alert:
  enable_console_alert: true
  enable_file_alert: true
  enable_log_alert: true
  enable_system_notification: true
  enable_sound_alert: true
```

### 2. 设置告警目录权限
```bash
# 确保告警目录可写
chmod 755 logs/alerts/
chown system:system logs/alerts/
```

### 3. 配置日志轮转
```bash
# 防止日志文件过大
logrotate -f /etc/logrotate.d/user_behavior_monitor
```

## 故障排除

### 1. 告警文件不生成
- 检查目录权限
- 检查磁盘空间
- 查看错误日志

### 2. 系统日志不记录
- 检查syslog服务状态
- 检查用户权限
- 查看系统日志配置

### 3. 声音告警不工作
- 检查音频设备
- 检查音频服务
- 检查权限设置

## 最佳实践

1. **定期检查**: 设置定时任务定期检查告警文件
2. **日志轮转**: 配置日志轮转防止文件过大
3. **权限管理**: 确保告警目录有适当权限
4. **监控集成**: 将告警集成到系统监控工具
5. **备份策略**: 定期备份告警和日志文件

## 紧急情况处理

### 发现异常告警时：
1. 立即检查告警文件内容
2. 查看系统日志获取详细信息
3. 检查用户活动日志
4. 必要时锁定系统或强制登出
5. 联系系统管理员

### 告警系统故障时：
1. 检查服务状态
2. 查看错误日志
3. 重启告警服务
4. 检查配置文件
5. 验证权限设置
"""
    
    guide_file = Path('SYSTEM_USER_ALERT_GUIDE.md')
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"✅ 告警指南已创建: {guide_file}")

def main():
    """主函数"""
    print("🚨 System用户告警测试")
    print("=" * 50)
    
    # 检查当前用户
    user_info = check_current_user()
    
    # 测试告警方法
    test_alert_methods()
    
    # 测试告警监控
    test_alert_monitoring()
    
    # 创建告警指南
    create_system_user_alert_guide()
    
    print("\n" + "=" * 50)
    print("✅ System用户告警测试完成!")
    print("\n📋 生成的文件:")
    print("- logs/alerts/ - 告警文件目录")
    print("- alert_monitor.sh - 告警监控脚本")
    print("- SYSTEM_USER_ALERT_GUIDE.md - 告警指南")
    print("\n💡 建议:")
    print("1. 定期运行 alert_monitor.sh 检查告警")
    print("2. 查看 SYSTEM_USER_ALERT_GUIDE.md 了解详细使用方法")
    print("3. 配置定时任务自动检查告警文件")
    print("4. 将告警集成到系统监控工具中")
    print("=" * 50)

if __name__ == '__main__':
    main()

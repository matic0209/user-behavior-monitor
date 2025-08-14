#!/usr/bin/env python3
"""
System用户告警功能测试脚本
用于测试在system用户（uid=0）环境下的告警功能
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_environment():
    """测试当前运行环境"""
    print("=== 环境检测 ===")
    
    # 检查用户ID
    try:
        uid = os.getuid()
        print(f"当前用户ID: {uid}")
        print(f"是否为system用户: {'是' if uid == 0 else '否'}")
    except AttributeError:
        print("当前用户ID: Windows系统")
        print("是否为system用户: 未知")
    
    # 检查显示环境
    display = os.environ.get('DISPLAY', '')
    print(f"DISPLAY环境变量: {display}")
    print(f"显示环境可用: {'是' if display else '否'}")
    
    # 检查GUI可用性
    try:
        import tkinter as tk
        print("tkinter: 可用")
        
        # 尝试创建窗口
        try:
            root = tk.Tk()
            root.withdraw()
            print("GUI窗口创建: 成功")
            root.destroy()
        except Exception as e:
            print(f"GUI窗口创建: 失败 - {e}")
            
    except ImportError:
        print("tkinter: 不可用")
    
    # 检查系统通知
    try:
        import subprocess
        result = subprocess.run(['which', 'notify-send'], capture_output=True, text=True)
        print(f"notify-send: {'可用' if result.returncode == 0 else '不可用'}")
    except Exception:
        print("notify-send: 检查失败")

def test_alert_service():
    """测试告警服务"""
    print("\n=== 告警服务测试 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        # 创建告警服务实例
        alert_service = AlertService()
        
        # 测试告警发送
        print("发送测试告警...")
        test_data = {
            'anomaly_score': 0.85,
            'user_id': 'test_user',
            'timestamp': time.time()
        }
        
        success = alert_service.send_alert(
            user_id='test_user',
            alert_type='behavior_anomaly',
            message='测试异常行为检测',
            severity='warning',
            data=test_data,
            bypass_cooldown=True
        )
        
        print(f"告警发送: {'成功' if success else '失败'}")
        
        return True
        
    except Exception as e:
        print(f"告警服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_console_alert():
    """测试控制台告警"""
    print("\n=== 控制台告警测试 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        alert_service = AlertService()
        
        # 测试控制台告警
        test_data = {
            'anomaly_score': 0.9,
            'user_id': 'system_user',
            'timestamp': time.time()
        }
        
        print("发送控制台告警...")
        alert_service._send_console_alert(
            user_id='system_user',
            alert_type='behavior_anomaly',
            message='System用户环境下的异常行为检测',
            severity='critical',
            data=test_data
        )
        
        print("控制台告警测试完成")
        return True
        
    except Exception as e:
        print(f"控制台告警测试失败: {e}")
        return False

def test_sound_alert():
    """测试声音告警"""
    print("\n=== 声音告警测试 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        alert_service = AlertService()
        
        # 测试不同严重程度的声音
        print("播放警告声音...")
        alert_service._send_sound_alert('warning')
        time.sleep(1)
        
        print("播放紧急声音...")
        alert_service._send_sound_alert('critical')
        time.sleep(1)
        
        print("播放普通告警声音...")
        alert_service._send_sound_alert('alert')
        
        print("声音告警测试完成")
        return True
        
    except Exception as e:
        print(f"声音告警测试失败: {e}")
        return False

def test_system_notification():
    """测试系统通知"""
    print("\n=== 系统通知测试 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        alert_service = AlertService()
        
        # 测试系统通知
        print("发送系统通知...")
        alert_service._send_system_notification(
            user_id='system_user',
            alert_type='behavior_anomaly',
            message='System用户环境下的系统通知测试',
            severity='warning'
        )
        
        print("系统通知测试完成")
        return True
        
    except Exception as e:
        print(f"系统通知测试失败: {e}")
        return False

def test_console_warning():
    """测试控制台警告"""
    print("\n=== 控制台警告测试 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        alert_service = AlertService()
        
        # 测试控制台警告（短时间）
        print("显示控制台警告（5秒）...")
        original_duration = alert_service.warning_duration
        alert_service.warning_duration = 5  # 临时设置为5秒
        
        alert_service._show_console_warning(0.95)
        
        alert_service.warning_duration = original_duration
        print("控制台警告测试完成")
        return True
        
    except Exception as e:
        print(f"控制台警告测试失败: {e}")
        return False

def main():
    """主函数"""
    print("System用户告警功能测试")
    print("=" * 50)
    
    # 测试环境
    test_environment()
    
    # 测试各项功能
    tests = [
        ("告警服务", test_alert_service),
        ("控制台告警", test_console_alert),
        ("声音告警", test_sound_alert),
        ("系统通知", test_system_notification),
        ("控制台警告", test_console_warning),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    # 统计
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！System用户环境下的告警功能正常")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")

if __name__ == "__main__":
    main()

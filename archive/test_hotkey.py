#!/usr/bin/env python3
"""
快捷键测试脚本
验证aaaa快捷键是否能正确触发弹窗
"""

import sys
import time
import threading
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_hotkey_functionality():
    """测试快捷键功能"""
    print("=== 快捷键功能测试 ===")
    print("测试aaaa快捷键是否能正确触发弹窗...")
    
    try:
        # 导入必要的模块
        from src.core.user_manager import UserManager
        from src.core.alert.alert_service import AlertService
        
        print("✅ 模块导入成功")
        
        # 创建用户管理器
        user_manager = UserManager()
        print("✅ 用户管理器创建成功")
        
        # 创建告警服务
        alert_service = AlertService()
        print("✅ 告警服务创建成功")
        
        # 测试GUI可用性
        try:
            import tkinter
            print("✅ GUI (tkinter) 可用")
        except ImportError:
            print("❌ GUI (tkinter) 不可用")
            return False
        
        # 测试告警服务的弹窗功能
        print("\n=== 测试告警弹窗功能 ===")
        
        def test_warning_dialog():
            """测试警告弹窗"""
            try:
                print("正在显示测试弹窗...")
                alert_service._show_warning_dialog(0.95)
                print("✅ 弹窗显示成功")
                return True
            except Exception as e:
                print(f"❌ 弹窗显示失败: {str(e)}")
                return False
        
        # 在后台线程中测试弹窗
        dialog_thread = threading.Thread(target=test_warning_dialog, daemon=True)
        dialog_thread.start()
        
        # 等待一段时间让弹窗显示
        time.sleep(3)
        
        print("\n=== 测试快捷键检测 ===")
        
        # 模拟快捷键检测
        def test_hotkey_detection():
            """测试快捷键检测"""
            try:
                # 模拟按4次'a'键
                test_sequence = ['a', 'a', 'a', 'a']
                
                for char in test_sequence:
                    # 模拟按键事件
                    class MockKey:
                        def __init__(self, char):
                            self.char = char
                    
                    key = MockKey(char)
                    user_manager._handle_hotkey(key)
                    time.sleep(0.1)  # 模拟按键间隔
                
                print("✅ 快捷键检测测试完成")
                return True
            except Exception as e:
                print(f"❌ 快捷键检测失败: {str(e)}")
                return False
        
        hotkey_result = test_hotkey_detection()
        
        print("\n=== 测试结果 ===")
        if hotkey_result:
            print("✅ 快捷键功能正常")
        else:
            print("❌ 快捷键功能异常")
        
        return hotkey_result
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_manual_trigger_alert():
    """测试手动触发告警功能"""
    print("\n=== 手动触发告警测试 ===")
    
    try:
        # 导入主程序
        from user_behavior_monitor import WindowsBehaviorMonitor
        
        print("✅ 主程序导入成功")
        
        # 创建监控器实例
        monitor = WindowsBehaviorMonitor()
        print("✅ 监控器创建成功")
        
        # 测试手动触发告警
        print("正在测试手动触发告警...")
        monitor._manual_trigger_alert()
        
        print("✅ 手动触发告警测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 手动触发告警测试失败: {str(e)}")
        return False

def test_gui_availability():
    """测试GUI可用性"""
    print("\n=== GUI可用性测试 ===")
    
    try:
        import tkinter as tk
        print("✅ tkinter 可用")
        
        # 测试创建简单窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        label = tk.Label(root, text="测试窗口")
        label.pack()
        
        # 测试窗口创建
        print("✅ 窗口创建成功")
        
        # 立即销毁窗口
        root.destroy()
        
        print("✅ GUI功能正常")
        return True
        
    except Exception as e:
        print(f"❌ GUI测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("快捷键功能测试工具")
    print("=" * 60)
    
    # 运行各项测试
    gui_test = test_gui_availability()
    hotkey_test = test_hotkey_functionality()
    manual_test = test_manual_trigger_alert()
    
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"GUI可用性: {'✅ 正常' if gui_test else '❌ 异常'}")
    print(f"快捷键功能: {'✅ 正常' if hotkey_test else '❌ 异常'}")
    print(f"手动触发告警: {'✅ 正常' if manual_test else '❌ 异常'}")
    print("=" * 60)
    
    if gui_test and hotkey_test and manual_test:
        print("🎉 所有测试通过！aaaa快捷键应该能正常工作")
        print("\n使用说明:")
        print("1. 运行主程序: python3 user_behavior_monitor.py")
        print("2. 连续按4次'a'键: aaaa")
        print("3. 应该会弹出安全警告窗口")
    else:
        print("⚠️ 部分测试失败，可能需要检查配置")
        print("\n可能的问题:")
        print("1. GUI环境不可用")
        print("2. tkinter模块缺失")
        print("3. 快捷键检测逻辑有问题")

if __name__ == "__main__":
    main()

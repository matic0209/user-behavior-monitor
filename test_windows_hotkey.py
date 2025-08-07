#!/usr/bin/env python3
"""
Windows环境快捷键测试脚本
在Windows环境下测试aaaa快捷键功能
"""

import sys
import time
import threading
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_windows_environment():
    """测试Windows环境"""
    print("=== Windows环境测试 ===")
    
    # 检查Windows API
    try:
        import win32api
        import win32con
        print("✅ Windows API 可用")
        windows_available = True
    except ImportError:
        print("❌ Windows API 不可用")
        windows_available = False
    
    # 检查GUI
    try:
        import tkinter as tk
        print("✅ tkinter GUI 可用")
        gui_available = True
    except ImportError:
        print("❌ tkinter GUI 不可用")
        gui_available = False
    
    # 检查pynput
    try:
        from pynput import keyboard
        print("✅ pynput 键盘监听可用")
        pynput_available = True
    except ImportError:
        print("❌ pynput 键盘监听不可用")
        pynput_available = False
    
    return windows_available, gui_available, pynput_available

def test_hotkey_workflow():
    """测试快捷键工作流程"""
    print("\n=== 快捷键工作流程测试 ===")
    
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
        print(f"❌ 快捷键工作流程测试失败: {str(e)}")
        return False

def test_gui_dialog():
    """测试GUI弹窗"""
    print("\n=== GUI弹窗测试 ===")
    
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        # 创建测试窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 显示消息框
        result = messagebox.showwarning(
            "测试弹窗",
            "这是一个测试弹窗\n\n如果您看到这个弹窗，说明GUI功能正常。",
            parent=root
        )
        
        root.destroy()
        
        print("✅ GUI弹窗测试成功")
        return True
        
    except Exception as e:
        print(f"❌ GUI弹窗测试失败: {str(e)}")
        return False

def test_keyboard_listener():
    """测试键盘监听"""
    print("\n=== 键盘监听测试 ===")
    
    try:
        from pynput import keyboard
        
        def on_press(key):
            try:
                if hasattr(key, 'char'):
                    print(f"按键: {key.char}")
                else:
                    print(f"特殊键: {key}")
            except Exception as e:
                print(f"按键处理错误: {str(e)}")
        
        def on_release(key):
            if key == keyboard.Key.esc:
                return False  # 停止监听
        
        print("开始键盘监听测试...")
        print("请按任意键测试，按ESC键停止")
        
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
        
        print("✅ 键盘监听测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 键盘监听测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("Windows快捷键功能测试工具")
    print("=" * 60)
    
    # 测试Windows环境
    windows_ok, gui_ok, pynput_ok = test_windows_environment()
    
    # 测试GUI弹窗
    gui_test = test_gui_dialog() if gui_ok else False
    
    # 测试快捷键工作流程
    workflow_test = test_hotkey_workflow()
    
    # 测试键盘监听（可选）
    keyboard_test = test_keyboard_listener() if pynput_ok else False
    
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"Windows API: {'✅ 可用' if windows_ok else '❌ 不可用'}")
    print(f"GUI (tkinter): {'✅ 可用' if gui_ok else '❌ 不可用'}")
    print(f"键盘监听 (pynput): {'✅ 可用' if pynput_ok else '❌ 不可用'}")
    print(f"GUI弹窗测试: {'✅ 成功' if gui_test else '❌ 失败'}")
    print(f"快捷键工作流程: {'✅ 成功' if workflow_test else '❌ 失败'}")
    print(f"键盘监听测试: {'✅ 成功' if keyboard_test else '❌ 失败'}")
    print("=" * 60)
    
    if gui_ok and workflow_test:
        print("🎉 aaaa快捷键应该能正常工作！")
        print("\n使用说明:")
        print("1. 运行主程序: python3 user_behavior_monitor.py")
        print("2. 连续按4次'a'键: aaaa")
        print("3. 应该会弹出安全警告窗口")
        print("4. 如果弹窗失败，会记录告警到数据库")
    else:
        print("⚠️ 部分功能不可用")
        print("\n可能的问题:")
        if not gui_ok:
            print("- tkinter模块缺失")
        if not pynput_ok:
            print("- pynput模块缺失")
        if not windows_ok:
            print("- Windows API不可用")
        print("\n建议:")
        print("1. 在Windows环境下运行")
        print("2. 安装必要的依赖: pip install pynput")
        print("3. 确保有GUI环境")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
GUI测试文件
用于测试tkinter是否正常工作
"""

import tkinter as tk
from tkinter import messagebox
import sys

def test_basic_gui():
    """测试基本的GUI功能"""
    try:
        print("开始GUI测试...")
        
        # 创建主窗口
        root = tk.Tk()
        root.title("GUI测试")
        root.geometry("400x300")
        root.configure(bg='#ff4444')
        
        # 设置窗口置顶
        root.attributes('-topmost', True)
        root.focus_force()
        
        # 创建标签
        label = tk.Label(
            root,
            text="🚨 测试警告窗口\n\n这是一个测试窗口\n\n点击按钮关闭",
            font=("Arial", 16),
            fg="white",
            bg="#ff4444",
            justify="center"
        )
        label.pack(pady=50)
        
        # 创建按钮
        button = tk.Button(
            root,
            text="关闭测试",
            font=("Arial", 14, "bold"),
            bg="#f44336",
            fg="white",
            command=root.destroy
        )
        button.pack(pady=20)
        
        print("GUI窗口已创建，请查看是否显示")
        
        # 启动主循环
        root.mainloop()
        
        print("GUI测试完成")
        return True
        
    except Exception as e:
        print(f"GUI测试失败: {str(e)}")
        return False

def test_messagebox():
    """测试消息框功能"""
    try:
        print("测试消息框...")
        result = messagebox.showwarning(
            "测试警告",
            "这是一个测试警告消息框\n\n点击确定关闭"
        )
        print(f"消息框结果: {result}")
        return True
    except Exception as e:
        print(f"消息框测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== GUI功能测试 ===")
    
    # 检查tkinter是否可用
    try:
        import tkinter
        print("✅ tkinter可用")
    except ImportError as e:
        print(f"❌ tkinter不可用: {e}")
        sys.exit(1)
    
    # 测试基本GUI
    if test_basic_gui():
        print("✅ 基本GUI测试通过")
    else:
        print("❌ 基本GUI测试失败")
    
    # 测试消息框
    if test_messagebox():
        print("✅ 消息框测试通过")
    else:
        print("❌ 消息框测试失败")
    
    print("=== 测试完成 ===") 
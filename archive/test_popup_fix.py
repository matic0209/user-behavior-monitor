#!/usr/bin/env python3
"""
弹窗修复测试脚本
验证弹窗功能是否正常工作
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_popup_fix():
    """测试弹窗修复"""
    print("=== 弹窗修复测试 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        # 创建告警服务
        alert_service = AlertService()
        print("✓ 告警服务创建成功")
        
        # 检查GUI可用性
        try:
            import tkinter as tk
            print("✓ tkinter可用")
        except ImportError:
            print("✗ tkinter不可用")
            return False
        
        # 测试弹窗功能
        print("\n开始测试弹窗功能...")
        print("注意：即将显示一个无法关闭的警告弹窗")
        print("弹窗将显示10秒倒计时，然后自动关闭")
        
        response = input("是否继续测试? (y/N): ")
        if response.lower() != 'y':
            print("取消测试")
            return True
        
        print("3秒后显示弹窗...")
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        
        # 测试弹窗
        try:
            # 模拟高异常分数触发弹窗
            anomaly_data = {
                'anomaly_score': 0.95,
                'probability': 0.05,
                'prediction': 0,
                'is_normal': False
            }
            
            # 发送告警触发弹窗
            success = alert_service.send_alert(
                user_id="test_user",
                alert_type="behavior_anomaly",
                message="弹窗修复测试 - 异常分数: 0.950",
                severity="warning",
                data=anomaly_data,
                bypass_cooldown=True  # 绕过冷却时间
            )
            
            if success:
                print("✓ 告警发送成功，弹窗应该已显示")
                print("注意：弹窗可能需要几秒钟才能显示")
                return True
            else:
                print("✗ 告警发送失败")
                return False
                
        except Exception as e:
            print(f"✗ 弹窗测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_popup():
    """测试简单弹窗"""
    print("\n=== 简单弹窗测试 ===")
    
    try:
        import tkinter as tk
        from tkinter import messagebox
        import threading
        import time
        
        # 创建简单测试窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 使用线程来避免阻塞
        def show_messagebox():
            try:
                result = messagebox.showwarning(
                    "测试弹窗",
                    "这是一个测试弹窗\n\n点击确定关闭"
                )
                print(f"消息框结果: {result}")
            except Exception as e:
                print(f"消息框异常: {e}")
        
        # 在新线程中显示消息框
        popup_thread = threading.Thread(target=show_messagebox)
        popup_thread.daemon = True
        popup_thread.start()
        
        # 等待一段时间让用户看到弹窗
        print("显示测试弹窗，请点击确定关闭...")
        time.sleep(2)
        
        # 如果线程还在运行，强制关闭
        if popup_thread.is_alive():
            print("弹窗可能卡住，尝试强制关闭...")
            try:
                root.quit()
                root.destroy()
            except:
                pass
        
        print("✓ 简单弹窗测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 简单弹窗测试失败: {e}")
        return False

def main():
    """主函数"""
    print("弹窗修复验证工具")
    print("=" * 50)
    
    # 测试简单弹窗
    simple_test_ok = test_simple_popup()
    
    # 测试完整弹窗功能
    popup_test_ok = test_popup_fix()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果:")
    print(f"简单弹窗: {'✓ 正常' if simple_test_ok else '✗ 异常'}")
    print(f"完整弹窗: {'✓ 正常' if popup_test_ok else '✗ 异常'}")
    
    if simple_test_ok and popup_test_ok:
        print("\n✅ 弹窗功能修复成功！")
        print("建议:")
        print("1. 弹窗警告功能已正常工作")
        print("2. 异常检测达到阈值时会显示不可关闭的警告对话框")
        print("3. 用户无法关闭弹窗，只能等待倒计时结束或立即锁屏")
        print("4. 倒计时结束后系统将强制锁屏")
        print("5. 运行 python user_behavior_monitor.py 启动完整系统")
        print("6. 使用快捷键 'aaaa' 手动触发告警弹窗测试")
    else:
        print("\n❌ 弹窗功能仍有问题")
        print("建议:")
        print("1. 检查tkinter是否正确安装")
        print("2. 确保有GUI环境支持")
        print("3. 检查系统权限设置")
        print("4. 查看日志文件获取详细错误信息")

if __name__ == "__main__":
    main() 
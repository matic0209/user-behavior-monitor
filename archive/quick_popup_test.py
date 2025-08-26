#!/usr/bin/env python3
"""
快速弹窗测试脚本
避免GUI阻塞问题
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_gui():
    """测试基本GUI功能"""
    print("=== 基本GUI测试 ===")
    
    try:
        import tkinter as tk
        
        # 创建测试窗口
        root = tk.Tk()
        root.title("GUI测试")
        root.geometry("300x200")
        root.configure(bg='#ff4444')
        
        # 设置窗口置顶
        root.attributes('-topmost', True)
        
        # 创建标签
        label = tk.Label(
            root,
            text="GUI测试窗口\n\n点击按钮关闭",
            font=("Arial", 14),
            fg="white",
            bg="#ff4444",
            justify="center"
        )
        label.pack(pady=30)
        
        # 创建按钮
        def close_window():
            print("用户点击关闭按钮")
            root.destroy()
        
        button = tk.Button(
            root,
            text="关闭测试",
            font=("Arial", 12, "bold"),
            bg="#f44336",
            fg="white",
            command=close_window
        )
        button.pack(pady=20)
        
        print("GUI窗口已创建，请查看是否显示")
        print("窗口将显示5秒后自动关闭...")
        
        # 设置自动关闭
        root.after(5000, root.destroy)
        
        # 启动主循环
        root.mainloop()
        
        print("✓ GUI测试完成")
        return True
        
    except Exception as e:
        print(f"✗ GUI测试失败: {str(e)}")
        return False

def test_alert_service():
    """测试告警服务"""
    print("\n=== 告警服务测试 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        # 创建告警服务
        alert_service = AlertService()
        print("✓ 告警服务创建成功")
        
        # 检查配置
        print(f"系统操作启用: {alert_service.enable_system_actions}")
        print(f"锁屏阈值: {alert_service.lock_screen_threshold}")
        print(f"弹窗警告: {'启用' if alert_service.show_warning_dialog else '禁用'}")
        print(f"警告持续时间: {alert_service.warning_duration}秒")
        
        # 测试告警发送（不触发弹窗）
        test_data = {
            'anomaly_score': 0.5,  # 低于阈值，不会触发弹窗
            'probability': 0.5,
            'prediction': 1,
            'is_normal': True
        }
        
        success = alert_service.send_alert(
            user_id="test_user",
            alert_type="behavior_anomaly",
            message="测试告警 - 正常行为",
            severity="info",
            data=test_data,
            bypass_cooldown=True
        )
        
        if success:
            print("✓ 告警服务测试成功")
            return True
        else:
            print("✗ 告警服务测试失败")
            return False
            
    except Exception as e:
        print(f"✗ 告警服务测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_popup():
    """手动测试弹窗"""
    print("\n=== 手动弹窗测试 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        alert_service = AlertService()
        
        print("警告: 即将显示锁屏警告对话框！")
        print("注意：此对话框无法关闭，倒计时结束后将自动锁屏")
        print("请观察对话框的外观和功能。")
        
        response = input("是否继续? (y/N): ")
        if response.lower() != 'y':
            print("取消测试")
            return True
        
        print("3秒后显示警告对话框...")
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        
        # 模拟高异常分数触发警告
        anomaly_data = {
            'anomaly_score': 0.95,
            'probability': 0.05,
            'prediction': 0,
            'is_normal': False
        }
        
        # 发送告警触发弹窗
        alert_service.send_alert(
            user_id="test_user",
            alert_type="behavior_anomaly",
            message="手动测试 - 异常分数: 0.950",
            severity="warning",
            data=anomaly_data,
            bypass_cooldown=True
        )
        
        return True
        
    except Exception as e:
        print(f"✗ 手动弹窗测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("快速弹窗测试工具")
    print("=" * 50)
    
    # 测试基本GUI
    gui_test_ok = test_basic_gui()
    
    # 测试告警服务
    alert_test_ok = test_alert_service()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果:")
    print(f"基本GUI: {'✓ 正常' if gui_test_ok else '✗ 异常'}")
    print(f"告警服务: {'✓ 正常' if alert_test_ok else '✗ 异常'}")
    
    if gui_test_ok and alert_test_ok:
        print("\n✅ 基本功能正常！")
        print("建议:")
        print("1. GUI环境正常工作")
        print("2. 告警服务配置正确")
        print("3. 可以尝试手动弹窗测试")
        
        # 询问是否进行手动测试
        response = input("\n是否进行手动弹窗测试? (y/N): ")
        if response.lower() == 'y':
            test_manual_popup()
    else:
        print("\n❌ 存在问题")
        print("建议:")
        print("1. 检查tkinter是否正确安装")
        print("2. 确保有GUI环境支持")
        print("3. 检查系统权限设置")

if __name__ == "__main__":
    main() 
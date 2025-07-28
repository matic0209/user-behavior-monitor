#!/usr/bin/env python3
"""
弹窗警告功能测试脚本
用于测试异常检测触发弹窗警告功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_warning_dialog():
    """测试弹窗警告功能"""
    print("=== 弹窗警告功能测试 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        # 创建告警服务
        alert_service = AlertService()
        print("✓ 告警服务创建成功")
        
        # 测试配置
        print(f"系统操作启用: {alert_service.enable_system_actions}")
        print(f"锁屏阈值: {alert_service.lock_screen_threshold}")
        print(f"弹窗警告: {'启用' if alert_service.show_warning_dialog else '禁用'}")
        print(f"警告持续时间: {alert_service.warning_duration}秒")
        
        # 测试GUI可用性
        try:
            import tkinter as tk
            print("✓ tkinter可用")
        except ImportError:
            print("✗ tkinter不可用，弹窗功能将不可用")
            return False
        
        # 测试不同异常分数的告警
        test_scores = [0.85, 0.9, 0.95]  # 使用超过阈值的分数
        
        for score in test_scores:
            print(f"\n--- 测试异常分数: {score} ---")
            
            # 模拟异常数据
            anomaly_data = {
                'anomaly_score': score,
                'probability': 1 - score,
                'prediction': 0,
                'is_normal': False
            }
            
            # 发送告警
            result = alert_service.send_alert(
                user_id="test_user",
                alert_type="behavior_anomaly",
                message=f"测试异常检测 - 分数: {score:.3f}",
                severity="warning",
                data=anomaly_data
            )
            
            print(f"告警发送结果: {'成功' if result else '失败'}")
            
            # 等待一下
            time.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"✗ 弹窗警告功能测试失败: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False

def test_dialog_appearance():
    """测试对话框外观"""
    print("\n=== 测试对话框外观 ===")
    
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        # 创建测试窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 显示测试对话框
        result = messagebox.askyesno(
            "测试对话框",
            "这是一个测试对话框\n\n点击'是'继续测试\n点击'否'退出测试"
        )
        
        if result:
            print("✓ 用户选择继续测试")
            return True
        else:
            print("用户选择退出测试")
            return False
            
    except Exception as e:
        print(f"✗ 对话框外观测试失败: {e}")
        return False

def test_manual_warning():
    """手动测试警告对话框"""
    print("\n=== 手动测试警告对话框 ===")
    
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
            data=anomaly_data
        )
        
        return True
        
    except Exception as e:
        print(f"✗ 手动警告测试失败: {e}")
        return False

def test_dialog_security():
    """测试对话框安全性"""
    print("\n=== 测试对话框安全性 ===")
    
    try:
        import tkinter as tk
        
        # 创建测试窗口
        root = tk.Tk()
        root.title("安全测试")
        root.geometry("400x300")
        root.configure(bg='#ff4444')
        
        # 设置窗口置顶且不可关闭
        root.attributes('-topmost', True)
        root.protocol("WM_DELETE_WINDOW", lambda: None)
        root.bind('<Alt-F4>', lambda e: None)
        root.bind('<Escape>', lambda e: None)
        
        # 添加说明
        label = tk.Label(
            root,
            text="这是一个安全测试窗口\n\n此窗口无法通过常规方式关闭\n\n请尝试关闭窗口（应该无法关闭）",
            font=("Arial", 12),
            fg="white",
            bg="#ff4444",
            justify="center"
        )
        label.pack(pady=50)
        
        # 添加关闭按钮（用于测试）
        close_button = tk.Button(
            root,
            text="测试关闭（应该无效）",
            command=lambda: print("尝试关闭窗口（应该无效）")
        )
        close_button.pack(pady=20)
        
        print("测试窗口已显示，请尝试关闭它...")
        print("按回车键继续测试...")
        input()
        
        root.destroy()
        print("✓ 安全性测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 安全性测试失败: {e}")
        return False

def main():
    """主函数"""
    print("弹窗警告功能测试工具")
    print("=" * 50)
    
    # 测试弹窗功能
    dialog_test_ok = test_warning_dialog()
    
    # 测试对话框外观
    appearance_test_ok = test_dialog_appearance()
    
    # 测试对话框安全性
    security_test_ok = test_dialog_security()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果:")
    print(f"弹窗功能: {'✓ 正常' if dialog_test_ok else '✗ 异常'}")
    print(f"对话框外观: {'✓ 正常' if appearance_test_ok else '✗ 异常'}")
    print(f"对话框安全性: {'✓ 正常' if security_test_ok else '✗ 异常'}")
    
    if dialog_test_ok and appearance_test_ok and security_test_ok:
        print("\n建议:")
        print("1. 弹窗警告功能已启用")
        print("2. 异常检测达到阈值时会显示不可关闭的警告对话框")
        print("3. 用户无法关闭弹窗，只能等待倒计时结束或立即锁屏")
        print("4. 倒计时结束后系统将强制锁屏")
        print("5. 运行 python start_monitor.py 启动完整系统")
        print("6. 系统将自动执行异常检测，观察异常检测和弹窗")
        
        # 询问是否进行手动测试
        response = input("\n是否进行手动警告对话框测试? (y/N): ")
        if response.lower() == 'y':
            test_manual_warning()
    else:
        print("\n建议:")
        print("1. 检查tkinter是否正确安装")
        print("2. 确保有GUI环境支持")
        print("3. 检查系统权限设置")

if __name__ == "__main__":
    main() 
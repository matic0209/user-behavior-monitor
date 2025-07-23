#!/usr/bin/env python3
"""
锁屏功能测试脚本
用于测试异常检测触发锁屏功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_lock_screen():
    """测试锁屏功能"""
    print("=== 锁屏功能测试 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        # 创建告警服务
        alert_service = AlertService()
        print("✓ 告警服务创建成功")
        
        # 测试配置
        print(f"系统操作启用: {alert_service.enable_system_actions}")
        print(f"锁屏阈值: {alert_service.lock_screen_threshold}")
        print(f"告警冷却时间: {alert_service.alert_cooldown}秒")
        
        # 测试不同异常分数的告警
        test_scores = [0.5, 0.7, 0.9]
        
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
        print(f"✗ 锁屏功能测试失败: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False

def test_manual_lock():
    """手动测试锁屏"""
    print("\n=== 手动锁屏测试 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        alert_service = AlertService()
        
        print("警告: 即将执行锁屏操作！")
        print("请确保已保存所有工作。")
        
        response = input("是否继续? (y/N): ")
        if response.lower() != 'y':
            print("取消锁屏测试")
            return True
        
        print("3秒后执行锁屏...")
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        
        # 执行锁屏
        alert_service._lock_screen()
        
        return True
        
    except Exception as e:
        print(f"✗ 手动锁屏测试失败: {e}")
        return False

def test_alert_statistics():
    """测试告警统计"""
    print("\n=== 告警统计测试 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        alert_service = AlertService()
        
        # 获取告警统计
        stats = alert_service.get_alert_statistics("test_user", hours=24)
        
        print(f"告警统计:")
        print(f"  总告警数: {stats.get('total_alerts', 0)}")
        print(f"  按类型统计: {stats.get('alerts_by_type', {})}")
        print(f"  时间范围: {stats.get('time_period_hours', 24)}小时")
        
        return True
        
    except Exception as e:
        print(f"✗ 告警统计测试失败: {e}")
        return False

def main():
    """主函数"""
    print("锁屏功能测试工具")
    print("=" * 50)
    
    # 测试锁屏功能
    lock_test_ok = test_lock_screen()
    
    # 测试告警统计
    stats_test_ok = test_alert_statistics()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果:")
    print(f"锁屏功能: {'✓ 正常' if lock_test_ok else '✗ 异常'}")
    print(f"告警统计: {'✓ 正常' if stats_test_ok else '✗ 异常'}")
    
    if lock_test_ok:
        print("\n建议:")
        print("1. 锁屏功能已启用，异常检测达到阈值时会自动锁屏")
        print("2. 可以调整锁屏阈值来改变敏感度")
        print("3. 运行 python start_monitor.py 启动完整系统")
        print("4. 按 pppp 开始预测，观察异常检测和锁屏")
        
        # 询问是否进行手动锁屏测试
        response = input("\n是否进行手动锁屏测试? (y/N): ")
        if response.lower() == 'y':
            test_manual_lock()
    else:
        print("\n建议:")
        print("1. 检查Windows API是否正确安装")
        print("2. 确保有足够的系统权限")
        print("3. 检查防火墙设置")

if __name__ == "__main__":
    main() 
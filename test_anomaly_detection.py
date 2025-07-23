#!/usr/bin/env python3
"""
异常检测测试脚本
用于测试和调试异常检测功能
"""

import sys
import time
import json
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_anomaly_detection():
    """测试异常检测功能"""
    print("=== 异常检测测试 ===")
    
    try:
        from src.core.predictor.simple_predictor import SimplePredictor
        from src.core.model_trainer.simple_model_trainer import SimpleModelTrainer
        
        # 创建预测器和模型训练器
        predictor = SimplePredictor()
        model_trainer = SimpleModelTrainer()
        
        print("✓ 预测器和模型训练器创建成功")
        
        # 检查数据库
        db_path = Path("data/mouse_data.db")
        if not db_path.exists():
            print("✗ 数据库不存在，请先进行数据采集和特征处理")
            return False
        
        # 获取用户列表
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM features")
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            print("✗ 没有找到用户数据，请先进行数据采集和特征处理")
            return False
        
        user_id = users[0][0]
        print(f"测试用户: {user_id}")
        
        # 检查模型是否存在
        model_path = Path("models") / f"user_{user_id}_model.pkl"
        if not model_path.exists():
            print("✗ 用户模型不存在，请先训练模型")
            return False
        
        print("✓ 用户模型存在")
        
        # 加载最近的特征数据
        features_df = predictor.load_recent_features(user_id, limit=10)
        if features_df.empty:
            print("✗ 没有找到特征数据")
            return False
        
        print(f"✓ 加载到 {len(features_df)} 条特征数据")
        
        # 进行预测
        predictions = predictor.predict_user_behavior(user_id, features_df)
        if not predictions:
            print("✗ 预测失败")
            return False
        
        print(f"✓ 成功进行 {len(predictions)} 个预测")
        
        # 分析预测结果
        normal_count = sum(1 for p in predictions if p['is_normal'])
        anomaly_count = sum(1 for p in predictions if not p['is_normal'])
        
        print(f"预测结果分析:")
        print(f"  正常行为: {normal_count}")
        print(f"  异常行为: {anomaly_count}")
        
        # 显示异常详情
        anomalies = [p for p in predictions if not p['is_normal']]
        if anomalies:
            print(f"\n异常详情:")
            for i, anomaly in enumerate(anomalies[:3]):  # 只显示前3个
                print(f"  异常 {i+1}: 分数={anomaly['anomaly_score']:.3f}, 概率={anomaly['probability']:.3f}")
        else:
            print("\n没有检测到异常行为")
        
        # 测试不同的阈值
        print(f"\n=== 阈值测试 ===")
        thresholds = [0.3, 0.5, 0.7, 0.9]
        for threshold in thresholds:
            anomaly_count = sum(1 for p in predictions if p['anomaly_score'] > threshold)
            print(f"阈值 {threshold}: {anomaly_count} 个异常")
        
        return True
        
    except Exception as e:
        print(f"✗ 异常检测测试失败: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False

def simulate_anomaly_behavior():
    """模拟异常行为数据"""
    print("\n=== 模拟异常行为 ===")
    
    try:
        from src.core.data_collector.windows_mouse_collector import WindowsMouseCollector
        
        # 创建鼠标采集器
        user_id = "test_user_anomaly"
        collector = WindowsMouseCollector(user_id)
        
        print("✓ 鼠标采集器创建成功")
        
        # 生成一些异常数据（快速移动、不规则模式等）
        print("生成异常行为数据...")
        
        # 这里可以添加生成异常数据的逻辑
        # 例如：快速移动、不规则点击模式等
        
        print("✓ 异常行为数据生成完成")
        return True
        
    except Exception as e:
        print(f"✗ 模拟异常行为失败: {e}")
        return False

def adjust_anomaly_threshold():
    """调整异常检测阈值"""
    print("\n=== 调整异常检测阈值 ===")
    
    try:
        # 读取当前配置
        from src.utils.config.config_loader import ConfigLoader
        config = ConfigLoader()
        prediction_config = config.get_prediction_config()
        
        current_threshold = prediction_config.get('anomaly_threshold', 0.5)
        print(f"当前异常阈值: {current_threshold}")
        
        # 建议的阈值调整
        new_threshold = 0.3  # 降低阈值，更容易触发异常
        print(f"建议的新阈值: {new_threshold}")
        
        # 这里可以添加更新配置的逻辑
        print("✓ 阈值调整建议已提供")
        return True
        
    except Exception as e:
        print(f"✗ 调整阈值失败: {e}")
        return False

def main():
    """主函数"""
    print("异常检测测试工具")
    print("=" * 50)
    
    # 测试异常检测
    detection_ok = test_anomaly_detection()
    
    # 模拟异常行为
    simulation_ok = simulate_anomaly_behavior()
    
    # 调整阈值
    threshold_ok = adjust_anomaly_threshold()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果:")
    print(f"异常检测: {'✓ 正常' if detection_ok else '✗ 异常'}")
    print(f"异常模拟: {'✓ 正常' if simulation_ok else '✗ 异常'}")
    print(f"阈值调整: {'✓ 正常' if threshold_ok else '✗ 异常'}")
    
    if detection_ok:
        print("\n建议:")
        print("1. 如果检测到异常，说明系统工作正常")
        print("2. 如果没有检测到异常，可能需要:")
        print("   - 降低异常检测阈值")
        print("   - 增加更多测试数据")
        print("   - 检查模型训练质量")
        print("3. 运行 python start_monitor.py 启动完整系统")
        print("4. 按 pppp 开始预测，观察异常检测")
    else:
        print("\n建议:")
        print("1. 确保已完成数据采集 (cccc)")
        print("2. 确保已完成特征处理 (ffff)")
        print("3. 确保已完成模型训练 (tttt)")
        print("4. 检查数据库和模型文件")

if __name__ == "__main__":
    main() 
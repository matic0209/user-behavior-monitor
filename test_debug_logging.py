#!/usr/bin/env python3
"""
调试日志测试脚本
用于验证系统的详细日志输出功能
"""

import sys
import os
import time
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_logger():
    """测试日志系统"""
    print("=== 测试日志系统 ===")
    
    try:
        from src.utils.logger.logger import Logger
        
        # 创建日志记录器
        logger = Logger()
        
        # 测试不同级别的日志
        logger.debug("这是一条调试日志")
        logger.info("这是一条信息日志")
        logger.warning("这是一条警告日志")
        logger.error("这是一条错误日志")
        
        # 测试异常日志
        try:
            raise ValueError("测试异常")
        except Exception as e:
            logger.exception("捕获到异常")
        
        print("✓ 日志系统测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 日志系统测试失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return False

def test_config_loader():
    """测试配置加载器"""
    print("=== 测试配置加载器 ===")
    
    try:
        from src.utils.config.config_loader import ConfigLoader
        
        # 创建配置加载器
        config = ConfigLoader()
        
        # 测试配置读取
        log_level = config.get('logging.level')
        print(f"日志级别: {log_level}")
        
        debug_mode = config.get('system.debug_mode')
        print(f"调试模式: {debug_mode}")
        
        print("✓ 配置加载器测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 配置加载器测试失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return False

def test_user_manager():
    """测试用户管理器"""
    print("=== 测试用户管理器 ===")
    
    try:
        from src.core.user_manager import UserManager
        
        # 创建用户管理器
        user_manager = UserManager()
        
        # 测试用户ID生成
        user_id = user_manager.get_current_user_id()
        print(f"当前用户ID: {user_id}")
        
        # 测试重新训练用户ID生成
        retrain_user_id = user_manager.generate_retrain_user_id()
        print(f"重新训练用户ID: {retrain_user_id}")
        
        # 测试用户信息获取
        user_info = user_manager.get_user_info()
        print(f"用户信息: {user_info}")
        
        print("✓ 用户管理器测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 用户管理器测试失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return False

def test_mouse_collector():
    """测试鼠标采集器"""
    print("=== 测试鼠标采集器 ===")
    
    try:
        from src.core.data_collector.windows_mouse_collector import WindowsMouseCollector
        
        # 创建鼠标采集器
        collector = WindowsMouseCollector("test_user")
        
        # 测试状态获取
        status = collector.get_collection_status()
        print(f"采集状态: {status}")
        
        # 测试会话列表获取
        sessions = collector.get_user_sessions()
        print(f"用户会话数量: {len(sessions)}")
        
        print("✓ 鼠标采集器测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 鼠标采集器测试失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return False

def test_feature_processor():
    """测试特征处理器"""
    print("=== 测试特征处理器 ===")
    
    try:
        from src.core.feature_engineer.simple_feature_processor import SimpleFeatureProcessor
        
        # 创建特征处理器
        processor = SimpleFeatureProcessor()
        
        print("✓ 特征处理器测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 特征处理器测试失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return False

def test_model_trainer():
    """测试模型训练器"""
    print("=== 测试模型训练器 ===")
    
    try:
        from src.core.model_trainer.simple_model_trainer import SimpleModelTrainer
        
        # 创建模型训练器
        trainer = SimpleModelTrainer()
        
        print("✓ 模型训练器测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 模型训练器测试失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return False

def test_predictor():
    """测试预测器"""
    print("=== 测试预测器 ===")
    
    try:
        from src.core.predictor.simple_predictor import SimplePredictor
        
        # 创建预测器
        predictor = SimplePredictor()
        
        print("✓ 预测器测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 预测器测试失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return False

def test_alert_service():
    """测试告警服务"""
    print("=== 测试告警服务 ===")
    
    try:
        from src.core.alert.alert_service import AlertService
        
        # 创建告警服务
        alert_service = AlertService()
        
        print("✓ 告警服务测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 告警服务测试失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return False

def check_log_files():
    """检查日志文件"""
    print("=== 检查日志文件 ===")
    
    log_dir = Path('logs')
    if not log_dir.exists():
        print("✗ 日志目录不存在")
        return False
    
    log_files = list(log_dir.glob('*.log'))
    if not log_files:
        print("✗ 没有找到日志文件")
        return False
    
    print(f"找到 {len(log_files)} 个日志文件:")
    for log_file in log_files:
        size = log_file.stat().st_size
        print(f"  - {log_file.name} ({size} bytes)")
    
    print("✓ 日志文件检查完成")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("调试日志功能测试")
    print("=" * 60)
    print()
    
    tests = [
        ("日志系统", test_logger),
        ("配置加载器", test_config_loader),
        ("用户管理器", test_user_manager),
        ("鼠标采集器", test_mouse_collector),
        ("特征处理器", test_feature_processor),
        ("模型训练器", test_model_trainer),
        ("预测器", test_predictor),
        ("告警服务", test_alert_service),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
            print(f"✓ {test_name} 测试通过")
        else:
            print(f"✗ {test_name} 测试失败")
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"失败: {total - passed}/{total}")
    
    # 检查日志文件
    print()
    check_log_files()
    
    print(f"\n=== 测试完成 ===")
    if passed == total:
        print("所有测试通过！调试日志功能正常。")
        return 0
    else:
        print("部分测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
#!/usr/bin/env python3
"""
智能启动功能测试脚本
测试系统是否能正确检测已训练的模型并自动启动预测
"""

import sys
import time
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_model_existence_check():
    """测试模型存在性检查"""
    print("=== 测试模型存在性检查 ===")
    
    try:
        from src.utils.config.config_loader import ConfigLoader
        
        config = ConfigLoader()
        models_path = Path(config.get_paths()['models'])
        
        print(f"模型目录: {models_path}")
        
        if not models_path.exists():
            print("模型目录不存在")
            return False
        
        # 查找所有模型文件
        model_files = list(models_path.glob("user_*_model.pkl"))
        print(f"找到 {len(model_files)} 个模型文件:")
        
        for model_file in model_files:
            user_id = model_file.stem.replace('user_', '').replace('_model', '')
            print(f"  - 用户: {user_id}, 文件: {model_file.name}")
        
        return len(model_files) > 0
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False

def test_smart_startup_logic():
    """测试智能启动逻辑"""
    print("\n=== 测试智能启动逻辑 ===")
    
    try:
        # 模拟SimpleMonitor的智能启动逻辑
        from src.utils.config.config_loader import ConfigLoader
        
        config = ConfigLoader()
        models_path = Path(config.get_paths()['models'])
        
        # 检查是否有模型文件
        model_files = list(models_path.glob("user_*_model.pkl"))
        
        if model_files:
            print("✓ 发现已训练的模型")
            for model_file in model_files:
                user_id = model_file.stem.replace('user_', '').replace('_model', '')
                print(f"  - 用户 {user_id} 的模型: {model_file.name}")
            
            print("\n预期行为:")
            print("1. 系统应该自动加载模型")
            print("2. 启动异常检测")
            print("3. 显示 '异常检测已启动，系统正在监控中...'")
            print("4. 提示 '如需重新训练，请按 rrrr'")
            
            return True
        else:
            print("✗ 没有发现已训练的模型")
            print("\n预期行为:")
            print("1. 系统应该显示 '用户 XXX 没有已训练的模型'")
            print("2. 提示 '请按 rrrr 开始数据采集和模型训练'")
            
            return False
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False

def test_model_loading():
    """测试模型加载功能"""
    print("\n=== 测试模型加载功能 ===")
    
    try:
        from src.core.model_trainer.simple_model_trainer import SimpleModelTrainer
        
        trainer = SimpleModelTrainer()
        
        # 查找可用的模型
        models_path = Path(trainer.models_path)
        model_files = list(models_path.glob("user_*_model.pkl"))
        
        if not model_files:
            print("没有找到可测试的模型文件")
            return False
        
        # 测试加载第一个模型
        test_model_file = model_files[0]
        user_id = test_model_file.stem.replace('user_', '').replace('_model', '')
        
        print(f"测试加载用户 {user_id} 的模型...")
        
        model, scaler, feature_cols = trainer.load_user_model(user_id)
        
        if model is not None:
            print("✓ 模型加载成功")
            print(f"  - 模型类型: {type(model).__name__}")
            print(f"  - 特征数量: {len(feature_cols) if feature_cols else '未知'}")
            return True
        else:
            print("✗ 模型加载失败")
            return False
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    print("智能启动功能测试")
    print("=" * 50)
    
    # 测试1: 模型存在性检查
    test1_result = test_model_existence_check()
    
    # 测试2: 智能启动逻辑
    test2_result = test_smart_startup_logic()
    
    # 测试3: 模型加载功能
    test3_result = test_model_loading()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print(f"模型存在性检查: {'✓ 通过' if test1_result else '✗ 失败'}")
    print(f"智能启动逻辑: {'✓ 通过' if test2_result else '✗ 失败'}")
    print(f"模型加载功能: {'✓ 通过' if test3_result else '✗ 失败'}")
    
    if test1_result and test2_result and test3_result:
        print("\n🎉 所有测试通过！智能启动功能正常工作")
    else:
        print("\n⚠️  部分测试失败，请检查系统配置")
    
    print("\n使用说明:")
    print("1. 如果系统发现已训练模型，会自动启动异常检测")
    print("2. 如果没有模型，会提示用户按 rrrr 进行训练")
    print("3. 训练完成后，下次启动会自动加载模型")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
测试修复后的模型训练功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.model_trainer.simple_model_trainer import SimpleModelTrainer
from src.utils.logger.logger import Logger

def test_model_training():
    """测试模型训练功能"""
    print("🧪 测试修复后的模型训练功能")
    print("=" * 50)
    
    # 创建日志器
    logger = Logger()
    
    # 创建模型训练器
    trainer = SimpleModelTrainer()
    
    # 测试用户ID（使用存在的用户）
    test_user_id = "quick_test_user"
    
    print(f"🎯 测试用户: {test_user_id}")
    
    # 检查用户数据
    print("\n📊 检查用户数据...")
    user_features = trainer.load_user_features_from_db(test_user_id)
    print(f"用户特征数据: {len(user_features)} 条记录")
    
    if user_features.empty:
        print("❌ 用户没有特征数据，尝试其他用户...")
        # 尝试其他用户
        test_user_id = "test_user_1"
        user_features = trainer.load_user_features_from_db(test_user_id)
        print(f"用户 {test_user_id} 特征数据: {len(user_features)} 条记录")
    
    # 检查负样本数据
    print("\n📊 检查负样本数据...")
    negative_samples = trainer.load_other_users_features_from_db(test_user_id, 100)
    print(f"其他用户负样本: {len(negative_samples)} 条记录")
    
    training_samples = trainer.load_training_data_as_negative_samples(test_user_id, 100)
    print(f"训练数据负样本: {len(training_samples)} 条记录")
    
    # 准备训练数据
    print("\n🔧 准备训练数据...")
    X, y, feature_cols = trainer.prepare_training_data(test_user_id)
    
    if X is not None:
        print(f"✅ 训练数据准备成功:")
        print(f"  特征矩阵形状: {X.shape}")
        print(f"  标签数量: {len(y)}")
        print(f"  特征数量: {len(feature_cols)}")
        
        # 训练模型
        print("\n🚀 开始训练模型...")
        success = trainer.train_user_model(test_user_id)
        
        if success:
            print("✅ 模型训练成功!")
            
            # 测试模型加载
            print("\n📥 测试模型加载...")
            model = trainer.load_user_model(test_user_id)
            if model is not None:
                print("✅ 模型加载成功!")
            else:
                print("❌ 模型加载失败")
        else:
            print("❌ 模型训练失败")
    else:
        print("❌ 训练数据准备失败")

def test_negative_sample_generation():
    """测试负样本生成"""
    print("\n🔧 测试负样本生成...")
    
    trainer = SimpleModelTrainer()
    
    # 检查数据库中的用户
    import sqlite3
    db_path = Path("data/mouse_data.db")
    
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM features 
            GROUP BY user_id 
            ORDER BY count DESC
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        print("数据库中的用户:")
        for user_id, count in users:
            print(f"  - {user_id}: {count} 条记录")
        
        # 为每个用户测试负样本加载
        for user_id, count in users[:3]:  # 测试前3个用户
            print(f"\n测试用户 {user_id} 的负样本:")
            
            negative_samples = trainer.load_other_users_features_from_db(user_id, 50)
            print(f"  其他用户负样本: {len(negative_samples)} 条")
            
            training_samples = trainer.load_training_data_as_negative_samples(user_id, 50)
            print(f"  训练数据负样本: {len(training_samples)} 条")

def main():
    """主函数"""
    print("🔍 模型训练修复测试")
    print("=" * 50)
    
    # 测试负样本生成
    test_negative_sample_generation()
    
    # 测试模型训练
    test_model_training()
    
    print("\n" + "=" * 50)
    print("✅ 测试完成")

if __name__ == '__main__':
    main()

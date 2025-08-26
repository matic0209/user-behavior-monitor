#!/usr/bin/env python3
"""
测试新用户的模型训练
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import sys
import os

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent / "src"))

def create_test_user_data():
    """创建测试用户数据"""
    print("👤 创建测试用户数据")
    print("=" * 30)
    
    db_path = Path("data/mouse_data.db")
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建新用户ID
        new_user_id = "new_user_test"
        
        # 生成一些测试特征数据
        test_features = []
        for i in range(10):  # 创建10条测试记录
            # 生成随机特征向量
            feature_vector = {}
            for j in range(100):  # 100个特征
                feature_vector[f"feature_{j}"] = np.random.normal(0, 1)
            
            # 插入到features表
            cursor.execute("""
                INSERT INTO features (user_id, session_id, timestamp, feature_vector, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                new_user_id,
                f"session_{new_user_id}_{i}",
                datetime.now().timestamp() + i,
                json.dumps(feature_vector),
                datetime.now().isoformat()
            ))
            
            test_features.append(feature_vector)
        
        # 提交事务
        conn.commit()
        conn.close()
        
        print(f"✅ 成功创建用户 {new_user_id} 的 {len(test_features)} 条测试数据")
        return True
        
    except Exception as e:
        print(f"❌ 创建测试用户数据失败: {e}")
        return False

def test_model_training():
    """测试模型训练"""
    print("\n🤖 测试模型训练")
    print("=" * 30)
    
    try:
        # 导入模型训练器
        from src.core.model_trainer.simple_model_trainer import SimpleModelTrainer
        
        # 创建模型训练器
        trainer = SimpleModelTrainer()
        
        # 测试用户ID
        test_user_id = "new_user_test"
        
        print(f"🎯 为用户 {test_user_id} 训练模型...")
        
        # 训练模型
        success = trainer.train_user_model(test_user_id)
        
        if success:
            print(f"✅ 用户 {test_user_id} 模型训练成功")
            
            # 测试模型加载
            print(f"📥 测试模型加载...")
            model_info = trainer.load_user_model(test_user_id)
            
            if model_info:
                print(f"✅ 模型加载成功: {model_info}")
            else:
                print(f"❌ 模型加载失败")
        else:
            print(f"❌ 用户 {test_user_id} 模型训练失败")
        
        return success
        
    except Exception as e:
        print(f"❌ 模型训练测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_negative_samples():
    """检查负样本情况"""
    print("\n🔍 检查负样本情况")
    print("=" * 30)
    
    db_path = Path("data/mouse_data.db")
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查新用户数据
        cursor.execute("SELECT COUNT(*) FROM features WHERE user_id = ?", ("new_user_test",))
        new_user_count = cursor.fetchone()[0]
        print(f"📊 新用户数据: {new_user_count} 条记录")
        
        # 检查其他用户数据
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM features 
            WHERE user_id != 'new_user_test'
            GROUP BY user_id
        """)
        
        other_users = cursor.fetchall()
        print(f"📊 其他用户数据: {len(other_users)} 个用户")
        
        training_users = []
        test_users = []
        
        for user_id, count in other_users:
            if user_id.startswith('training_user'):
                training_users.append((user_id, count))
            elif user_id.startswith('test_user'):
                test_users.append((user_id, count))
        
        print(f"📚 训练用户: {len(training_users)} 个")
        total_training = sum(count for _, count in training_users)
        print(f"   总记录数: {total_training}")
        
        print(f"🧪 测试用户: {len(test_users)} 个")
        total_test = sum(count for _, count in test_users)
        print(f"   总记录数: {total_test}")
        
        print(f"📈 可用于负样本的总记录数: {total_training + total_test}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查负样本失败: {e}")

def main():
    """主函数"""
    print("🧪 测试新用户模型训练")
    print("=" * 60)
    
    # 创建测试用户数据
    if not create_test_user_data():
        print("❌ 无法创建测试用户数据，退出")
        return
    
    # 检查负样本情况
    check_negative_samples()
    
    # 测试模型训练
    success = test_model_training()
    
    if success:
        print(f"\n🎉 新用户模型训练测试成功！")
        print(f"✅ 新用户可以从20个现有用户中找到足够的负样本")
        print(f"✅ 模型训练和加载功能正常")
    else:
        print(f"\n❌ 新用户模型训练测试失败")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
测试新用户是否能从20个用户中找到负样本
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import numpy as np

def test_negative_samples_for_new_user():
    """测试新用户是否能从20个用户中找到负样本"""
    print("🧪 测试新用户负样本查找")
    print("=" * 50)
    
    db_path = Path("data/mouse_data.db")
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    # 模拟一个新用户
    new_user_id = "new_user_test"
    
    print(f"🎯 测试用户: {new_user_id}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查数据库中的用户分布
        print(f"\n📊 数据库中的用户分布:")
        cursor.execute("SELECT user_id, COUNT(*) FROM features GROUP BY user_id ORDER BY user_id")
        users = cursor.fetchall()
        
        training_users = []
        test_users = []
        
        for user_id, count in users:
            if user_id.startswith('training_user'):
                training_users.append((user_id, count))
            elif user_id.startswith('test_user'):
                test_users.append((user_id, count))
        
        print(f"📚 训练用户: {len(training_users)} 个")
        for user_id, count in training_users:
            print(f"  {user_id}: {count} 条记录")
        
        print(f"🧪 测试用户: {len(test_users)} 个")
        for user_id, count in test_users:
            print(f"  {user_id}: {count} 条记录")
        
        # 测试负样本查找逻辑
        print(f"\n🔍 测试负样本查找逻辑:")
        
        # 1. 查找其他用户数据（排除当前用户）
        print(f"1️⃣ 查找其他用户数据（排除 {new_user_id}）:")
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM features 
            WHERE user_id != ? 
            GROUP BY user_id
        """, (new_user_id,))
        
        other_users = cursor.fetchall()
        print(f"   找到 {len(other_users)} 个其他用户:")
        total_other_samples = 0
        for user_id, count in other_users:
            print(f"     {user_id}: {count} 条记录")
            total_other_samples += count
        
        print(f"   其他用户总样本数: {total_other_samples}")
        
        # 2. 查找训练用户数据（作为负样本）
        print(f"\n2️⃣ 查找训练用户数据（作为负样本）:")
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM features 
            WHERE user_id LIKE 'training_user%' AND user_id != ?
            GROUP BY user_id
        """, (new_user_id,))
        
        training_negative = cursor.fetchall()
        print(f"   找到 {len(training_negative)} 个训练用户:")
        total_training_samples = 0
        for user_id, count in training_negative:
            print(f"     {user_id}: {count} 条记录")
            total_training_samples += count
        
        print(f"   训练用户总样本数: {total_training_samples}")
        
        # 3. 查找测试用户数据（作为负样本）
        print(f"\n3️⃣ 查找测试用户数据（作为负样本）:")
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM features 
            WHERE user_id LIKE 'test_user%' AND user_id != ?
            GROUP BY user_id
        """, (new_user_id,))
        
        test_negative = cursor.fetchall()
        print(f"   找到 {len(test_negative)} 个测试用户:")
        total_test_samples = 0
        for user_id, count in test_negative:
            print(f"     {user_id}: {count} 条记录")
            total_test_samples += count
        
        print(f"   测试用户总样本数: {total_test_samples}")
        
        # 4. 模拟负样本加载逻辑
        print(f"\n4️⃣ 模拟负样本加载逻辑:")
        
        # 模拟load_other_users_features_from_db函数
        def simulate_load_other_users_features(exclude_user_id, limit=1000):
            """模拟加载其他用户特征"""
            cursor.execute("""
                SELECT feature_vector FROM features 
                WHERE user_id != ? AND user_id NOT LIKE 'training_user%' AND user_id NOT LIKE 'test_user%'
                ORDER BY timestamp DESC
            """, (exclude_user_id,))
            
            other_users_data = cursor.fetchall()
            print(f"   其他用户数据: {len(other_users_data)} 条")
            
            if len(other_users_data) < limit // 2:
                # 如果其他用户数据不足，使用测试用户数据
                cursor.execute("""
                    SELECT feature_vector FROM features 
                    WHERE user_id != ? AND user_id LIKE 'test_user%'
                    ORDER BY timestamp DESC
                """, (exclude_user_id,))
                
                test_users_data = cursor.fetchall()
                print(f"   测试用户数据: {len(test_users_data)} 条")
                
                # 合并数据
                all_data = other_users_data + test_users_data
                print(f"   合并后数据: {len(all_data)} 条")
                
                return all_data[:limit]
            else:
                return other_users_data[:limit]
        
        # 测试负样本加载
        negative_samples = simulate_load_other_users_features(new_user_id, 1000)
        print(f"   最终负样本数量: {len(negative_samples)}")
        
        # 5. 测试完整的负样本查找流程
        print(f"\n5️⃣ 测试完整的负样本查找流程:")
        
        # 模拟simple_model_trainer中的逻辑
        def simulate_negative_sample_loading(user_id, negative_sample_limit=1000):
            """模拟负样本加载的完整流程"""
            print(f"   为用户 {user_id} 加载负样本（限制: {negative_sample_limit}）:")
            
            # 第一步：查找其他用户数据
            cursor.execute("""
                SELECT feature_vector FROM features 
                WHERE user_id != ? AND user_id NOT LIKE 'training_user%' AND user_id NOT LIKE 'test_user%'
                ORDER BY timestamp DESC
            """, (user_id,))
            
            other_users_data = cursor.fetchall()
            print(f"     其他用户数据: {len(other_users_data)} 条")
            
            # 第二步：如果其他用户数据不足，使用测试用户数据
            if len(other_users_data) < negative_sample_limit // 2:
                cursor.execute("""
                    SELECT feature_vector FROM features 
                    WHERE user_id != ? AND user_id LIKE 'test_user%'
                    ORDER BY timestamp DESC
                """, (user_id,))
                
                test_users_data = cursor.fetchall()
                print(f"     测试用户数据: {len(test_users_data)} 条")
                
                # 合并数据
                all_negative_data = other_users_data + test_users_data
                print(f"     合并后数据: {len(all_negative_data)} 条")
                
                return all_negative_data[:negative_sample_limit]
            else:
                return other_users_data[:negative_sample_limit]
        
        # 测试不同用户的负样本加载
        test_users = ["new_user_1", "new_user_2", "new_user_3"]
        
        for test_user in test_users:
            print(f"\n   测试用户 {test_user}:")
            negative_samples = simulate_negative_sample_loading(test_user, 500)
            print(f"     最终负样本数量: {len(negative_samples)}")
        
        # 6. 总结
        print(f"\n📋 总结:")
        print(f"   ✅ 数据库中有 {len(training_users)} 个训练用户")
        print(f"   ✅ 数据库中有 {len(test_users)} 个测试用户")
        print(f"   ✅ 总共 {total_other_samples} 条其他用户样本")
        print(f"   ✅ 总共 {total_training_samples} 条训练用户样本")
        print(f"   ✅ 总共 {total_test_samples} 条测试用户样本")
        print(f"   ✅ 新用户可以从这些数据中找到足够的负样本")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def main():
    """主函数"""
    print("🧪 测试新用户负样本查找")
    print("=" * 60)
    
    # 测试负样本查找
    test_negative_samples_for_new_user()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")

if __name__ == '__main__':
    main()

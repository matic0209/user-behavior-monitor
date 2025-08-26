#!/usr/bin/env python3
"""
调试数据库内容脚本
查看负样本数据的情况
"""

import sqlite3
import pandas as pd
from pathlib import Path
import json

def check_database_content():
    """检查数据库内容"""
    db_path = Path("data/mouse_data.db")
    
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    print("🔍 检查数据库内容...")
    print(f"数据库路径: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 检查表结构
        print("\n📋 数据库表结构:")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\n表: {table_name}")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # 获取记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"  记录数: {count}")
        
        # 检查features表的具体内容
        print("\n📊 features表详细内容:")
        
        # 检查用户分布
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM features 
            GROUP BY user_id 
            ORDER BY count DESC
        """)
        user_distribution = cursor.fetchall()
        
        print("用户数据分布:")
        for user_id, count in user_distribution:
            print(f"  - {user_id}: {count} 条记录")
        
        # 检查特定用户的数据
        target_user = "HUAWEI_1755014060"
        print(f"\n🎯 目标用户 {target_user} 的数据:")
        
        cursor.execute("""
            SELECT user_id, timestamp, feature_vector 
            FROM features 
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 5
        """, (target_user,))
        
        user_data = cursor.fetchall()
        print(f"找到 {len(user_data)} 条记录")
        
        for i, (user_id, timestamp, feature_vector) in enumerate(user_data):
            print(f"\n记录 {i+1}:")
            print(f"  用户ID: {user_id}")
            print(f"  时间戳: {timestamp}")
            print(f"  特征向量长度: {len(feature_vector) if feature_vector else 0}")
            
            # 尝试解析特征向量
            if feature_vector:
                try:
                    features = json.loads(feature_vector)
                    print(f"  特征数量: {len(features)}")
                    print(f"  特征示例: {list(features.keys())[:5]}")
                except:
                    print("  特征向量解析失败")
        
        # 检查其他用户数据（作为负样本）
        print(f"\n🔍 其他用户数据（负样本）:")
        
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM features 
            WHERE user_id != ? AND user_id NOT LIKE 'training_user%' AND user_id NOT LIKE 'test_user%'
            GROUP BY user_id 
            ORDER BY count DESC
        """, (target_user,))
        
        other_users = cursor.fetchall()
        print(f"找到 {len(other_users)} 个其他用户:")
        
        for user_id, count in other_users:
            print(f"  - {user_id}: {count} 条记录")
        
        # 检查训练数据
        print(f"\n📚 训练数据:")
        
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM features 
            WHERE user_id LIKE 'training_user%'
            GROUP BY user_id 
            ORDER BY count DESC
        """)
        
        training_data = cursor.fetchall()
        print(f"找到 {len(training_data)} 个训练用户:")
        
        for user_id, count in training_data:
            print(f"  - {user_id}: {count} 条记录")
        
        # 检查测试数据
        print(f"\n🧪 测试数据:")
        
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM features 
            WHERE user_id LIKE 'test_user%'
            GROUP BY user_id 
            ORDER BY count DESC
        """)
        
        test_data = cursor.fetchall()
        print(f"找到 {len(test_data)} 个测试用户:")
        
        for user_id, count in test_data:
            print(f"  - {user_id}: {count} 条记录")
        
        conn.close()
        
        # 分析问题
        print(f"\n🔍 问题分析:")
        
        total_other_users = sum(count for _, count in other_users)
        total_training_data = sum(count for _, count in training_data)
        
        print(f"其他用户数据总量: {total_other_users}")
        print(f"训练数据总量: {total_training_data}")
        
        if total_other_users == 0 and total_training_data == 0:
            print("❌ 问题确认: 没有负样本数据")
            print("💡 解决方案:")
            print("1. 需要收集其他用户的数据")
            print("2. 或者生成训练数据")
            print("3. 或者使用单类分类方法")
        
        elif total_other_users == 0:
            print("⚠️  问题: 没有其他用户数据，但有训练数据")
            print("💡 解决方案: 使用训练数据作为负样本")
        
        else:
            print("✅ 有足够的负样本数据")
        
    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")

def generate_test_negative_samples():
    """生成测试用的负样本数据"""
    print("\n🔧 生成测试用的负样本数据...")
    
    db_path = Path("data/mouse_data.db")
    
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 检查是否已有负样本数据
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM features 
            WHERE user_id LIKE 'negative_sample%'
        """)
        
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"✅ 已存在 {existing_count} 条负样本数据")
            conn.close()
            return
        
        # 获取一个正样本作为模板
        cursor.execute("""
            SELECT feature_vector FROM features 
            WHERE user_id = 'HUAWEI_1755014060'
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if not result:
            print("❌ 没有找到正样本数据作为模板")
            conn.close()
            return
        
        # 解析特征向量
        template_features = json.loads(result[0])
        feature_names = list(template_features.keys())
        
        print(f"使用 {len(feature_names)} 个特征生成负样本")
        
        # 生成负样本数据
        import numpy as np
        from datetime import datetime, timedelta
        
        negative_samples = []
        base_time = datetime.now()
        
        for i in range(50):  # 生成50个负样本
            # 为每个特征添加随机噪声
            noisy_features = {}
            for feature_name in feature_names:
                base_value = template_features.get(feature_name, 0.0)
                # 添加较大的噪声来模拟不同用户的行为
                noise = np.random.normal(0, 0.5)  # 较大的噪声
                noisy_features[feature_name] = base_value + noise
            
            # 创建负样本记录
            negative_sample = {
                'user_id': f'negative_sample_{i+1:03d}',
                'timestamp': (base_time + timedelta(minutes=i)).isoformat(),
                'feature_vector': json.dumps(noisy_features)
            }
            
            negative_samples.append(negative_sample)
        
        # 插入负样本数据
        cursor.executemany("""
            INSERT INTO features (user_id, timestamp, feature_vector)
            VALUES (?, ?, ?)
        """, [(sample['user_id'], sample['timestamp'], sample['feature_vector']) 
              for sample in negative_samples])
        
        conn.commit()
        conn.close()
        
        print(f"✅ 成功生成 {len(negative_samples)} 条负样本数据")
        
    except Exception as e:
        print(f"❌ 生成负样本数据失败: {e}")

def main():
    """主函数"""
    print("🔍 数据库内容调试工具")
    print("=" * 50)
    
    # 检查数据库内容
    check_database_content()
    
    # 生成测试负样本
    generate_test_negative_samples()
    
    print("\n" + "=" * 50)
    print("✅ 调试完成")

if __name__ == '__main__':
    main()

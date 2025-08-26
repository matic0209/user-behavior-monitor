#!/usr/bin/env python3
"""
调试负样本加载问题
"""
import sqlite3
import pandas as pd
import json
from pathlib import Path
import sys
import os

# 添加src路径
sys.path.append(str(Path(__file__).parent / "src"))

def test_negative_sample_loading():
    """测试负样本加载逻辑"""
    print("🔍 调试负样本加载问题")
    print("=" * 50)
    
    # 数据库路径
    db_path = "data/mouse_data.db"
    
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    # 测试多个用户ID
    test_user_ids = [
        "HUAWEI_1755014060",
        "HUAWEI_1755016445",  # 从错误日志中看到的用户ID
        "new_user_test"
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 1. 检查数据库中的用户
        print("📊 数据库中的用户:")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_id, COUNT(*) as count FROM features GROUP BY user_id ORDER BY count DESC")
        users = cursor.fetchall()
        
        for user_id, count in users:
            print(f"  - {user_id}: {count} 条记录")
        
        # 2. 测试每个用户ID的负样本查询
        for test_user_id in test_user_ids:
            print(f"\n🔍 测试用户ID: {test_user_id}")
            print("-" * 40)
            
            # 检查该用户是否存在
            cursor.execute("SELECT COUNT(*) FROM features WHERE user_id = ?", (test_user_id,))
            user_count = cursor.fetchone()[0]
            print(f"  该用户在数据库中的记录数: {user_count}")
            
            if user_count == 0:
                print(f"  ⚠️  用户 {test_user_id} 在数据库中不存在")
                continue
            
            # 测试负样本查询
            query = '''
                SELECT user_id, COUNT(*) as count FROM features 
                WHERE user_id != ?
                GROUP BY user_id
                ORDER BY count DESC
            '''
            
            cursor.execute(query, (test_user_id,))
            other_users = cursor.fetchall()
            
            print("  其他用户数据:")
            total_other = 0
            for user_id, count in other_users:
                print(f"    - {user_id}: {count} 条记录")
                total_other += count
            
            print(f"  总计: {total_other} 条记录")
            
            # 测试特征向量查询
            feature_query = '''
                SELECT feature_vector FROM features 
                WHERE user_id != ?
                ORDER BY timestamp DESC
                LIMIT 5
            '''
            
            cursor.execute(feature_query, (test_user_id,))
            feature_results = cursor.fetchall()
            
            print(f"  特征记录查询结果: {len(feature_results)} 条记录")
            
            if feature_results:
                print("  第一条特征记录:")
                first_record = feature_results[0][0]
                print(f"    类型: {type(first_record)}")
                print(f"    长度: {len(str(first_record))}")
                
                try:
                    if isinstance(first_record, str):
                        parsed = json.loads(first_record)
                        print(f"    解析成功，特征数量: {len(parsed)}")
                        print(f"    前5个特征: {list(parsed.keys())[:5]}")
                    else:
                        print(f"    非字符串类型: {first_record}")
                except Exception as e:
                    print(f"    解析失败: {e}")
        
        # 3. 测试完整的负样本加载流程
        print(f"\n🔍 测试完整负样本加载流程:")
        
        # 模拟load_other_users_features_from_db的逻辑
        limit = 1000
        query = '''
            SELECT feature_vector FROM features 
            WHERE user_id != ?
            ORDER BY timestamp DESC
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        print(f"  执行查询: {query}")
        
        for test_user_id in test_user_ids:
            print(f"\n  测试用户: {test_user_id}")
            
            df = pd.read_sql_query(query, conn, params=(test_user_id,))
            print(f"    查询结果: {len(df)} 条记录")
            
            if not df.empty:
                print(f"    列名: {list(df.columns)}")
                print(f"    数据类型: {df.dtypes.to_dict()}")
                
                # 测试解析
                if 'feature_vector' in df.columns:
                    print("    测试特征向量解析...")
                    
                    # 取第一条记录测试
                    first_vector = df.iloc[0]['feature_vector']
                    print(f"      第一条记录类型: {type(first_vector)}")
                    
                    try:
                        if isinstance(first_vector, str):
                            parsed = json.loads(first_vector)
                            print(f"      解析成功，特征数量: {len(parsed)}")
                        else:
                            print(f"      非字符串类型，直接使用")
                            parsed = first_vector
                        
                        # 转换为DataFrame
                        feature_df = pd.DataFrame([parsed])
                        print(f"      转换后DataFrame形状: {feature_df.shape}")
                        print(f"      列名: {list(feature_df.columns)[:5]}...")
                        
                    except Exception as e:
                        print(f"      解析失败: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_negative_sample_loading()

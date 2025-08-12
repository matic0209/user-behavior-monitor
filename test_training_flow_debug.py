#!/usr/bin/env python3
"""
调试完整训练流程，找出负样本加载失败的原因
"""
import sqlite3
import pandas as pd
import json
from pathlib import Path
import sys
import os
import logging

# 添加src路径
sys.path.append(str(Path(__file__).parent / "src"))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_training_flow():
    """测试完整的训练流程"""
    print("🔍 调试完整训练流程")
    print("=" * 50)
    
    # 数据库路径
    db_path = "data/mouse_data.db"
    
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    # 测试用户ID - 使用实际存在的用户
    test_user_id = "new_user_test"
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 1. 模拟 load_user_features_from_db
        print(f"\n🔍 步骤1: 加载用户 {test_user_id} 的特征数据")
        print("-" * 40)
        
        query = '''
            SELECT feature_vector FROM features 
            WHERE user_id = ?
            ORDER BY timestamp DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(test_user_id,))
        print(f"  查询结果: {len(df)} 条记录")
        
        if df.empty:
            print(f"  ❌ 用户 {test_user_id} 没有特征数据，无法继续训练")
            return
        
        print(f"  列名: {list(df.columns)}")
        print(f"  数据类型: {df.dtypes.to_dict()}")
        
        # 2. 模拟 load_other_users_features_from_db
        print(f"\n🔍 步骤2: 加载其他用户特征数据作为负样本")
        print("-" * 40)
        
        negative_query = '''
            SELECT feature_vector FROM features 
            WHERE user_id != ?
            ORDER BY timestamp DESC
        '''
        
        # 添加限制
        limit = 1000
        if limit:
            negative_query += f' LIMIT {limit}'
        
        print(f"  执行查询: {negative_query}")
        print(f"  参数: {test_user_id}")
        
        negative_df = pd.read_sql_query(negative_query, conn, params=(test_user_id,))
        print(f"  查询结果: {len(negative_df)} 条记录")
        
        if negative_df.empty:
            print(f"  ❌ 没有找到其他用户数据")
            return
        
        print(f"  列名: {list(negative_df.columns)}")
        print(f"  数据类型: {negative_df.dtypes.to_dict()}")
        
        # 3. 模拟 _parse_feature_vectors
        print(f"\n🔍 步骤3: 解析特征向量")
        print("-" * 40)
        
        if 'feature_vector' in negative_df.columns:
            print("  开始解析特征向量...")
            
            feature_vectors = []
            for i, vector_str in enumerate(negative_df['feature_vector']):
                try:
                    if isinstance(vector_str, str):
                        vector_dict = json.loads(vector_str)
                    else:
                        vector_dict = vector_str
                    feature_vectors.append(vector_dict)
                    
                    # 只显示前3条记录的解析结果
                    if i < 3:
                        print(f"    记录 {i+1}: 解析成功，特征数量: {len(vector_dict)}")
                        
                except Exception as e:
                    print(f"    记录 {i+1}: 解析失败: {e}")
                    feature_vectors.append({})
            
            print(f"  成功解析: {len([v for v in feature_vectors if v])} 条记录")
            print(f"  解析失败: {len([v for v in feature_vectors if not v])} 条记录")
            
            # 转换为DataFrame
            if feature_vectors:
                feature_df = pd.DataFrame(feature_vectors)
                print(f"  转换后DataFrame形状: {feature_df.shape}")
                print(f"  列名: {list(feature_df.columns)[:5]}...")
                
                # 合并到原始DataFrame
                final_df = pd.concat([negative_df.drop('feature_vector', axis=1), feature_df], axis=1)
                print(f"  最终DataFrame形状: {final_df.shape}")
                print(f"  最终列数: {len(final_df.columns)}")
                
                return final_df
            else:
                print("  ❌ 所有特征向量解析失败")
                return None
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_with_real_user():
    """使用真实存在的用户测试"""
    print("\n🔍 使用真实用户测试训练流程")
    print("=" * 50)
    
    # 数据库路径
    db_path = "data/mouse_data.db"
    
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 查找有数据的用户
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_id, COUNT(*) as count FROM features GROUP BY user_id ORDER BY count DESC LIMIT 5")
        users = cursor.fetchall()
        
        print("📊 可用的用户:")
        for user_id, count in users:
            print(f"  - {user_id}: {count} 条记录")
        
        # 选择第一个用户进行测试
        if users:
            test_user = users[0][0]
            print(f"\n🎯 选择用户 {test_user} 进行测试")
            
            # 测试负样本加载
            negative_query = '''
                SELECT feature_vector FROM features 
                WHERE user_id != ?
                ORDER BY timestamp DESC
                LIMIT 100
            '''
            
            df = pd.read_sql_query(negative_query, conn, params=(test_user,))
            print(f"  负样本查询结果: {len(df)} 条记录")
            
            if not df.empty:
                print(f"  列名: {list(df.columns)}")
                
                # 测试解析第一条记录
                first_vector = df.iloc[0]['feature_vector']
                print(f"  第一条记录类型: {type(first_vector)}")
                
                try:
                    if isinstance(first_vector, str):
                        parsed = json.loads(first_vector)
                        print(f"  解析成功，特征数量: {len(parsed)}")
                        print(f"  前5个特征: {list(parsed.keys())[:5]}")
                    else:
                        print(f"  非字符串类型，直接使用")
                        parsed = first_vector
                    
                    # 转换为DataFrame
                    feature_df = pd.DataFrame([parsed])
                    print(f"  转换后DataFrame形状: {feature_df.shape}")
                    
                except Exception as e:
                    print(f"  解析失败: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 测试1: 完整训练流程
    result = test_training_flow()
    
    # 测试2: 使用真实用户
    test_with_real_user()
    
    print("\n✅ 调试完成")

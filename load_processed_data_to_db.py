#!/usr/bin/env python3
"""
将处理后的数据文件导入到数据库
"""

import pickle
import pandas as pd
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import numpy as np

def load_processed_data_to_db():
    """将处理后的数据文件导入到数据库"""
    print("📥 将处理后的数据文件导入到数据库")
    print("=" * 50)
    
    processed_dir = Path("data/processed")
    db_path = Path("data/mouse_data.db")
    
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total_imported = 0
    
    # 导入训练数据
    training_file = processed_dir / "all_training_aggregation.pickle"
    if training_file.exists():
        print(f"\n📚 导入训练数据: {training_file}")
        try:
            with open(training_file, 'rb') as f:
                training_data = pickle.load(f)
            
            if isinstance(training_data, pd.DataFrame) and 'user' in training_data.columns:
                imported_count = import_data_to_db(cursor, training_data, "training_user")
                total_imported += imported_count
                print(f"✅ 训练数据导入完成: {imported_count} 条记录")
            else:
                print("❌ 训练数据格式不正确")
                
        except Exception as e:
            print(f"❌ 导入训练数据失败: {e}")
    
    # 导入测试数据
    test_file = processed_dir / "all_test_aggregation.pickle"
    if test_file.exists():
        print(f"\n🧪 导入测试数据: {test_file}")
        try:
            with open(test_file, 'rb') as f:
                test_data = pickle.load(f)
            
            if isinstance(test_data, pd.DataFrame) and 'user' in test_data.columns:
                imported_count = import_data_to_db(cursor, test_data, "test_user")
                total_imported += imported_count
                print(f"✅ 测试数据导入完成: {imported_count} 条记录")
            else:
                print("❌ 测试数据格式不正确")
                
        except Exception as e:
            print(f"❌ 导入测试数据失败: {e}")
    
    # 提交事务
    conn.commit()
    conn.close()
    
    print(f"\n🎉 数据导入完成! 总共导入 {total_imported} 条记录")
    
    # 验证导入结果
    verify_imported_data()

def import_data_to_db(cursor, data_df, user_prefix):
    """将数据导入到数据库"""
    imported_count = 0
    
    # 获取用户列表
    users = data_df['user'].unique()
    print(f"  发现 {len(users)} 个用户: {list(users)}")
    
    for user_id in users:
        # 获取该用户的数据
        user_data = data_df[data_df['user'] == user_id]
        
        # 生成数据库用户ID
        db_user_id = f"{user_prefix}_{user_id}"
        
        print(f"  处理用户 {db_user_id}: {len(user_data)} 条记录")
        
        for idx, row in user_data.iterrows():
            try:
                # 准备特征向量
                feature_cols = [col for col in row.index if col not in ['session', 'user']]
                feature_vector = {}
                
                for col in feature_cols:
                    value = row[col]
                    # 处理NaN值
                    if pd.isna(value):
                        feature_vector[col] = 0.0
                    elif isinstance(value, (int, float)):
                        feature_vector[col] = float(value)
                    else:
                        feature_vector[col] = 0.0
                
                # 生成会话ID
                session_id = f"session_{user_id}_{idx}"
                
                # 生成时间戳
                timestamp = datetime.now().timestamp() + idx
                
                # 插入到features表
                cursor.execute("""
                    INSERT INTO features (user_id, session_id, timestamp, feature_vector, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    db_user_id,
                    session_id,
                    timestamp,
                    json.dumps(feature_vector),
                    datetime.now().isoformat()
                ))
                
                imported_count += 1
                
            except Exception as e:
                print(f"    ⚠️  导入记录失败: {e}")
                continue
    
    return imported_count

def verify_imported_data():
    """验证导入的数据"""
    print(f"\n🔍 验证导入的数据")
    print("=" * 30)
    
    db_path = Path("data/mouse_data.db")
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查features表中的用户分布
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM features 
            GROUP BY user_id 
            ORDER BY count DESC
        """)
        
        users = cursor.fetchall()
        print(f"数据库中的用户: {len(users)} 个")
        
        training_users = []
        test_users = []
        other_users = []
        
        for user_id, count in users:
            if user_id.startswith('training_user'):
                training_users.append((user_id, count))
            elif user_id.startswith('test_user'):
                test_users.append((user_id, count))
            else:
                other_users.append((user_id, count))
        
        print(f"\n📚 训练用户: {len(training_users)} 个")
        for user_id, count in training_users:
            print(f"  {user_id}: {count} 条记录")
        
        print(f"\n🧪 测试用户: {len(test_users)} 个")
        for user_id, count in test_users:
            print(f"  {user_id}: {count} 条记录")
        
        print(f"\n📊 其他用户: {len(other_users)} 个")
        for user_id, count in other_users:
            print(f"  {user_id}: {count} 条记录")
        
        # 统计总记录数
        cursor.execute("SELECT COUNT(*) FROM features")
        total_count = cursor.fetchone()[0]
        print(f"\n📈 总记录数: {total_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 验证数据失败: {e}")

def main():
    """主函数"""
    print("📥 数据导入工具")
    print("=" * 60)
    
    # 导入数据
    load_processed_data_to_db()
    
    print("\n" + "=" * 60)
    print("✅ 数据导入完成")

if __name__ == '__main__':
    main()

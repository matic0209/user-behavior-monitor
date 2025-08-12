#!/usr/bin/env python3
"""
全面的用户数据检查脚本
检查data文件夹下的原始数据和数据库中的数据情况
"""

import sqlite3
import pandas as pd
from pathlib import Path
import json
import pickle
import os

def check_raw_data():
    """检查原始数据文件夹"""
    print("📁 检查原始数据文件夹...")
    
    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    # 检查训练数据
    training_dir = raw_dir / "training"
    if training_dir.exists():
        training_users = [d.name for d in training_dir.iterdir() if d.is_dir()]
        print(f"📚 训练数据用户: {len(training_users)} 个")
        print(f"  用户列表: {training_users}")
        
        # 统计每个用户的文件数量
        for user in training_users[:5]:  # 只显示前5个用户
            user_dir = training_dir / user
            files = list(user_dir.glob("*.csv"))
            print(f"    {user}: {len(files)} 个CSV文件")
    else:
        print("❌ 训练数据目录不存在")
    
    # 检查测试数据
    test_dir = raw_dir / "test"
    if test_dir.exists():
        test_users = [d.name for d in test_dir.iterdir() if d.is_dir()]
        print(f"🧪 测试数据用户: {len(test_users)} 个")
        print(f"  用户列表: {test_users}")
        
        # 统计每个用户的文件数量
        for user in test_users[:5]:  # 只显示前5个用户
            user_dir = test_dir / user
            files = list(user_dir.glob("*.csv"))
            print(f"    {user}: {len(files)} 个CSV文件")
    else:
        print("❌ 测试数据目录不存在")
    
    # 检查处理后的数据
    print(f"\n📦 处理后的数据文件:")
    if (processed_dir / "all_training_aggregation.pickle").exists():
        print("  ✅ all_training_aggregation.pickle 存在")
    else:
        print("  ❌ all_training_aggregation.pickle 不存在")
    
    if (processed_dir / "all_test_aggregation.pickle").exists():
        print("  ✅ all_test_aggregation.pickle 存在")
    else:
        print("  ❌ all_test_aggregation.pickle 不存在")

def check_processed_data():
    """检查处理后的数据"""
    print("\n📊 检查处理后的数据...")
    
    processed_dir = Path("data/processed")
    
    # 检查训练数据
    training_file = processed_dir / "all_training_aggregation.pickle"
    if training_file.exists():
        try:
            with open(training_file, 'rb') as f:
                training_data = pickle.load(f)
            
            if isinstance(training_data, dict):
                print(f"📚 训练数据字典键: {list(training_data.keys())}")
                for key, value in training_data.items():
                    if isinstance(value, pd.DataFrame):
                        print(f"  {key}: DataFrame, 形状 {value.shape}")
                        if 'user_id' in value.columns:
                            users = value['user_id'].unique()
                            print(f"    用户: {list(users)}")
                    else:
                        print(f"  {key}: {type(value)}")
            elif isinstance(training_data, pd.DataFrame):
                print(f"📚 训练数据: DataFrame, 形状 {training_data.shape}")
                if 'user_id' in training_data.columns:
                    users = training_data['user_id'].unique()
                    print(f"  用户: {list(users)}")
            else:
                print(f"📚 训练数据: {type(training_data)}")
        except Exception as e:
            print(f"❌ 读取训练数据失败: {e}")
    
    # 检查测试数据
    test_file = processed_dir / "all_test_aggregation.pickle"
    if test_file.exists():
        try:
            with open(test_file, 'rb') as f:
                test_data = pickle.load(f)
            
            if isinstance(test_data, dict):
                print(f"🧪 测试数据字典键: {list(test_data.keys())}")
                for key, value in test_data.items():
                    if isinstance(value, pd.DataFrame):
                        print(f"  {key}: DataFrame, 形状 {value.shape}")
                        if 'user_id' in value.columns:
                            users = value['user_id'].unique()
                            print(f"    用户: {list(users)}")
                    else:
                        print(f"  {key}: {type(value)}")
            elif isinstance(test_data, pd.DataFrame):
                print(f"🧪 测试数据: DataFrame, 形状 {test_data.shape}")
                if 'user_id' in test_data.columns:
                    users = test_data['user_id'].unique()
                    print(f"  用户: {list(users)}")
            else:
                print(f"🧪 测试数据: {type(test_data)}")
        except Exception as e:
            print(f"❌ 读取测试数据失败: {e}")

def check_database_users():
    """检查数据库中的用户数据"""
    print("\n🗄️ 检查数据库中的用户数据...")
    
    db_path = Path("data/mouse_data.db")
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 检查features表中的用户
        print("📊 features表用户分布:")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM features 
            GROUP BY user_id 
            ORDER BY count DESC
        """)
        
        features_users = cursor.fetchall()
        print(f"  总用户数: {len(features_users)}")
        for user_id, count in features_users:
            print(f"    {user_id}: {count} 条记录")
        
        # 检查mouse_events表中的用户
        print("\n📊 mouse_events表用户分布:")
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM mouse_events 
            GROUP BY user_id 
            ORDER BY count DESC
        """)
        
        events_users = cursor.fetchall()
        print(f"  总用户数: {len(events_users)}")
        for user_id, count in events_users:
            print(f"    {user_id}: {count} 条记录")
        
        # 检查predictions表中的用户
        print("\n📊 predictions表用户分布:")
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM predictions 
            GROUP BY user_id 
            ORDER BY count DESC
        """)
        
        predictions_users = cursor.fetchall()
        print(f"  总用户数: {len(predictions_users)}")
        for user_id, count in predictions_users:
            print(f"    {user_id}: {count} 条记录")
        
        # 统计所有用户
        all_users = set()
        for user_id, _ in features_users:
            all_users.add(user_id)
        for user_id, _ in events_users:
            all_users.add(user_id)
        for user_id, _ in predictions_users:
            all_users.add(user_id)
        
        print(f"\n📋 数据库中所有用户: {len(all_users)} 个")
        print(f"  用户列表: {sorted(list(all_users))}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")

def check_data_loading_status():
    """检查数据加载状态"""
    print("\n🔄 检查数据加载状态...")
    
    # 检查是否有数据加载脚本
    data_loading_scripts = [
        "load_training_data.py",
        "load_test_data.py", 
        "load_all_data.py",
        "data_loader.py"
    ]
    
    print("📜 数据加载脚本:")
    for script in data_loading_scripts:
        if Path(script).exists():
            print(f"  ✅ {script} 存在")
        else:
            print(f"  ❌ {script} 不存在")
    
    # 检查是否有数据导入记录
    print("\n📝 检查数据导入记录...")
    
    # 检查数据库中的时间戳
    db_path = Path("data/mouse_data.db")
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查features表的时间范围
            cursor.execute("""
                SELECT MIN(created_at), MAX(created_at), COUNT(*) 
                FROM features
            """)
            min_time, max_time, count = cursor.fetchone()
            print(f"📊 features表:")
            print(f"  记录数: {count}")
            print(f"  时间范围: {min_time} 到 {max_time}")
            
            # 检查mouse_events表的时间范围
            cursor.execute("""
                SELECT MIN(created_at), MAX(created_at), COUNT(*) 
                FROM mouse_events
            """)
            min_time, max_time, count = cursor.fetchone()
            print(f"📊 mouse_events表:")
            print(f"  记录数: {count}")
            print(f"  时间范围: {min_time} 到 {max_time}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ 检查时间戳失败: {e}")

def suggest_data_loading():
    """建议数据加载方案"""
    print("\n💡 数据加载建议:")
    
    # 检查原始数据
    training_users = []
    test_users = []
    
    training_dir = Path("data/raw/training")
    if training_dir.exists():
        training_users = [d.name for d in training_dir.iterdir() if d.is_dir()]
    
    test_dir = Path("data/raw/test")
    if test_dir.exists():
        test_users = [d.name for d in test_dir.iterdir() if d.is_dir()]
    
    print(f"📚 可用的训练用户: {len(training_users)} 个")
    print(f"🧪 可用的测试用户: {len(test_users)} 个")
    
    if training_users or test_users:
        print("\n🔧 建议执行以下步骤:")
        print("1. 运行数据加载脚本将原始数据导入数据库")
        print("2. 或者手动运行特征提取和导入")
        print("3. 确保所有用户数据都被正确加载")
        
        # 创建数据加载脚本建议
        print("\n📜 建议创建数据加载脚本:")
        print("   - load_all_users.py: 加载所有用户数据")
        print("   - load_training_users.py: 加载训练用户数据")
        print("   - load_test_users.py: 加载测试用户数据")
    else:
        print("❌ 没有找到可用的用户数据")

def main():
    """主函数"""
    print("🔍 全面的用户数据检查")
    print("=" * 60)
    
    # 检查原始数据
    check_raw_data()
    
    # 检查处理后的数据
    check_processed_data()
    
    # 检查数据库中的用户
    check_database_users()
    
    # 检查数据加载状态
    check_data_loading_status()
    
    # 建议数据加载方案
    suggest_data_loading()
    
    print("\n" + "=" * 60)
    print("✅ 检查完成")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
检查处理后数据文件中的具体用户信息
"""

import pickle
import pandas as pd
from pathlib import Path

def check_processed_users():
    """检查处理后数据文件中的用户信息"""
    print("🔍 检查处理后数据文件中的用户信息")
    print("=" * 50)
    
    processed_dir = Path("data/processed")
    
    # 检查训练数据
    training_file = processed_dir / "all_training_aggregation.pickle"
    if training_file.exists():
        print(f"\n📚 检查训练数据文件: {training_file}")
        try:
            with open(training_file, 'rb') as f:
                training_data = pickle.load(f)
            
            print(f"数据类型: {type(training_data)}")
            
            if isinstance(training_data, pd.DataFrame):
                print(f"数据形状: {training_data.shape}")
                print(f"列名: {list(training_data.columns)[:10]}...")  # 显示前10列
                
                # 检查用户ID列
                if 'user_id' in training_data.columns:
                    users = training_data['user_id'].unique()
                    print(f"训练数据中的用户: {list(users)}")
                    print(f"用户数量: {len(users)}")
                    
                    # 统计每个用户的记录数
                    user_counts = training_data['user_id'].value_counts()
                    print("每个用户的记录数:")
                    for user, count in user_counts.items():
                        print(f"  {user}: {count} 条记录")
                else:
                    print("❌ 没有找到user_id列")
                    print(f"可用的列: {list(training_data.columns)}")
            else:
                print(f"❌ 数据不是DataFrame，而是 {type(training_data)}")
                
        except Exception as e:
            print(f"❌ 读取训练数据失败: {e}")
    
    # 检查测试数据
    test_file = processed_dir / "all_test_aggregation.pickle"
    if test_file.exists():
        print(f"\n🧪 检查测试数据文件: {test_file}")
        try:
            with open(test_file, 'rb') as f:
                test_data = pickle.load(f)
            
            print(f"数据类型: {type(test_data)}")
            
            if isinstance(test_data, pd.DataFrame):
                print(f"数据形状: {test_data.shape}")
                print(f"列名: {list(test_data.columns)[:10]}...")  # 显示前10列
                
                # 检查用户ID列
                if 'user_id' in test_data.columns:
                    users = test_data['user_id'].unique()
                    print(f"测试数据中的用户: {list(users)}")
                    print(f"用户数量: {len(users)}")
                    
                    # 统计每个用户的记录数
                    user_counts = test_data['user_id'].value_counts()
                    print("每个用户的记录数:")
                    for user, count in user_counts.items():
                        print(f"  {user}: {count} 条记录")
                else:
                    print("❌ 没有找到user_id列")
                    print(f"可用的列: {list(test_data.columns)}")
            else:
                print(f"❌ 数据不是DataFrame，而是 {type(test_data)}")
                
        except Exception as e:
            print(f"❌ 读取测试数据失败: {e}")

def check_raw_user_files():
    """检查原始用户文件夹中的具体文件"""
    print(f"\n📁 检查原始用户文件夹中的具体文件")
    print("=" * 50)
    
    # 检查训练数据文件夹
    training_dir = Path("data/raw/training")
    if training_dir.exists():
        print(f"\n📚 训练数据文件夹: {training_dir}")
        
        for user_dir in training_dir.iterdir():
            if user_dir.is_dir():
                print(f"\n用户: {user_dir.name}")
                
                # 检查所有文件类型
                all_files = list(user_dir.rglob("*"))
                csv_files = list(user_dir.rglob("*.csv"))
                json_files = list(user_dir.rglob("*.json"))
                pickle_files = list(user_dir.rglob("*.pickle"))
                pkl_files = list(user_dir.rglob("*.pkl"))
                
                print(f"  总文件数: {len(all_files)}")
                print(f"  CSV文件: {len(csv_files)}")
                print(f"  JSON文件: {len(json_files)}")
                print(f"  Pickle文件: {len(pickle_files)}")
                print(f"  PKL文件: {len(pkl_files)}")
                
                # 显示前几个文件
                if all_files:
                    print(f"  文件示例:")
                    for file in all_files[:3]:
                        print(f"    {file.name} ({file.stat().st_size} bytes)")
    
    # 检查测试数据文件夹
    test_dir = Path("data/raw/test")
    if test_dir.exists():
        print(f"\n🧪 测试数据文件夹: {test_dir}")
        
        for user_dir in test_dir.iterdir():
            if user_dir.is_dir():
                print(f"\n用户: {user_dir.name}")
                
                # 检查所有文件类型
                all_files = list(user_dir.rglob("*"))
                csv_files = list(user_dir.rglob("*.csv"))
                json_files = list(user_dir.rglob("*.json"))
                pickle_files = list(user_dir.rglob("*.pickle"))
                pkl_files = list(user_dir.rglob("*.pkl"))
                
                print(f"  总文件数: {len(all_files)}")
                print(f"  CSV文件: {len(csv_files)}")
                print(f"  JSON文件: {len(json_files)}")
                print(f"  Pickle文件: {len(pickle_files)}")
                print(f"  PKL文件: {len(pkl_files)}")
                
                # 显示前几个文件
                if all_files:
                    print(f"  文件示例:")
                    for file in all_files[:3]:
                        print(f"    {file.name} ({file.stat().st_size} bytes)")

def main():
    """主函数"""
    print("🔍 检查处理后数据文件中的用户信息")
    print("=" * 60)
    
    # 检查处理后数据文件中的用户
    check_processed_users()
    
    # 检查原始用户文件夹中的文件
    check_raw_user_files()
    
    print("\n" + "=" * 60)
    print("✅ 检查完成")

if __name__ == '__main__':
    main()

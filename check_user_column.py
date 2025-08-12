#!/usr/bin/env python3
"""
检查处理后数据文件中的user列
"""

import pickle
import pandas as pd
from pathlib import Path

def check_user_column():
    """检查处理后数据文件中的user列"""
    print("🔍 检查处理后数据文件中的user列")
    print("=" * 50)
    
    processed_dir = Path("data/processed")
    
    # 检查训练数据
    training_file = processed_dir / "all_training_aggregation.pickle"
    if training_file.exists():
        print(f"\n📚 检查训练数据文件: {training_file}")
        try:
            with open(training_file, 'rb') as f:
                training_data = pickle.load(f)
            
            if isinstance(training_data, pd.DataFrame):
                print(f"数据形状: {training_data.shape}")
                
                # 检查user列
                if 'user' in training_data.columns:
                    users = training_data['user'].unique()
                    print(f"训练数据中的用户: {list(users)}")
                    print(f"用户数量: {len(users)}")
                    
                    # 统计每个用户的记录数
                    user_counts = training_data['user'].value_counts()
                    print("每个用户的记录数:")
                    for user, count in user_counts.items():
                        print(f"  {user}: {count} 条记录")
                else:
                    print("❌ 没有找到user列")
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
            
            if isinstance(test_data, pd.DataFrame):
                print(f"数据形状: {test_data.shape}")
                
                # 检查user列
                if 'user' in test_data.columns:
                    users = test_data['user'].unique()
                    print(f"测试数据中的用户: {list(users)}")
                    print(f"用户数量: {len(users)}")
                    
                    # 统计每个用户的记录数
                    user_counts = test_data['user'].value_counts()
                    print("每个用户的记录数:")
                    for user, count in user_counts.items():
                        print(f"  {user}: {count} 条记录")
                else:
                    print("❌ 没有找到user列")
                    print(f"可用的列: {list(test_data.columns)}")
            else:
                print(f"❌ 数据不是DataFrame，而是 {type(test_data)}")
                
        except Exception as e:
            print(f"❌ 读取测试数据失败: {e}")

def main():
    """主函数"""
    print("🔍 检查处理后数据文件中的user列")
    print("=" * 60)
    
    # 检查user列
    check_user_column()
    
    print("\n" + "=" * 60)
    print("✅ 检查完成")

if __name__ == '__main__':
    main()

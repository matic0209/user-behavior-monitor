#!/usr/bin/env python3
"""
特征处理诊断脚本
用于检查特征处理失败的原因
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_database():
    """检查数据库状态"""
    print("=== 检查数据库状态 ===")
    
    try:
        db_path = Path("data/mouse_data.db")
        if not db_path.exists():
            print("✗ 数据库文件不存在")
            return False
        
        print(f"✓ 数据库文件存在: {db_path}")
        
        # 连接数据库
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"数据库中的表: {[table[0] for table in tables]}")
        
        # 检查mouse_events表
        if ('mouse_events',) in tables:
            cursor.execute("SELECT COUNT(*) FROM mouse_events")
            count = cursor.fetchone()[0]
            print(f"✓ mouse_events表存在，有 {count} 条记录")
            
            # 检查用户数据
            cursor.execute("SELECT DISTINCT user_id FROM mouse_events")
            users = cursor.fetchall()
            print(f"用户列表: {[user[0] for user in users]}")
            
            # 检查会话数据
            cursor.execute("SELECT DISTINCT session_id FROM mouse_events")
            sessions = cursor.fetchall()
            print(f"会话列表: {[session[0] for session in sessions]}")
            
        else:
            print("✗ mouse_events表不存在")
        
        # 检查features表
        if ('features',) in tables:
            cursor.execute("SELECT COUNT(*) FROM features")
            count = cursor.fetchone()[0]
            print(f"✓ features表存在，有 {count} 条记录")
        else:
            print("✗ features表不存在")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 数据库检查失败: {e}")
        return False

def test_feature_processor():
    """测试特征处理器"""
    print("\n=== 测试特征处理器 ===")
    
    try:
        from src.core.feature_engineer.simple_feature_processor import SimpleFeatureProcessor
        
        # 创建特征处理器
        processor = SimpleFeatureProcessor()
        print("✓ 特征处理器创建成功")
        
        # 检查数据库路径
        print(f"数据库路径: {processor.db_path}")
        
        # 获取用户列表
        conn = sqlite3.connect(str(processor.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM mouse_events")
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            print("✗ 没有找到用户数据")
            return False
        
        user_id = users[0][0]
        print(f"测试用户: {user_id}")
        
        # 测试加载数据
        df = processor.load_data_from_db(user_id)
        print(f"加载到 {len(df)} 条鼠标事件数据")
        
        if df.empty:
            print("✗ 没有鼠标事件数据")
            return False
        
        # 测试特征处理
        features_df = processor.process_features(df)
        print(f"处理得到 {len(features_df)} 条特征数据")
        
        if features_df.empty:
            print("✗ 特征处理结果为空")
            return False
        
        print("✓ 特征处理测试成功")
        return True
        
    except Exception as e:
        print(f"✗ 特征处理器测试失败: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False

def test_data_collection():
    """测试数据采集状态"""
    print("\n=== 测试数据采集状态 ===")
    
    try:
        from src.core.data_collector.windows_mouse_collector import WindowsMouseCollector
        
        # 检查是否有用户数据
        db_path = Path("data/mouse_data.db")
        if not db_path.exists():
            print("✗ 数据库不存在，请先进行数据采集")
            return False
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM mouse_events")
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            print("✗ 没有用户数据，请先进行数据采集")
            return False
        
        user_id = users[0][0]
        print(f"找到用户: {user_id}")
        
        # 创建采集器
        collector = WindowsMouseCollector(user_id)
        print("✓ 鼠标采集器创建成功")
        
        # 获取会话数据
        sessions = collector.get_user_sessions()
        print(f"用户会话: {sessions}")
        
        if sessions:
            session_id = sessions[0]['session_id']
            data = collector.get_session_data(session_id)
            print(f"会话 {session_id} 有 {len(data)} 条数据")
            return True
        else:
            print("✗ 没有会话数据")
            return False
        
    except Exception as e:
        print(f"✗ 数据采集状态检查失败: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    print("特征处理诊断工具")
    print("=" * 50)
    
    # 检查数据库
    db_ok = check_database()
    
    # 测试数据采集
    collection_ok = test_data_collection()
    
    # 测试特征处理
    feature_ok = test_feature_processor()
    
    # 总结
    print("\n" + "=" * 50)
    print("诊断结果:")
    print(f"数据库状态: {'✓ 正常' if db_ok else '✗ 异常'}")
    print(f"数据采集: {'✓ 正常' if collection_ok else '✗ 异常'}")
    print(f"特征处理: {'✓ 正常' if feature_ok else '✗ 异常'}")
    
    if not db_ok:
        print("\n建议:")
        print("1. 确保数据库文件存在")
        print("2. 检查数据库权限")
    elif not collection_ok:
        print("\n建议:")
        print("1. 先进行数据采集")
        print("2. 按 cccc 开始采集，ssss 停止采集")
    elif not feature_ok:
        print("\n建议:")
        print("1. 检查数据质量")
        print("2. 确保有足够的鼠标事件数据")
    else:
        print("\n✓ 所有检查通过，特征处理应该可以正常工作")

if __name__ == "__main__":
    main() 
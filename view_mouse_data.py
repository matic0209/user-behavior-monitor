#!/usr/bin/env python3
"""
查看鼠标数据工具
支持查看不同数据库文件中的鼠标事件数据
"""

import sqlite3
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

# 数据库文件路径列表
DB_PATHS = [
    Path('data/mouse_data.db'),  # 统一使用mouse_data.db
    Path('data/mouse_data_sample.db'),  # 样本数据库
]

def check_database_exists(db_path):
    """检查数据库是否存在"""
    if db_path.exists():
        print(f"✓ 数据库存在: {db_path}")
        return True
    else:
        print(f"✗ 数据库不存在: {db_path}")
        return False

def get_table_info(db_path):
    """获取数据库表信息"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        table_info = {}
        for (table_name,) in tables:
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # 获取记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            table_info[table_name] = {
                'columns': [col[1] for col in columns],
                'count': count
            }
        
        conn.close()
        return table_info
        
    except Exception as e:
        print(f"获取数据库 {db_path} 信息失败: {str(e)}")
        return {}

def view_mouse_events(db_path, limit=10):
    """查看鼠标事件数据"""
    try:
        conn = sqlite3.connect(db_path)
        
        # 检查是否有mouse_events表
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mouse_events';")
        if not cursor.fetchone():
            print(f"数据库 {db_path} 中没有mouse_events表")
            conn.close()
            return
        
        # 查询鼠标事件数据
        query = f'''
            SELECT * FROM mouse_events 
            ORDER BY timestamp DESC 
            LIMIT {limit}
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print(f"数据库 {db_path} 中没有鼠标事件数据")
            return
        
        print(f"\n=== 鼠标事件数据 ({db_path}) ===")
        print(f"总记录数: {len(df)}")
        print("\n前10条记录:")
        print(df.to_string(index=False))
        
    except Exception as e:
        print(f"查看鼠标事件数据失败: {str(e)}")

def view_features(db_path, limit=5):
    """查看特征数据"""
    try:
        conn = sqlite3.connect(db_path)
        
        # 检查是否有features表
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='features';")
        if not cursor.fetchone():
            print(f"数据库 {db_path} 中没有features表")
            conn.close()
            return
        
        # 查询特征数据
        query = f'''
            SELECT id, user_id, session_id, timestamp, 
                   substr(feature_vector, 1, 100) || '...' as feature_preview
            FROM features 
            ORDER BY timestamp DESC 
            LIMIT {limit}
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print(f"数据库 {db_path} 中没有特征数据")
            return
        
        print(f"\n=== 特征数据 ({db_path}) ===")
        print(f"总记录数: {len(df)}")
        print("\n前5条记录:")
        print(df.to_string(index=False))
        
    except Exception as e:
        print(f"查看特征数据失败: {str(e)}")

def export_sample_data(db_path, output_file=None):
    """导出样本数据"""
    try:
        conn = sqlite3.connect(db_path)
        
        # 导出mouse_events表
        try:
            df_events = pd.read_sql_query("SELECT * FROM mouse_events LIMIT 100", conn)
            if not df_events.empty:
                events_file = output_file or f"sample_mouse_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df_events.to_csv(events_file, index=False)
                print(f"✓ 鼠标事件数据已导出到: {events_file}")
        except Exception as e:
            print(f"导出鼠标事件数据失败: {str(e)}")
        
        # 导出features表
        try:
            df_features = pd.read_sql_query("SELECT * FROM features LIMIT 50", conn)
            if not df_features.empty:
                features_file = output_file or f"sample_features_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df_features.to_csv(features_file, index=False)
                print(f"✓ 特征数据已导出到: {features_file}")
        except Exception as e:
            print(f"导出特征数据失败: {str(e)}")
        
        conn.close()
        
    except Exception as e:
        print(f"导出样本数据失败: {str(e)}")

def main():
    print("=== 鼠标数据查看工具 ===")
    print()
    
    # 检查数据库文件
    available_dbs = []
    for db_path in DB_PATHS:
        if check_database_exists(db_path):
            available_dbs.append(db_path)
    
    if not available_dbs:
        print("\n没有找到可用的数据库文件")
        print("请确保以下文件之一存在:")
        for db_path in DB_PATHS:
            print(f"  - {db_path}")
        return
    
    print(f"\n找到 {len(available_dbs)} 个可用数据库")
    
    # 显示每个数据库的信息
    for db_path in available_dbs:
        print(f"\n--- 数据库: {db_path} ---")
        table_info = get_table_info(db_path)
        
        if not table_info:
            print("无法获取表信息")
            continue
        
        for table_name, info in table_info.items():
            print(f"表: {table_name}")
            print(f"  列: {', '.join(info['columns'])}")
            print(f"  记录数: {info['count']}")
            
            # 查看具体数据
            if table_name == 'mouse_events':
                view_mouse_events(db_path, limit=5)
            elif table_name == 'features':
                view_features(db_path, limit=3)
    
    # 导出样本数据
    print("\n=== 导出样本数据 ===")
    for db_path in available_dbs:
        print(f"\n导出 {db_path} 的样本数据...")
        export_sample_data(db_path)
    
    print("\n=== 工具使用完成 ===")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
检查mouse_data.db的数据库结构
"""

import sqlite3
from pathlib import Path

DB_PATH = Path('data/mouse_data.db')

def check_db_structure():
    """检查数据库结构"""
    print(f"检查数据库: {DB_PATH}")
    
    if not DB_PATH.exists():
        print("数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"数据库中的表: {[table[0] for table in tables]}")
        
        # 检查每个表的结构
        for table in tables:
            table_name = table[0]
            print(f"\n表: {table_name}")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("  列结构:")
            for col in columns:
                print(f"    {col[1]} ({col[2]})")
            
            # 获取记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  记录数: {count}")
            
            # 显示前3条记录
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_records = cursor.fetchall()
                print("  前3条记录:")
                for record in sample_records:
                    print(f"    {record}")
        
        conn.close()
        
    except Exception as e:
        print(f"检查失败: {str(e)}")

if __name__ == "__main__":
    check_db_structure() 
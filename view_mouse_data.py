#!/usr/bin/env python3
"""
查看鼠标数据存储位置和内容
"""

import sqlite3
import pandas as pd
from pathlib import Path
import os

def check_data_locations():
    """检查数据存储位置"""
    print("=== 鼠标数据存储位置检查 ===")
    
    # 检查数据库文件
    db_paths = [
        Path('data/user_behavior.db'),
        Path('data/mouse_data.db'),
        Path('data/raw/user_behavior.db'),
        Path('data/processed/user_behavior.db')
    ]
    
    print("\n1. 数据库文件位置:")
    for db_path in db_paths:
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(f"   ✓ {db_path} ({size_mb:.2f} MB)")
        else:
            print(f"   ✗ {db_path} (不存在)")
    
    # 检查数据目录
    print("\n2. 数据目录结构:")
    data_dirs = ['data', 'data/raw', 'data/processed', 'logs']
    for dir_path in data_dirs:
        if Path(dir_path).exists():
            files = list(Path(dir_path).glob('*'))
            print(f"   {dir_path}/ ({len(files)} 个文件)")
            for file in files[:5]:  # 只显示前5个文件
                if file.is_file():
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"     - {file.name} ({size_mb:.2f} MB)")
                else:
                    print(f"     - {file.name}/ (目录)")
            if len(files) > 5:
                print(f"     ... 还有 {len(files) - 5} 个文件")
        else:
            print(f"   ✗ {dir_path}/ (不存在)")

def view_database_content(db_path):
    """查看数据库内容"""
    print(f"\n=== 数据库内容: {db_path} ===")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"数据库中的表: {[table[0] for table in tables]}")
        
        # 检查鼠标事件表
        if ('mouse_events',) in tables:
            print("\n鼠标事件表 (mouse_events):")
            
            # 获取表结构
            cursor.execute("PRAGMA table_info(mouse_events);")
            columns = cursor.fetchall()
            print("  表结构:")
            for col in columns:
                print(f"    {col[1]} ({col[2]})")
            
            # 获取记录数
            cursor.execute("SELECT COUNT(*) FROM mouse_events;")
            count = cursor.fetchone()[0]
            print(f"  总记录数: {count}")
            
            # 获取用户列表
            cursor.execute("SELECT DISTINCT user_id FROM mouse_events LIMIT 10;")
            users = cursor.fetchall()
            print(f"  用户列表 (前10个): {[user[0] for user in users]}")
            
            # 获取会话列表
            cursor.execute("SELECT DISTINCT session_id FROM mouse_events LIMIT 10;")
            sessions = cursor.fetchall()
            print(f"  会话列表 (前10个): {[session[0] for session in sessions]}")
            
            # 获取最新记录
            cursor.execute("""
                SELECT user_id, session_id, timestamp, x, y, event_type, button 
                FROM mouse_events 
                ORDER BY timestamp DESC 
                LIMIT 5;
            """)
            recent_records = cursor.fetchall()
            
            print("\n  最新5条记录:")
            for record in recent_records:
                print(f"    用户: {record[0]}, 会话: {record[1][:8]}..., "
                      f"时间: {record[2]:.2f}, 坐标: ({record[3]}, {record[4]}), "
                      f"事件: {record[5]}, 按钮: {record[6]}")
            
            # 获取统计信息
            cursor.execute("""
                SELECT 
                    MIN(timestamp) as start_time,
                    MAX(timestamp) as end_time,
                    COUNT(DISTINCT user_id) as user_count,
                    COUNT(DISTINCT session_id) as session_count
                FROM mouse_events;
            """)
            stats = cursor.fetchone()
            
            print(f"\n  统计信息:")
            print(f"    时间范围: {stats[0]:.2f} - {stats[1]:.2f}")
            print(f"    用户数量: {stats[2]}")
            print(f"    会话数量: {stats[3]}")
            
        else:
            print("  没有找到mouse_events表")
        
        conn.close()
        
    except Exception as e:
        print(f"  查看数据库失败: {e}")

def export_sample_data(db_path, output_file='sample_mouse_data.csv'):
    """导出样本数据到CSV"""
    print(f"\n=== 导出样本数据 ===")
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 查询样本数据
        query = """
            SELECT user_id, session_id, timestamp, x, y, event_type, button, wheel_delta
            FROM mouse_events 
            ORDER BY timestamp DESC 
            LIMIT 1000;
        """
        
        df = pd.read_sql_query(query, conn)
        
        # 保存到CSV
        df.to_csv(output_file, index=False)
        
        print(f"  导出 {len(df)} 条记录到 {output_file}")
        print(f"  文件大小: {Path(output_file).stat().st_size / 1024:.2f} KB")
        
        # 显示前几行
        print("\n  前5行数据:")
        print(df.head().to_string())
        
        conn.close()
        
    except Exception as e:
        print(f"  导出数据失败: {e}")

def main():
    """主函数"""
    print("鼠标数据查看工具")
    print("=" * 50)
    
    # 检查数据位置
    check_data_locations()
    
    # 查看数据库内容
    db_files = ['data/user_behavior.db', 'data/mouse_data.db']
    
    for db_file in db_files:
        if Path(db_file).exists():
            view_database_content(db_file)
            
            # 导出样本数据
            export_sample_data(db_file, f'sample_data_{Path(db_file).stem}.csv')
            break
    else:
        print("\n没有找到鼠标数据数据库文件")
        print("请先运行数据采集: python start_monitor.py")

if __name__ == "__main__":
    main() 
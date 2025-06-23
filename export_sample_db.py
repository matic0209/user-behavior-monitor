#!/usr/bin/env python3
"""
从现有的mouse_data.db中随机抽样1000条特征数据，导出到mouse_data_sample.db
保持数据结构和分布一致，便于跨机测试和演示
"""

import sqlite3
import random
from pathlib import Path

SOURCE_DB = Path('data/mouse_data.db')
SAMPLE_DB = Path('data/mouse_data_sample.db')

def export_sample_data(sample_size=1000):
    """从源数据库导出样本数据"""
    print(f"从 {SOURCE_DB} 导出 {sample_size} 条样本数据...")
    
    if not SOURCE_DB.exists():
        print(f"错误: 源数据库 {SOURCE_DB} 不存在")
        return False
    
    try:
        # 连接源数据库
        source_conn = sqlite3.connect(SOURCE_DB)
        source_cursor = source_conn.cursor()
        
        # 获取总记录数
        source_cursor.execute("SELECT COUNT(*) FROM features")
        total_records = source_cursor.fetchone()[0]
        
        if total_records == 0:
            print("源数据库中没有数据")
            return False
        
        print(f"源数据库共有 {total_records} 条特征记录")
        
        # 随机选择记录ID
        if total_records <= sample_size:
            # 如果总记录数少于样本大小，全部导出
            selected_ids = list(range(1, total_records + 1))
            print(f"记录数不足，导出全部 {total_records} 条记录")
        else:
            # 随机选择样本大小的记录ID
            selected_ids = random.sample(range(1, total_records + 1), sample_size)
            print(f"随机选择 {sample_size} 条记录")
        
        # 查询选中的记录
        placeholders = ','.join(['?' for _ in selected_ids])
        query = f"SELECT * FROM features WHERE id IN ({placeholders}) ORDER BY id"
        source_cursor.execute(query, selected_ids)
        sample_data = source_cursor.fetchall()
        
        # 获取表结构
        source_cursor.execute("PRAGMA table_info(features)")
        columns = source_cursor.fetchall()
        
        # 创建目标数据库
        sample_conn = sqlite3.connect(SAMPLE_DB)
        sample_cursor = sample_conn.cursor()
        
        # 创建表结构
        sample_cursor.execute("""
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                feature_vector TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        sample_cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_session ON features(user_id, session_id)')
        sample_cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON features(timestamp)')
        
        # 插入样本数据
        for row in sample_data:
            # 跳过id列（让SQLite自动生成新的id）
            sample_cursor.execute("""
                INSERT INTO features 
                (user_id, session_id, timestamp, feature_vector, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, row[1:])  # 从第2列开始，跳过id
        
        sample_conn.commit()
        
        # 验证导出结果
        sample_cursor.execute("SELECT COUNT(*) FROM features")
        exported_count = sample_cursor.fetchone()[0]
        
        # 获取一些统计信息
        sample_cursor.execute("SELECT DISTINCT user_id FROM features")
        user_count = len(sample_cursor.fetchall())
        
        sample_cursor.execute("SELECT DISTINCT session_id FROM features")
        session_count = len(sample_cursor.fetchall())
        
        # 关闭连接
        source_conn.close()
        sample_conn.close()
        
        # 显示结果
        print(f"✓ 成功导出 {exported_count} 条记录到 {SAMPLE_DB}")
        print(f"  包含 {user_count} 个用户")
        print(f"  包含 {session_count} 个会话")
        print(f"  文件大小: {SAMPLE_DB.stat().st_size / 1024:.2f} KB")
        
        return True
        
    except Exception as e:
        print(f"导出失败: {str(e)}")
        return False

def verify_sample_db():
    """验证样本数据库"""
    print(f"\n验证样本数据库 {SAMPLE_DB}...")
    
    try:
        conn = sqlite3.connect(SAMPLE_DB)
        cursor = conn.cursor()
        
        # 检查记录数
        cursor.execute("SELECT COUNT(*) FROM features")
        count = cursor.fetchone()[0]
        print(f"  记录数: {count}")
        
        # 检查用户分布
        cursor.execute("SELECT user_id, COUNT(*) FROM features GROUP BY user_id")
        user_dist = cursor.fetchall()
        print(f"  用户分布:")
        for user_id, user_count in user_dist:
            print(f"    {user_id}: {user_count} 条")
        
        # 显示前3条记录
        cursor.execute("SELECT * FROM features LIMIT 3")
        sample_records = cursor.fetchall()
        print(f"  前3条记录:")
        for record in sample_records:
            print(f"    ID:{record[0]}, 用户:{record[1]}, 会话:{record[2]}, 时间戳:{record[3]}")
            # 显示特征向量的前100个字符
            feature_preview = record[4][:100] + "..." if len(record[4]) > 100 else record[4]
            print(f"      特征向量: {feature_preview}")
        
        conn.close()
        
    except Exception as e:
        print(f"验证失败: {str(e)}")

def main():
    print("=== 特征数据库样本导出工具 ===")
    
    if not SOURCE_DB.exists():
        print(f"错误: 源数据库 {SOURCE_DB} 不存在")
        print("请确保已经运行过数据采集和特征工程，生成了mouse_data.db文件")
        return
    
    # 导出样本数据
    if export_sample_data(1000):
        # 验证结果
        verify_sample_db()
        print(f"\n✓ 样本数据库创建完成: {SAMPLE_DB}")
        print("你可以将此文件提交到GitHub，用于跨机测试")
    else:
        print("✗ 样本数据库创建失败")

if __name__ == "__main__":
    main() 
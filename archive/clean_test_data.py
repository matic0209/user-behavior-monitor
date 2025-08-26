#!/usr/bin/env python3
"""
删除数据库中的测试数据
"""

import sqlite3
from pathlib import Path

def clean_test_data():
    """删除数据库中的测试数据"""
    print("🧹 删除数据库中的测试数据")
    print("=" * 50)
    
    db_path = Path("data/mouse_data.db")
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查删除前的数据
        print("📊 删除前的数据统计:")
        
        # features表
        cursor.execute("SELECT user_id, COUNT(*) FROM features GROUP BY user_id")
        features_users = cursor.fetchall()
        print(f"  features表用户: {len(features_users)} 个")
        for user_id, count in features_users:
            print(f"    {user_id}: {count} 条记录")
        
        # mouse_events表
        cursor.execute("SELECT user_id, COUNT(*) FROM mouse_events GROUP BY user_id")
        events_users = cursor.fetchall()
        print(f"  mouse_events表用户: {len(events_users)} 个")
        for user_id, count in events_users:
            print(f"    {user_id}: {count} 条记录")
        
        # predictions表
        cursor.execute("SELECT user_id, COUNT(*) FROM predictions GROUP BY user_id")
        predictions_users = cursor.fetchall()
        print(f"  predictions表用户: {len(predictions_users)} 个")
        for user_id, count in predictions_users:
            print(f"    {user_id}: {count} 条记录")
        
        # 删除测试数据
        print(f"\n🗑️ 删除测试数据...")
        
        # 删除features表中的测试数据
        test_users = ['test_user_1', 'test_user_2', 'test_user_3', 'quick_test_user']
        for user_id in test_users:
            cursor.execute("DELETE FROM features WHERE user_id = ?", (user_id,))
            deleted_count = cursor.rowcount
            print(f"  删除 features 表中 {user_id}: {deleted_count} 条记录")
        
        # 删除mouse_events表中的测试数据
        for user_id in test_users:
            cursor.execute("DELETE FROM mouse_events WHERE user_id = ?", (user_id,))
            deleted_count = cursor.rowcount
            print(f"  删除 mouse_events 表中 {user_id}: {deleted_count} 条记录")
        
        # 删除predictions表中的测试数据
        for user_id in test_users:
            cursor.execute("DELETE FROM predictions WHERE user_id = ?", (user_id,))
            deleted_count = cursor.rowcount
            print(f"  删除 predictions 表中 {user_id}: {deleted_count} 条记录")
        
        # 提交事务
        conn.commit()
        
        # 检查删除后的数据
        print(f"\n📊 删除后的数据统计:")
        
        # features表
        cursor.execute("SELECT user_id, COUNT(*) FROM features GROUP BY user_id")
        features_users = cursor.fetchall()
        print(f"  features表用户: {len(features_users)} 个")
        for user_id, count in features_users:
            print(f"    {user_id}: {count} 条记录")
        
        # mouse_events表
        cursor.execute("SELECT user_id, COUNT(*) FROM mouse_events GROUP BY user_id")
        events_users = cursor.fetchall()
        print(f"  mouse_events表用户: {len(events_users)} 个")
        for user_id, count in events_users:
            print(f"    {user_id}: {count} 条记录")
        
        # predictions表
        cursor.execute("SELECT user_id, COUNT(*) FROM predictions GROUP BY user_id")
        predictions_users = cursor.fetchall()
        print(f"  predictions表用户: {len(predictions_users)} 个")
        for user_id, count in predictions_users:
            print(f"    {user_id}: {count} 条记录")
        
        # 统计总记录数
        cursor.execute("SELECT COUNT(*) FROM features")
        total_features = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM mouse_events")
        total_events = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]
        
        print(f"\n📈 总记录数:")
        print(f"  features: {total_features}")
        print(f"  mouse_events: {total_events}")
        print(f"  predictions: {total_predictions}")
        
        conn.close()
        
        print(f"\n✅ 测试数据删除完成")
        
    except Exception as e:
        print(f"❌ 删除测试数据失败: {e}")

def main():
    """主函数"""
    print("🧹 删除数据库中的测试数据")
    print("=" * 60)
    
    # 删除测试数据
    clean_test_data()
    
    print("\n" + "=" * 60)
    print("✅ 清理完成")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
数据流诊断脚本
检查数据收集和存储过程
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
import time
from datetime import datetime

def check_database_content():
    """检查数据库内容"""
    print("=== 检查数据库内容 ===")
    
    try:
        from src.utils.config.config_loader import ConfigLoader
        config = ConfigLoader()
        db_path = Path(config.get_paths()['database'])
        
        if not db_path.exists():
            print(f"✗ 数据库文件不存在: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"数据库表: {tables}")
        
        # 检查mouse_events表
        if 'mouse_events' in tables:
            cursor.execute("SELECT COUNT(*) FROM mouse_events")
            mouse_count = cursor.fetchone()[0]
            print(f"mouse_events表记录数: {mouse_count}")
            
            if mouse_count > 0:
                cursor.execute("SELECT DISTINCT user_id FROM mouse_events LIMIT 5")
                mouse_users = [row[0] for row in cursor.fetchall()]
                print(f"mouse_events用户示例: {mouse_users}")
                
                cursor.execute("SELECT * FROM mouse_events ORDER BY timestamp DESC LIMIT 3")
                recent_events = cursor.fetchall()
                print("最近的鼠标事件:")
                for event in recent_events:
                    print(f"  {event}")
        
        # 检查features表
        if 'features' in tables:
            cursor.execute("SELECT COUNT(*) FROM features")
            features_count = cursor.fetchone()[0]
            print(f"features表记录数: {features_count}")
            
            if features_count > 0:
                cursor.execute("SELECT DISTINCT user_id FROM features LIMIT 5")
                features_users = [row[0] for row in cursor.fetchall()]
                print(f"features用户示例: {features_users}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 检查数据库失败: {str(e)}")
        return False

def test_data_collector():
    """测试数据收集器"""
    print("\n=== 测试数据收集器 ===")
    
    try:
        from src.core.data_collector.windows_mouse_collector import WindowsMouseCollector
        from src.core.user_manager import UserManager
        
        # 创建用户管理器
        user_manager = UserManager()
        user_id = user_manager.get_current_user_id()
        print(f"当前用户ID: {user_id}")
        
        # 创建数据收集器
        collector = WindowsMouseCollector()
        print("✓ 数据收集器创建成功")
        
        # 测试数据收集（短暂运行）
        print("开始测试数据收集（5秒）...")
        collector.start_collection()
        time.sleep(5)
        collector.stop_collection()
        print("✓ 数据收集测试完成")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据收集器测试失败: {str(e)}")
        return False

def test_database_connection():
    """测试数据库连接和写入"""
    print("\n=== 测试数据库连接和写入 ===")
    
    try:
        from src.utils.config.config_loader import ConfigLoader
        config = ConfigLoader()
        db_path = Path(config.get_paths()['database'])
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 测试插入一条记录
        test_user_id = "test_user_diagnostic"
        test_session_id = "test_session_diagnostic"
        test_timestamp = time.time()
        
        cursor.execute('''
            INSERT INTO mouse_events (user_id, session_id, timestamp, x, y, event_type, button, wheel_delta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (test_user_id, test_session_id, test_timestamp, 100, 200, 'move', None, 0))
        
        conn.commit()
        print("✓ 测试记录插入成功")
        
        # 验证插入
        cursor.execute("SELECT * FROM mouse_events WHERE user_id = ?", (test_user_id,))
        result = cursor.fetchone()
        if result:
            print(f"✓ 验证插入成功: {result}")
        else:
            print("✗ 验证插入失败")
        
        # 清理测试数据
        cursor.execute("DELETE FROM mouse_events WHERE user_id = ?", (test_user_id,))
        conn.commit()
        print("✓ 测试数据清理完成")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 数据库连接测试失败: {str(e)}")
        return False

def check_data_collector_config():
    """检查数据收集器配置"""
    print("\n=== 检查数据收集器配置 ===")
    
    try:
        from src.utils.config.config_loader import ConfigLoader
        config = ConfigLoader()
        
        # 检查配置
        paths = config.get_paths()
        print(f"数据库路径: {paths.get('database')}")
        print(f"日志路径: {paths.get('logs')}")
        
        # 检查数据收集器配置
        collector_config = config.get_data_collector_config()
        print(f"数据收集器配置: {collector_config}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置检查失败: {str(e)}")
        return False

def generate_sample_mouse_data():
    """生成样本鼠标数据"""
    print("\n=== 生成样本鼠标数据 ===")
    
    try:
        from src.utils.config.config_loader import ConfigLoader
        config = ConfigLoader()
        db_path = Path(config.get_paths()['database'])
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 生成100条样本鼠标事件
        sample_user_id = "sample_user"
        sample_session_id = "sample_session"
        base_timestamp = time.time()
        
        events = []
        for i in range(100):
            timestamp = base_timestamp + i * 0.1  # 每100ms一个事件
            x = 100 + (i % 800)  # 在100-900范围内移动
            y = 100 + (i % 600)  # 在100-700范围内移动
            
            # 交替事件类型
            if i % 10 == 0:
                event_type = 'click'
                button = 'left'
            elif i % 5 == 0:
                event_type = 'move'
                button = None
            else:
                event_type = 'move'
                button = None
            
            events.append((sample_user_id, sample_session_id, timestamp, x, y, event_type, button, 0))
        
        # 批量插入
        cursor.executemany('''
            INSERT INTO mouse_events (user_id, session_id, timestamp, x, y, event_type, button, wheel_delta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', events)
        
        conn.commit()
        print(f"✓ 生成了 {len(events)} 条样本鼠标事件")
        
        # 验证插入
        cursor.execute("SELECT COUNT(*) FROM mouse_events WHERE user_id = ?", (sample_user_id,))
        count = cursor.fetchone()[0]
        print(f"✓ 验证: 数据库中有 {count} 条样本记录")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 生成样本数据失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("数据流诊断脚本")
    print("=" * 50)
    
    # 1. 检查数据库内容
    check_database_content()
    
    # 2. 检查配置
    check_data_collector_config()
    
    # 3. 测试数据库连接
    test_database_connection()
    
    # 4. 测试数据收集器
    test_data_collector()
    
    # 5. 生成样本数据
    generate_sample_mouse_data()
    
    # 6. 再次检查数据库内容
    print("\n=== 最终检查 ===")
    check_database_content()
    
    print("\n" + "=" * 50)
    print("🎉 诊断完成！")
    print("\n如果mouse_events表仍然为空，可能的原因:")
    print("1. 数据收集器没有正确启动")
    print("2. 数据库权限问题")
    print("3. 配置文件路径错误")
    print("4. 鼠标事件监听器权限问题")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
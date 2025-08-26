#!/usr/bin/env python3
"""
简化的鼠标数据采集测试
直接测试数据采集功能
"""

import sys
import time
import sqlite3
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_simple_mouse_collection():
    """简单的鼠标数据采集测试"""
    print("=== 简单鼠标数据采集测试 ===")
    
    try:
        # 测试Windows API
        print("1. 测试Windows API...")
        import win32api
        pos = win32api.GetCursorPos()
        print(f"   鼠标位置: {pos}")
        
        # 创建数据库
        print("2. 创建测试数据库...")
        db_path = Path("data/test_mouse.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_mouse_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                event_type TEXT NOT NULL
            )
        ''')
        conn.commit()
        
        # 开始采集
        print("3. 开始数据采集 (10秒)...")
        events = []
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                # 获取鼠标位置
                pos = win32api.GetCursorPos()
                x, y = pos
                
                # 记录事件
                event = {
                    'timestamp': time.time(),
                    'x': x,
                    'y': y,
                    'event_type': 'move'
                }
                events.append(event)
                
                # 每100个事件保存一次
                if len(events) % 100 == 0:
                    print(f"   已采集 {len(events)} 个事件...")
                
                time.sleep(0.1)  # 100ms间隔
                
            except Exception as e:
                print(f"   采集异常: {e}")
                time.sleep(0.1)
        
        # 保存数据
        print("4. 保存数据到数据库...")
        cursor.executemany('''
            INSERT INTO test_mouse_events (timestamp, x, y, event_type)
            VALUES (?, ?, ?, ?)
        ''', [
            (event['timestamp'], event['x'], event['y'], event['event_type'])
            for event in events
        ])
        conn.commit()
        
        # 查询数据
        cursor.execute('SELECT COUNT(*) FROM test_mouse_events')
        count = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM test_mouse_events')
        time_range = cursor.fetchone()
        
        print(f"5. 采集结果:")
        print(f"   总事件数: {count}")
        print(f"   时间范围: {time_range[0]:.2f} - {time_range[1]:.2f}")
        print(f"   采集时长: {time_range[1] - time_range[0]:.2f} 秒")
        
        conn.close()
        
        if count > 0:
            print("✓ 数据采集测试成功!")
            return True
        else:
            print("✗ 没有采集到数据")
            return False
            
    except ImportError as e:
        print(f"✗ Windows API不可用: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_keyboard_hotkey():
    """测试键盘快捷键"""
    print("\n=== 键盘快捷键测试 ===")
    
    try:
        from pynput import keyboard
        
        print("连续按下 c 键4次开始测试 (10秒)...")
        print("提示: 需要在1秒内连续按4次c键")
        
        hotkey_detected = False
        listener = None
        key_sequence = []
        last_key_time = 0
        sequence_timeout = 1.0
        sequence_count = 4
        
        def on_press(key):
            nonlocal hotkey_detected, key_sequence, last_key_time
            
            try:
                if hasattr(key, 'char'):
                    char = key.char.lower()
                    current_time = time.time()
                    print(f"按下字符键: {char}")
                    
                    if char == 'c':
                        # 添加到序列
                        key_sequence.append(char)
                        
                        # 如果序列长度超过4，移除最早的
                        if len(key_sequence) > sequence_count:
                            key_sequence.pop(0)
                        
                        # 检查是否在时间窗口内
                        if current_time - last_key_time <= sequence_timeout:
                            # 检查是否连续4次相同字符
                            if len(key_sequence) == sequence_count and len(set(key_sequence)) == 1:
                                print("✓ 检测到快捷键序列: c x4")
                                hotkey_detected = True
                                if listener:
                                    listener.stop()
                                return False
                        
                        # 更新最后按键时间
                        last_key_time = current_time
                    else:
                        # 非c键，清空序列
                        key_sequence = []
                else:
                    print(f"按下特殊键: {key}")
                    key_sequence = []
            except Exception as e:
                print(f"按键处理异常: {e}")
        
        def on_release(key):
            try:
                if hasattr(key, 'char'):
                    print(f"释放字符键: {key.char}")
                else:
                    print(f"释放特殊键: {key}")
            except Exception as e:
                print(f"按键释放处理异常: {e}")
        
        # 创建监听器
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        
        # 等待10秒或直到检测到快捷键
        start_time = time.time()
        while time.time() - start_time < 10 and not hotkey_detected:
            time.sleep(0.1)
        
        # 停止监听器
        if listener:
            listener.stop()
        
        if hotkey_detected:
            print("✓ 键盘快捷键测试成功!")
            return True
        else:
            print("✗ 未检测到快捷键")
            print("可能的原因:")
            print("- 没有连续按4次c键")
            print("- 按键间隔超过1秒")
            print("- 键盘监听权限不足")
            return False
            
    except ImportError as e:
        print(f"✗ pynput不可用: {e}")
        return False
    except Exception as e:
        print(f"✗ 键盘测试失败: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    print("鼠标数据采集问题诊断")
    print("=" * 40)
    
    # 测试1: 简单鼠标采集
    result1 = test_simple_mouse_collection()
    
    # 测试2: 键盘快捷键
    result2 = test_keyboard_hotkey()
    
    # 总结
    print("\n" + "=" * 40)
    print("测试结果:")
    print(f"鼠标数据采集: {'✓ 成功' if result1 else '✗ 失败'}")
    print(f"键盘快捷键: {'✓ 成功' if result2 else '✗ 失败'}")
    
    if result1 and result2:
        print("\n✓ 所有测试通过，系统应该可以正常工作")
        print("建议:")
        print("1. 运行 python start_monitor.py")
        print("2. 按 Ctrl+Alt+C 开始数据采集")
        print("3. 按 Ctrl+Alt+S 停止数据采集")
    else:
        print("\n✗ 存在问题，请检查:")
        if not result1:
            print("- Windows API权限")
            print("- 数据库写入权限")
        if not result2:
            print("- pynput库安装")
            print("- 键盘监听权限")

if __name__ == "__main__":
    main() 
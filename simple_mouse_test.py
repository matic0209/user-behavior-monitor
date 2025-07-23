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
        
        print("按下 Ctrl+Alt+C 开始测试 (5秒)...")
        
        ctrl_pressed = False
        alt_pressed = False
        hotkey_detected = False
        
        def on_press(key):
            nonlocal ctrl_pressed, alt_pressed, hotkey_detected
            
            if key == keyboard.Key.ctrl:
                ctrl_pressed = True
                print("Ctrl键按下")
            elif key == keyboard.Key.alt:
                alt_pressed = True
                print("Alt键按下")
            elif hasattr(key, 'char') and key.char == 'c':
                if ctrl_pressed and alt_pressed:
                    print("✓ 检测到快捷键: Ctrl+Alt+C")
                    hotkey_detected = True
                    return False  # 停止监听
        
        def on_release(key):
            nonlocal ctrl_pressed, alt_pressed
            
            if key == keyboard.Key.ctrl:
                ctrl_pressed = False
                print("Ctrl键释放")
            elif key == keyboard.Key.alt:
                alt_pressed = False
                print("Alt键释放")
        
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
        
        if hotkey_detected:
            print("✓ 键盘快捷键测试成功!")
            return True
        else:
            print("✗ 未检测到快捷键")
            return False
            
    except ImportError as e:
        print(f"✗ pynput不可用: {e}")
        return False
    except Exception as e:
        print(f"✗ 键盘测试失败: {e}")
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
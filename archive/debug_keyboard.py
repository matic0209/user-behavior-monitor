#!/usr/bin/env python3
"""
键盘监听调试脚本
用于测试键盘监听是否正常工作
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_keyboard():
    """基础键盘监听测试"""
    print("=== 基础键盘监听测试 ===")
    
    try:
        from pynput import keyboard
        
        print("开始监听键盘事件 (10秒)...")
        print("请随意按一些键，观察输出")
        print("按 Ctrl+C 可以提前退出")
        
        def on_press(key):
            try:
                if hasattr(key, 'char'):
                    print(f"按下字符键: '{key.char}'")
                else:
                    print(f"按下特殊键: {key}")
            except Exception as e:
                print(f"按键处理异常: {e}")
        
        def on_release(key):
            try:
                if hasattr(key, 'char'):
                    print(f"释放字符键: '{key.char}'")
                else:
                    print(f"释放特殊键: {key}")
            except Exception as e:
                print(f"按键释放处理异常: {e}")
        
        # 创建监听器
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        
        # 等待10秒
        start_time = time.time()
        while time.time() - start_time < 10:
            time.sleep(0.1)
        
        # 停止监听器
        listener.stop()
        print("键盘监听测试完成")
        return True
        
    except ImportError as e:
        print(f"✗ pynput不可用: {e}")
        return False
    except Exception as e:
        print(f"✗ 键盘监听测试失败: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False

def test_hotkey_detection():
    """快捷键检测测试"""
    print("\n=== 快捷键检测测试 ===")
    
    try:
        from pynput import keyboard
        
        print("请连续按 c 键4次")
        print("测试时间: 10秒")
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
                    print(f"按下: {char}")
                    
                    if char == 'c':
                        # 添加到序列
                        key_sequence.append(char)
                        print(f"序列: {key_sequence}")
                        
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
                        else:
                            print("时间间隔过长，重置序列")
                            key_sequence = [char]
                        
                        # 更新最后按键时间
                        last_key_time = current_time
                    else:
                        # 非c键，清空序列
                        key_sequence = []
                        print("非快捷键字符，重置序列")
                else:
                    print(f"按下: {key}")
                    key_sequence = []
            except Exception as e:
                print(f"按键处理异常: {e}")
        
        def on_release(key):
            try:
                if hasattr(key, 'char'):
                    print(f"释放: {key.char}")
                else:
                    print(f"释放: {key}")
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
            print("✓ 快捷键检测测试成功!")
            return True
        else:
            print("✗ 未检测到快捷键")
            return False
            
    except ImportError as e:
        print(f"✗ pynput不可用: {e}")
        return False
    except Exception as e:
        print(f"✗ 快捷键检测测试失败: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    print("键盘监听调试工具")
    print("=" * 40)
    
    # 测试1: 基础键盘监听
    result1 = test_basic_keyboard()
    
    # 测试2: 快捷键检测
    result2 = test_hotkey_detection()
    
    # 总结
    print("\n" + "=" * 40)
    print("测试结果:")
    print(f"基础键盘监听: {'✓ 成功' if result1 else '✗ 失败'}")
    print(f"快捷键检测: {'✓ 成功' if result2 else '✗ 失败'}")
    
    if result1 and result2:
        print("\n✓ 所有测试通过，键盘监听功能正常")
    else:
        print("\n✗ 存在问题:")
        if not result1:
            print("- 基础键盘监听失败，可能是权限问题")
        if not result2:
            print("- 快捷键检测失败，可能是组合键逻辑问题")
        
        print("\n建议:")
        print("1. 确保以管理员权限运行")
        print("2. 检查是否有其他程序占用键盘监听")
        print("3. 尝试重新安装pynput: pip install --upgrade pynput")

if __name__ == "__main__":
    main() 
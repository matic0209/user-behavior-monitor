#!/usr/bin/env python3
"""
鼠标数据采集测试脚本
用于诊断数据采集问题
"""

import sys
import time
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_windows_api():
    """测试Windows API是否可用"""
    print("=== 测试Windows API ===")
    
    try:
        import win32api
        print("✓ win32api 导入成功")
        
        # 测试获取鼠标位置
        pos = win32api.GetCursorPos()
        print(f"✓ 鼠标位置获取成功: {pos}")
        
        return True
    except ImportError as e:
        print(f"✗ win32api 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 鼠标位置获取失败: {e}")
        return False

def test_keyboard_listener():
    """测试键盘监听器"""
    print("\n=== 测试键盘监听器 ===")
    
    try:
        from pynput import keyboard
        print("✓ pynput 导入成功")
        
        # 测试键盘监听
        def on_press(key):
            print(f"按下键: {key}")
        
        def on_release(key):
            print(f"释放键: {key}")
        
        print("开始键盘监听测试 (5秒)...")
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            time.sleep(5)
        
        print("✓ 键盘监听器测试完成")
        return True
        
    except ImportError as e:
        print(f"✗ pynput 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 键盘监听器测试失败: {e}")
        return False

def test_config_loader():
    """测试配置加载器"""
    print("\n=== 测试配置加载器 ===")
    
    try:
        from src.utils.config.config_loader import ConfigLoader
        
        config = ConfigLoader()
        print("✓ 配置加载器创建成功")
        
        # 测试获取配置
        paths = config.get_paths()
        print(f"✓ 路径配置: {paths}")
        
        data_config = config.get_data_collection_config()
        print(f"✓ 数据采集配置: {data_config}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置加载器测试失败: {e}")
        print(f"异常详情: {traceback.format_exc()}")
        return False

def test_mouse_collector():
    """测试鼠标采集器"""
    print("\n=== 测试鼠标采集器 ===")
    
    try:
        from src.core.data_collector.windows_mouse_collector import WindowsMouseCollector
        
        # 创建采集器
        collector = WindowsMouseCollector("test_user")
        print("✓ 鼠标采集器创建成功")
        
        # 测试启动采集
        print("启动数据采集 (5秒)...")
        if collector.start_collection():
            print("✓ 数据采集启动成功")
            
            # 等待5秒
            time.sleep(5)
            
            # 停止采集
            collector.stop_collection()
            print("✓ 数据采集停止成功")
            
            # 检查数据
            data = collector.get_session_data()
            print(f"✓ 采集到 {len(data)} 条数据")
            
            return True
        else:
            print("✗ 数据采集启动失败")
            return False
            
    except Exception as e:
        print(f"✗ 鼠标采集器测试失败: {e}")
        print(f"异常详情: {traceback.format_exc()}")
        return False

def test_user_manager():
    """测试用户管理器"""
    print("\n=== 测试用户管理器 ===")
    
    try:
        from src.core.user_manager import UserManager
        
        # 创建用户管理器
        user_manager = UserManager()
        print("✓ 用户管理器创建成功")
        
        # 测试获取用户ID
        user_id = user_manager.get_current_user_id()
        print(f"✓ 当前用户ID: {user_id}")
        
        # 测试键盘监听器
        print("启动键盘监听器 (5秒)...")
        user_manager.start_keyboard_listener()
        time.sleep(5)
        user_manager.stop_keyboard_listener()
        print("✓ 键盘监听器测试完成")
        
        return True
        
    except Exception as e:
        print(f"✗ 用户管理器测试失败: {e}")
        print(f"异常详情: {traceback.format_exc()}")
        return False

def main():
    """主测试函数"""
    print("鼠标数据采集诊断工具")
    print("=" * 50)
    
    tests = [
        ("Windows API", test_windows_api),
        ("键盘监听器", test_keyboard_listener),
        ("配置加载器", test_config_loader),
        ("鼠标采集器", test_mouse_collector),
        ("用户管理器", test_user_manager)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    # 给出建议
    print("\n建议:")
    failed_tests = [name for name, result in results if not result]
    
    if not failed_tests:
        print("✓ 所有测试通过，系统应该可以正常工作")
    else:
        print(f"✗ 以下测试失败: {', '.join(failed_tests)}")
        
        if "Windows API" in failed_tests:
            print("- 请确保在Windows系统上运行")
            print("- 请安装pywin32: pip install pywin32")
        
        if "键盘监听器" in failed_tests:
            print("- 请安装pynput: pip install pynput")
        
        if "配置加载器" in failed_tests:
            print("- 请检查配置文件是否存在")
            print("- 请检查YAML格式是否正确")
        
        if "鼠标采集器" in failed_tests:
            print("- 请检查数据库权限")
            print("- 请检查Windows API权限")
        
        if "用户管理器" in failed_tests:
            print("- 请检查用户配置文件权限")

if __name__ == "__main__":
    main() 
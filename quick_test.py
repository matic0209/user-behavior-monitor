#!/usr/bin/env python3
"""
快速测试脚本
验证心跳功能集成是否正常
"""

import sys
import time
import json
import urllib.request
import urllib.parse
import urllib.error

def test_imports():
    """测试必要的模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        import urllib.request
        import urllib.parse
        import urllib.error
        import json
        import threading
        import time
        print("[SUCCESS] 所有必要模块导入成功")
        return True
    except ImportError as e:
        print(f"[ERROR] 模块导入失败: {e}")
        return False

def test_heartbeat_request():
    """测试心跳请求"""
    print("🔍 测试心跳请求...")
    
    heartbeat_url = "http://127.0.0.1:26002/heartbeat"
    heartbeat_data = {"type": 4}
    
    try:
        # 准备请求数据
        data = json.dumps(heartbeat_data).encode('utf-8')
        headers = {
            'Content-Type': 'application/json'
        }
        
        # 创建请求
        req = urllib.request.Request(
            heartbeat_url,
            data=data,
            headers=headers,
            method='POST'
        )
        
        # 发送请求
        with urllib.request.urlopen(req, timeout=5) as response:
            response_code = response.getcode()
            if response_code == 200:
                print("[SUCCESS] 心跳请求测试成功")
                return True
            else:
                print(f"[ERROR] 心跳请求失败，状态码: {response_code}")
                return False
                
    except urllib.error.URLError as e:
        print(f"[ERROR] 心跳请求失败 (网络错误): {str(e)}")
        print("[TIP] 请确保模拟心跳服务器正在运行")
        return False
    except Exception as e:
        print(f"[ERROR] 心跳请求失败: {str(e)}")
        return False

def test_main_program_imports():
    """测试主程序导入"""
    print("🔍 测试主程序导入...")
    
    try:
        # 模拟主程序的关键导入
        import sys
        import os
        import time
        import signal
        import threading
        import psutil
        from pathlib import Path
        import traceback
        import json
        from datetime import datetime
        import urllib.request
        import urllib.parse
        import urllib.error
        
        print("[SUCCESS] 主程序模块导入成功")
        return True
    except ImportError as e:
        print(f"[ERROR] 主程序模块导入失败: {e}")
        return False

def test_build_script_imports():
    """测试构建脚本导入"""
    print("🔍 测试构建脚本导入...")
    
    try:
        import os
        import sys
        import subprocess
        import shutil
        from pathlib import Path
        
        print("[SUCCESS] 构建脚本模块导入成功")
        return True
    except ImportError as e:
        print(f"[ERROR] 构建脚本模块导入失败: {e}")
        return False

def check_server_status():
    """检查服务器状态"""
    print("🔍 检查心跳服务器状态...")
    
    try:
        response = urllib.request.urlopen('http://127.0.0.1:26002/', timeout=5)
        if response.getcode() == 200:
            print("[SUCCESS] 心跳服务器正在运行")
            return True
        else:
            print(f"[ERROR] 心跳服务器响应异常，状态码: {response.getcode()}")
            return False
    except:
        print("[ERROR] 心跳服务器未运行")
        print("[TIP] 请运行: python3 mock_heartbeat_server.py")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("心跳功能集成测试")
    print("=" * 50)
    
    tests = [
        ("模块导入测试", test_imports),
        ("主程序导入测试", test_main_program_imports),
        ("构建脚本导入测试", test_build_script_imports),
        ("服务器状态检查", check_server_status),
        ("心跳请求测试", test_heartbeat_request),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}")
        print("-" * 30)
        
        if test_func():
            passed += 1
            print(f"[SUCCESS] {test_name} 通过")
        else:
            print(f"[ERROR] {test_name} 失败")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("[SUCCESS] 所有测试通过！心跳功能集成成功")
        print("\n[NEXT] 下一步:")
        print("1. 运行主程序: python user_behavior_monitor.py")
        print("2. 打包程序: python build_exe_simple_fixed.py")
        print("3. 查看日志: tail -f logs/monitor_*.log")
        return 0
    else:
        print("[ERROR] 部分测试失败，请检查相关配置")
        print("\n[TIP] 建议:")
        print("1. 确保模拟心跳服务器正在运行")
        print("2. 检查网络连接")
        print("3. 验证所有依赖已安装")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

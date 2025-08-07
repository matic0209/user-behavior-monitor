#!/usr/bin/env python3
"""
Windows构建脚本调试版本
用于测试各个步骤是否正常工作
"""

import os
import sys
import subprocess
import shutil
import time
import platform

def test_windows_check():
    """测试Windows环境检查"""
    print("测试Windows环境检查...")
    if platform.system() == 'Windows':
        print("[SUCCESS] 当前是Windows系统")
        return True
    else:
        print(f"[INFO] 当前系统: {platform.system()}")
        return False

def test_dependencies():
    """测试依赖检查"""
    print("测试依赖检查...")
    
    test_modules = ['psutil', 'yaml', 'numpy', 'pandas']
    
    for module in test_modules:
        try:
            __import__(module)
            print(f"[SUCCESS] {module} 可用")
        except ImportError:
            print(f"[ERROR] {module} 缺失")
    
    return True

def test_process_kill():
    """测试进程结束功能"""
    print("测试进程结束功能...")
    
    processes = ['python.exe', 'UserBehaviorMonitor.exe']
    
    for proc in processes:
        try:
            print(f"正在检查进程: {proc}")
            result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {proc}'], 
                                  capture_output=True, shell=True, timeout=5)
            if result.returncode == 0 and proc in result.stdout.decode():
                print(f"[INFO] 发现进程: {proc}")
                # 尝试结束进程
                kill_result = subprocess.run(['taskkill', '/f', '/im', proc], 
                                           capture_output=True, shell=True, timeout=10)
                if kill_result.returncode == 0:
                    print(f"[SUCCESS] 已结束进程: {proc}")
                else:
                    print(f"[WARNING] 无法结束进程: {proc}")
            else:
                print(f"[INFO] 进程 {proc} 未运行")
        except subprocess.TimeoutExpired:
            print(f"[WARNING] 检查进程 {proc} 超时")
        except Exception as e:
            print(f"[ERROR] 检查进程 {proc} 时出错: {e}")
    
    return True

def test_directory_cleanup():
    """测试目录清理功能"""
    print("测试目录清理功能...")
    
    test_dirs = ['build', 'dist', '__pycache__']
    
    for dir_name in test_dirs:
        if os.path.exists(dir_name):
            try:
                print(f"正在删除目录: {dir_name}")
                shutil.rmtree(dir_name)
                print(f"[SUCCESS] 已删除: {dir_name}")
            except Exception as e:
                print(f"[ERROR] 删除 {dir_name} 时出错: {e}")
        else:
            print(f"[INFO] 目录 {dir_name} 不存在")
    
    return True

def test_pyinstaller():
    """测试PyInstaller是否可用"""
    print("测试PyInstaller...")
    
    try:
        result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"[SUCCESS] PyInstaller可用，版本: {result.stdout.strip()}")
            return True
        else:
            print(f"[ERROR] PyInstaller不可用: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] 测试PyInstaller时出错: {e}")
        return False

def main():
    """主函数"""
    print("Windows构建脚本调试工具")
    print("=" * 40)
    
    try:
        # 测试Windows环境
        print("\n=== 测试1: Windows环境检查 ===")
        test_windows_check()
        
        # 测试依赖
        print("\n=== 测试2: 依赖检查 ===")
        test_dependencies()
        
        # 测试进程结束
        print("\n=== 测试3: 进程结束功能 ===")
        test_process_kill()
        
        # 测试目录清理
        print("\n=== 测试4: 目录清理功能 ===")
        test_directory_cleanup()
        
        # 测试PyInstaller
        print("\n=== 测试5: PyInstaller检查 ===")
        test_pyinstaller()
        
        print("\n" + "=" * 40)
        print("[SUCCESS] 所有测试完成!")
        print("[TIP] 如果所有测试都通过，可以运行完整的构建脚本")
        print("=" * 40)
        
    except Exception as e:
        print(f"\n[ERROR] 调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

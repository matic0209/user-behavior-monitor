#!/usr/bin/env python3
"""
Windows权限错误修复工具
"""

import os
import sys
import subprocess
import shutil
import time
import platform

def fix_encoding():
    """修复编码问题"""
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    if platform.system() == 'Windows':
        os.system('chcp 65001 > nul 2>&1')
        print("[SUCCESS] 编码已设置为UTF-8")

def kill_processes():
    """结束占用文件的进程"""
    processes = ['python.exe', 'UserBehaviorMonitor.exe', 'pyinstaller.exe']
    
    for proc in processes:
        try:
            subprocess.run(['taskkill', '/f', '/im', proc], 
                         capture_output=True, shell=True)
            print(f"[INFO] 已尝试结束进程: {proc}")
        except:
            pass

def clean_directories():
    """清理构建目录"""
    dirs = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"[SUCCESS] 已删除: {dir_name}")
            except PermissionError:
                print(f"[WARNING] 无法删除: {dir_name} (可能正在使用)")
            except Exception as e:
                print(f"[ERROR] 删除 {dir_name} 时出错: {e}")

def main():
    """主函数"""
    print("Windows权限错误修复工具")
    print("=" * 30)
    
    # 修复编码
    fix_encoding()
    
    # 结束进程
    kill_processes()
    
    # 清理目录
    clean_directories()
    
    print("\n[SUCCESS] 修复完成!")
    print("[TIP] 现在可以重新运行构建脚本")

if __name__ == "__main__":
    main()

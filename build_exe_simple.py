#!/usr/bin/env python3
"""
简化的PyInstaller打包脚本
专门解决Windows环境下PyInstaller命令找不到的问题
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除 {dir_name}")
    
    # 清理spec文件
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        spec_file.unlink()
        print(f"已删除 {spec_file}")

def check_pyinstaller():
    """检查PyInstaller是否可用"""
    print("检查PyInstaller...")
    
    # 方法1: 直接命令
    try:
        result = subprocess.run(['pyinstaller', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"PyInstaller版本: {result.stdout.strip()}")
        return ['pyinstaller']
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("pyinstaller命令不可用")
    
    # 方法2: python -m PyInstaller
    try:
        result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"PyInstaller模块版本: {result.stdout.strip()}")
        return [sys.executable, '-m', 'PyInstaller']
    except subprocess.CalledProcessError:
        print("PyInstaller模块也不可用")
    
    # 方法3: 尝试安装PyInstaller
    print("尝试安装PyInstaller...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], 
                      check=True, capture_output=True)
        print("PyInstaller安装成功")
        return [sys.executable, '-m', 'PyInstaller']
    except subprocess.CalledProcessError as e:
        print(f"安装PyInstaller失败: {e}")
        return None

def build_exe(pyinstaller_cmd):
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    cmd = pyinstaller_cmd + [
        '--onefile',                    # 单文件
        '--windowed',                   # 无控制台窗口
        '--name=UserBehaviorMonitor',   # 可执行文件名
        '--add-data=src/utils/config;src/utils/config',  # 配置文件
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32gui',
        '--hidden-import=win32service',
        '--hidden-import=win32serviceutil',
        '--hidden-import=pynput',
        '--hidden-import=xgboost',
        '--hidden-import=sklearn',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=yaml',
        'user_behavior_monitor.py'
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def main():
    """主函数"""
    print("简化版用户行为监控系统打包工具")
    print("=" * 30)
    
    # 检查操作系统
    if sys.platform != 'win32':
        print("错误: 此脚本只能在Windows系统上运行")
        return
    
    try:
        # 清理构建目录
        clean_build()
        
        # 检查PyInstaller
        pyinstaller_cmd = check_pyinstaller()
        if pyinstaller_cmd is None:
            print("错误: 无法找到或安装PyInstaller")
            return
        
        # 构建可执行文件
        if build_exe(pyinstaller_cmd):
            print("\n打包完成!")
            print("可执行文件位置: dist/UserBehaviorMonitor.exe")
        else:
            print("\n打包失败!")
        
    except Exception as e:
        print(f"打包过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 
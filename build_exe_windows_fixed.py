#!/usr/bin/env python3
"""
Windows环境优化的PyInstaller打包脚本
专门解决Windows权限问题和文件占用问题
"""

import os
import sys
import subprocess
import shutil
import time
import threading
from pathlib import Path

def safe_remove_path(path, max_retries=3, delay=1):
    """安全删除路径，带重试机制"""
    for attempt in range(max_retries):
        try:
            if os.path.isfile(path):
                os.unlink(path)
                print(f"已删除文件: {path}")
                return True
            elif os.path.isdir(path):
                shutil.rmtree(path)
                print(f"已删除目录: {path}")
                return True
        except PermissionError as e:
            if attempt < max_retries - 1:
                print(f"警告: 无法删除 {path} (尝试 {attempt + 1}/{max_retries})")
                print(f"错误: {e}")
                print(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
            else:
                print(f"错误: 无法删除 {path}，文件可能正在使用中")
                print(f"请关闭所有相关程序后重试")
                return False
        except Exception as e:
            print(f"删除 {path} 时出错: {e}")
            return False
    return False

def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    
    # 需要清理的目录
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"正在清理 {dir_name}...")
            safe_remove_path(dir_name)
    
    # 清理spec文件
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        print(f"正在清理 {spec_file}...")
        safe_remove_path(spec_file)
    
    # 清理日志文件（保留目录，只删除旧文件）
    log_dirs = ['logs', 'dist/logs']
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            print(f"正在清理 {log_dir} 中的旧日志文件...")
            try:
                for log_file in Path(log_dir).glob('*.log'):
                    # 只删除1小时前的日志文件
                    if log_file.stat().st_mtime < time.time() - 3600:
                        safe_remove_path(log_file)
            except Exception as e:
                print(f"清理日志文件时出错: {e}")

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
        '--hidden-import=urllib.request',
        '--hidden-import=urllib.parse',
        '--hidden-import=urllib.error',
        '--hidden-import=http.client',
        '--hidden-import=socket',
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

def check_windows_environment():
    """检查Windows环境"""
    print("检查Windows环境...")
    
    if sys.platform != 'win32':
        print("错误: 此脚本只能在Windows系统上运行")
        return False
    
    print("✅ Windows环境检查通过")
    return True

def main():
    """主函数"""
    print("Windows优化的用户行为监控系统打包工具")
    print("=" * 50)
    
    try:
        # 检查Windows环境
        if not check_windows_environment():
            return
        
        # 清理构建目录
        clean_build()
        
        # 检查PyInstaller
        pyinstaller_cmd = check_pyinstaller()
        if pyinstaller_cmd is None:
            print("错误: 无法找到或安装PyInstaller")
            print("请手动安装: pip install pyinstaller")
            return
        
        # 构建可执行文件
        if build_exe(pyinstaller_cmd):
            print("\n" + "=" * 50)
            print("✅ 构建完成!")
            print("可执行文件位置: dist/UserBehaviorMonitor.exe")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("❌ 构建失败!")
            print("请检查错误信息并重试")
            print("=" * 50)
            
    except KeyboardInterrupt:
        print("\n用户中断构建过程")
    except Exception as e:
        print(f"\n构建过程中出现未知错误: {e}")
        print("请检查环境配置并重试")

if __name__ == "__main__":
    main()

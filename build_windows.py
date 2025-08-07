#!/usr/bin/env python3
"""
Windows专用构建脚本
包含完整的依赖检查和错误处理
"""

import os
import sys
import subprocess
import shutil
import time
import platform

def check_windows():
    """检查是否在Windows环境下"""
    if platform.system() != 'Windows':
        print("[ERROR] 此脚本只能在Windows系统上运行")
        return False
    return True

def check_dependencies():
    """检查依赖是否安装"""
    print("检查依赖...")
    
    required_modules = [
        'psutil',
        'pynput',
        'keyboard',
        'yaml',
        'numpy',
        'pandas',
        'sklearn',
        'xgboost',
        'win32api',
        'win32con',
        'win32gui',
        'win32service',
        'win32serviceutil'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"[SUCCESS] {module} 可用")
        except ImportError:
            print(f"[ERROR] {module} 缺失")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n[ERROR] 以下模块缺失: {missing_modules}")
        print("[TIP] 请先运行: python install_dependencies_windows.py")
        return False
    
    print("[SUCCESS] 所有依赖检查通过")
    return True

def setup_environment():
    """设置环境"""
    # 设置编码
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # 设置控制台编码
    os.system('chcp 65001 > nul 2>&1')
    print("[SUCCESS] 环境设置完成")

def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"[SUCCESS] 已删除: {dir_name}")
            except PermissionError:
                print(f"[WARNING] 无法删除 {dir_name}，可能正在使用")
            except Exception as e:
                print(f"[ERROR] 删除 {dir_name} 时出错: {e}")

def kill_conflicting_processes():
    """结束冲突的进程"""
    print("检查并结束冲突进程...")
    
    processes = ['python.exe', 'UserBehaviorMonitor.exe', 'pyinstaller.exe']
    
    for proc in processes:
        try:
            result = subprocess.run(['taskkill', '/f', '/im', proc], 
                                  capture_output=True, shell=True)
            if result.returncode == 0:
                print(f"[SUCCESS] 已结束进程: {proc}")
        except Exception as e:
            print(f"[INFO] 进程 {proc} 未运行或无法结束")

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # Windows专用构建命令
    build_cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',                    # 单文件
        '--windowed',                   # 无控制台窗口
        '--name=UserBehaviorMonitor',   # 可执行文件名
        '--add-data=src/utils/config;src/utils/config',  # 配置文件
        
        # Windows API
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32gui',
        '--hidden-import=win32service',
        '--hidden-import=win32serviceutil',
        
        # 核心依赖
        '--hidden-import=pynput',
        '--hidden-import=psutil',
        '--hidden-import=keyboard',
        '--hidden-import=yaml',
        '--hidden-import=numpy',
        '--hidden-import=pandas',
        '--hidden-import=sklearn',
        '--hidden-import=xgboost',
        
        # 网络通信模块（心跳功能）
        '--hidden-import=urllib.request',
        '--hidden-import=urllib.parse',
        '--hidden-import=urllib.error',
        
        # 强制收集关键模块
        '--collect-all=xgboost',
        '--collect-all=sklearn',
        '--collect-all=pandas',
        '--collect-all=numpy',
        '--collect-all=psutil',
        '--collect-all=pynput',
        
        # 排除不需要的模块以减小体积
        '--exclude-module=matplotlib',
        '--exclude-module=seaborn',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        '--exclude-module=notebook',
        
        'user_behavior_monitor.py'
    ]
    
    try:
        print("执行构建命令...")
        print(f"命令: {' '.join(build_cmd)}")
        
        result = subprocess.run(build_cmd, check=True, 
                              capture_output=True, text=True, encoding='utf-8')
        
        print("[SUCCESS] 构建成功!")
        print("构建输出:")
        print(result.stdout)
        
        # 检查生成的文件
        exe_path = 'dist/UserBehaviorMonitor.exe'
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"[SUCCESS] 可执行文件已生成: {exe_path}")
            print(f"[INFO] 文件大小: {size:.1f} MB")
            return True
        else:
            print("[ERROR] 可执行文件未生成")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 构建失败!")
        print(f"[ERROR] 返回码: {e.returncode}")
        print(f"[ERROR] 错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"[ERROR] 构建过程中出错: {e}")
        return False

def main():
    """主函数"""
    print("Windows专用构建脚本")
    print("=" * 40)
    
    # 检查Windows环境
    if not check_windows():
        return
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 设置环境
    setup_environment()
    
    # 结束冲突进程
    kill_conflicting_processes()
    
    # 清理构建目录
    clean_build()
    
    # 等待一下确保文件释放
    print("等待文件系统稳定...")
    time.sleep(2)
    
    # 构建可执行文件
    if build_executable():
        print("\n" + "=" * 40)
        print("[SUCCESS] 构建完成!")
        print("[INFO] 可执行文件位置: dist/UserBehaviorMonitor.exe")
        print("=" * 40)
    else:
        print("\n" + "=" * 40)
        print("[ERROR] 构建失败!")
        print("[TIP] 请检查错误信息并重试")
        print("=" * 40)

if __name__ == "__main__":
    main()

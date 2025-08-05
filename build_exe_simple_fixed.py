#!/usr/bin/env python3
"""
简化的xgboost修复版打包脚本
避免spec文件复杂性，直接使用命令行参数
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
        return None

def build_exe_simple(pyinstaller_cmd):
    """简化的构建方法"""
    print("开始构建可执行文件（简化版）...")
    
    cmd = pyinstaller_cmd + [
        '--onefile',                    # 单文件
        '--windowed',                   # 无控制台窗口
        '--name=UserBehaviorMonitor',   # 可执行文件名
        '--add-data=src/utils/config;src/utils/config',  # 配置文件
        
        # 核心依赖
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32gui',
        '--hidden-import=win32service',
        '--hidden-import=win32serviceutil',
        '--hidden-import=pynput',
        '--hidden-import=psutil',
        '--hidden-import=keyboard',
        '--hidden-import=yaml',
        '--hidden-import=numpy',
        '--hidden-import=pandas',
        '--hidden-import=sklearn',
        '--hidden-import=xgboost',
        
        # 强制收集关键模块
        '--collect-all=xgboost',
        '--collect-all=sklearn',
        
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

def build_exe_detailed(pyinstaller_cmd):
    """详细的构建方法"""
    print("开始构建可执行文件（详细版）...")
    
    cmd = pyinstaller_cmd + [
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
        
        # 数据处理
        '--hidden-import=numpy',
        '--hidden-import=pandas',
        
        # 机器学习 - 详细导入
        '--hidden-import=sklearn',
        '--hidden-import=sklearn.ensemble',
        '--hidden-import=sklearn.tree',
        '--hidden-import=sklearn.model_selection',
        '--hidden-import=sklearn.preprocessing',
        '--hidden-import=sklearn.metrics',
        '--hidden-import=sklearn.utils',
        '--hidden-import=sklearn.base',
        '--hidden-import=sklearn.exceptions',
        
        # xgboost - 详细导入
        '--hidden-import=xgboost',
        '--hidden-import=xgboost.sklearn',
        '--hidden-import=xgboost.core',
        '--hidden-import=xgboost.training',
        '--hidden-import=xgboost.callback',
        '--hidden-import=xgboost.compat',
        '--hidden-import=xgboost.libpath',
        
        # 标准库
        '--hidden-import=threading',
        '--hidden-import=json',
        '--hidden-import=datetime',
        '--hidden-import=pathlib',
        '--hidden-import=time',
        '--hidden-import=signal',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--hidden-import=traceback',
        
        # 强制收集所有相关模块
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
        '--exclude-module=tkinter',
        
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

def build_exe_onedir(pyinstaller_cmd):
    """使用--onedir模式构建（更容易调试）"""
    print("开始构建可执行文件（目录模式）...")
    
    cmd = pyinstaller_cmd + [
        '--onedir',                     # 目录模式
        '--windowed',                   # 无控制台窗口
        '--name=UserBehaviorMonitor',   # 可执行文件名
        '--add-data=src/utils/config;src/utils/config',  # 配置文件
        
        # 核心依赖
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32gui',
        '--hidden-import=win32service',
        '--hidden-import=win32serviceutil',
        '--hidden-import=pynput',
        '--hidden-import=psutil',
        '--hidden-import=keyboard',
        '--hidden-import=yaml',
        '--hidden-import=numpy',
        '--hidden-import=pandas',
        '--hidden-import=sklearn',
        '--hidden-import=xgboost',
        
        # 强制收集关键模块
        '--collect-all=xgboost',
        '--collect-all=sklearn',
        
        'user_behavior_monitor.py'
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功!")
        print(result.stdout)
        print("注意: 这是目录模式，可执行文件在 dist/UserBehaviorMonitor/ 目录中")
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("简化版xgboost修复打包工具")
    print("=" * 60)
    
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
            print("错误: 无法找到PyInstaller")
            return
        
        # 选择构建方式
        print("\n选择构建方式:")
        print("1. 简化版构建（推荐，快速）")
        print("2. 详细版构建（包含所有导入）")
        print("3. 目录模式构建（便于调试）")
        
        choice = input("请选择 (1/2/3): ").strip()
        
        if choice == "1":
            success = build_exe_simple(pyinstaller_cmd)
        elif choice == "2":
            success = build_exe_detailed(pyinstaller_cmd)
        elif choice == "3":
            success = build_exe_onedir(pyinstaller_cmd)
        else:
            print("无效选择，使用简化版构建")
            success = build_exe_simple(pyinstaller_cmd)
        
        if success:
            print("\n🎉 打包完成!")
            if choice == "3":
                print("可执行文件位置: dist/UserBehaviorMonitor/UserBehaviorMonitor.exe")
                print("注意: 这是目录模式，包含所有依赖文件")
            else:
                print("可执行文件位置: dist/UserBehaviorMonitor.exe")
            
            print("\n如果仍有xgboost问题，请尝试:")
            print("1. 重新安装xgboost: pip install --force-reinstall xgboost")
            print("2. 使用conda环境: conda install xgboost")
            print("3. 检查Python版本兼容性")
            print("4. 尝试目录模式构建（选项3）")
        else:
            print("\n❌ 打包失败!")
        
    except Exception as e:
        print(f"打包过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 
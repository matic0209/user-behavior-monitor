#!/usr/bin/env python3
"""
简化构建脚本
避免spec文件问题，直接使用命令行参数
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def find_pyinstaller():
    """查找pyinstaller命令"""
    try:
        # 方法1: 直接查找pyinstaller命令
        result = subprocess.run(['pyinstaller', '--version'], 
                             capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ 找到PyInstaller: {result.stdout.strip()}")
            return 'pyinstaller'
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    try:
        # 方法2: 使用python -m pyinstaller
        result = subprocess.run([sys.executable, '-m', 'pyinstaller', '--version'], 
                             capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ 找到PyInstaller: {result.stdout.strip()}")
            return [sys.executable, '-m', 'pyinstaller']
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("✗ 找不到PyInstaller")
    return None

def install_pyinstaller():
    """安装PyInstaller"""
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        print("✓ PyInstaller安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ PyInstaller安装失败: {e}")
        return False

def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    for dir_name in ['build', 'dist', '__pycache__']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ 已删除 {dir_name}")
    
    # 清理spec文件
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"✓ 已删除 {spec_file.name}")

def build_exe(script_name, exe_name, pyinstaller_cmd):
    """构建可执行文件"""
    print(f"🔨 构建 {exe_name}...")
    
    cmd = pyinstaller_cmd + [
        '--onefile',
        '--console',
        f'--name={exe_name}',
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32gui',
        '--hidden-import=pynput',
        '--hidden-import=xgboost',
        '--hidden-import=sklearn',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=yaml',
        '--hidden-import=psutil',
        '--hidden-import=tkinter',
        '--add-data=src/utils/config;src/utils/config',
        '--distpath=dist',
        '--workpath=build',
        script_name
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ {exe_name} 构建成功!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {exe_name} 构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def create_installer():
    """创建安装包"""
    print("📦 创建安装包...")
    installer_dir = Path("installer")
    installer_dir.mkdir(exist_ok=True)
    
    # 复制可执行文件
    exe_files = [
        "dist/UserBehaviorMonitor.exe",
        "dist/UserBehaviorMonitorOptimized.exe"
    ]
    
    for exe_file in exe_files:
        if os.path.exists(exe_file):
            shutil.copy2(exe_file, installer_dir)
            print(f"✓ 已复制 {exe_file}")
        else:
            print(f"⚠️ 文件不存在: {exe_file}")
    
    # 创建README
    readme_file = installer_dir / "README.txt"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write("""用户行为监控系统
================

文件说明:
- UserBehaviorMonitor.exe: 标准版本
- UserBehaviorMonitorOptimized.exe: 优化版本（推荐）

使用方法:
1. 双击运行任意一个exe文件
2. 系统将自动开始工作
3. 按 Ctrl+C 退出程序

快捷键:
- 连续按 r 键4次: 重新采集和训练
- 连续按 a 键4次: 手动触发告警测试
- 连续按 q 键4次: 退出系统

注意事项:
- 首次运行需要采集数据
- 建议使用优化版本以获得更好的性能
- 如遇问题请查看控制台输出
""")
    
    print("✓ 安装包创建完成")

def main():
    """主函数"""
    print("简化构建工具")
    print("=" * 30)
    
    # 检查操作系统
    if sys.platform != 'win32':
        print("❌ 错误: 此脚本只能在Windows系统上运行")
        return False
    
    try:
        # 清理构建目录
        clean_build()
        
        # 查找PyInstaller
        pyinstaller_cmd = find_pyinstaller()
        if not pyinstaller_cmd:
            print("尝试安装PyInstaller...")
            if install_pyinstaller():
                pyinstaller_cmd = find_pyinstaller()
                if not pyinstaller_cmd:
                    print("❌ 无法找到PyInstaller")
                    return False
            else:
                print("❌ PyInstaller安装失败")
                return False
        
        # 构建主程序
        if not build_exe('user_behavior_monitor.py', 'UserBehaviorMonitor', pyinstaller_cmd):
            return False
        
        # 构建优化版本
        if not build_exe('user_behavior_monitor_optimized.py', 'UserBehaviorMonitorOptimized', pyinstaller_cmd):
            return False
        
        # 创建安装包
        create_installer()
        
        print("\n" + "=" * 30)
        print("✅ 构建完成!")
        print("=" * 30)
        print("📁 可执行文件位置: dist/")
        print("📦 安装包位置: installer/")
        print("\n📋 下一步:")
        print("1. 测试 dist/UserBehaviorMonitor.exe")
        print("2. 测试 dist/UserBehaviorMonitorOptimized.exe")
        print("3. 复制 installer/ 目录到目标机器")
        
        return True
        
    except Exception as e:
        print(f"❌ 构建过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎉 构建成功完成!")
    else:
        print("\n❌ 构建失败!") 
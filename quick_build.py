#!/usr/bin/env python3
"""
快速打包脚本
简化版本，专门用于快速构建exe文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """主函数"""
    print("快速打包工具")
    print("=" * 30)
    
    # 检查操作系统
    if sys.platform != 'win32':
        print("[ERROR] 此脚本只能在Windows系统上运行")
        return False
    
    try:
        # 清理构建目录
        print("[CLEAN] 清理构建目录...")
        for dir_name in ['build', 'dist', '__pycache__']:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                print(f"[OK] 已删除 {dir_name}")
        
        # 安装PyInstaller
        print("[PKG] 安装PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        print("[OK] PyInstaller安装完成")
        
        # 查找pyinstaller命令
        def find_pyinstaller():
            try:
                # 方法1: 直接查找pyinstaller命令
                result = subprocess.run(['pyinstaller', '--version'], 
                                     capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"[OK] 找到PyInstaller: {result.stdout.strip()}")
                    return ['pyinstaller']
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            try:
                # 方法2: 使用python -m pyinstaller
                result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                                     capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"[OK] 找到PyInstaller: {result.stdout.strip()}")
                    return [sys.executable, '-m', 'PyInstaller']
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            try:
                # 方法3: 使用python -m pyinstaller (小写)
                result = subprocess.run([sys.executable, '-m', 'pyinstaller', '--version'], 
                                     capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"[OK] 找到PyInstaller: {result.stdout.strip()}")
                    return [sys.executable, '-m', 'pyinstaller']
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            print("[ERROR] 找不到PyInstaller")
            return None
        
        pyinstaller_cmd = find_pyinstaller()
        if not pyinstaller_cmd:
            print("[ERROR] 找不到PyInstaller，请确保已正确安装")
            return False
        
        # 构建主程序
        print("[BUILD] 构建主程序...")
        cmd = pyinstaller_cmd + [
            '--onefile',
            '--console',
            '--name=UserBehaviorMonitor',
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
            'user_behavior_monitor.py'
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        print("[OK] 主程序构建完成")
        
        # 构建优化版本
        print("[BUILD] 构建优化版本...")
        cmd_optimized = pyinstaller_cmd + [
            '--onefile',
            '--console',
            '--name=UserBehaviorMonitorOptimized',
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
            'user_behavior_monitor_optimized.py'
        ]
        
        print(f"执行命令: {' '.join(cmd_optimized)}")
        result = subprocess.run(cmd_optimized, check=True)
        print("[OK] 优化版本构建完成")
        
        # 创建简单的安装包
        print("[PKG] 创建安装包...")
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
                print(f"[OK] 已复制 {exe_file}")
        
        # 复制数据库
        try:
            src_db = Path('data') / 'mouse_data.db'
            if src_db.exists():
                (installer_dir / 'data').mkdir(exist_ok=True)
                shutil.copy2(src_db, installer_dir / 'data' / 'mouse_data.db')
                print("[OK] 已复制数据库到安装包: installer/data/mouse_data.db")
            else:
                print("[WARN] 未找到 data/mouse_data.db，安装包不包含数据库")
        except Exception as e:
            print(f"[WARN] 复制数据库到安装包失败: {e}")

        # 创建简单的README
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
        
        print("[OK] 安装包创建完成")
        
        print("\n" + "=" * 30)
        print("[SUCCESS] 构建完成!")
        print("=" * 30)
        print("[PATH] 可执行文件位置: dist/")
        print("[PATH] 安装包位置: installer/")
        print("\n[TODO] 下一步:")
        print("1. 测试 dist/UserBehaviorMonitor.exe")
        print("2. 测试 dist/UserBehaviorMonitorOptimized.exe")
        print("3. 复制 installer/ 目录到目标机器")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 构建失败: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 构建过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n[DONE] 构建成功完成!")
    else:
        print("\n[ERROR] 构建失败!")
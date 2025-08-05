#!/usr/bin/env python3
"""
PyInstaller打包脚本
将用户行为监控系统打包为Windows可执行文件
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

def install_dependencies():
    """安装打包依赖"""
    print("安装打包依赖...")
    
    dependencies = [
        'pyinstaller',
        'pywin32',
        'pynput',
        'xgboost',
        'scikit-learn',
        'pandas',
        'numpy',
        'pyyaml'
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                         check=True, capture_output=True)
            print(f"已安装 {dep}")
        except subprocess.CalledProcessError as e:
            print(f"安装 {dep} 失败: {e}")
    
    # 检查PyInstaller是否可用
    try:
        result = subprocess.run(['pyinstaller', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"PyInstaller版本: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("警告: PyInstaller命令不可用，尝试使用python -m PyInstaller")
        # 测试python -m PyInstaller是否可用
        try:
            result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"PyInstaller模块版本: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"错误: PyInstaller模块也不可用: {e}")
            return False
    return True

def build_exe():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 检查PyInstaller命令是否可用
    pyinstaller_cmd = ['pyinstaller']
    try:
        subprocess.run(['pyinstaller', '--version'], 
                      capture_output=True, check=True)
        print("使用pyinstaller命令")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("pyinstaller命令不可用，尝试使用python -m PyInstaller")
        pyinstaller_cmd = [sys.executable, '-m', 'PyInstaller']
    
    # PyInstaller命令
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
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    
    return True

def build_service_exe():
    """构建服务可执行文件"""
    print("构建Windows服务可执行文件...")
    
    # 检查PyInstaller命令是否可用
    pyinstaller_cmd = ['pyinstaller']
    try:
        subprocess.run(['pyinstaller', '--version'], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pyinstaller_cmd = [sys.executable, '-m', 'PyInstaller']
    
    cmd = pyinstaller_cmd + [
        '--onefile',
        '--name=UserBehaviorMonitorService',
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32gui',
        '--hidden-import=win32service',
        '--hidden-import=win32serviceutil',
        '--hidden-import=win32event',
        '--hidden-import=servicemanager',
        'windows_service.py'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("服务构建成功!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"服务构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    
    return True

def create_installer():
    """创建安装包"""
    print("创建安装包...")
    
    # 创建安装目录
    installer_dir = Path("installer")
    installer_dir.mkdir(exist_ok=True)
    
    # 复制可执行文件
    exe_files = [
        "dist/UserBehaviorMonitor.exe",
        "dist/UserBehaviorMonitorService.exe"
    ]
    
    for exe_file in exe_files:
        if os.path.exists(exe_file):
            shutil.copy2(exe_file, installer_dir)
            print(f"已复制 {exe_file}")
    
    # 创建安装脚本
    install_script = installer_dir / "install.bat"
    with open(install_script, 'w', encoding='utf-8') as f:
        f.write("""@echo off
echo 用户行为监控系统安装程序
echo ========================

echo 正在安装服务...
UserBehaviorMonitorService.exe install

echo 正在启动服务...
UserBehaviorMonitorService.exe start

echo 安装完成!
echo 系统将在后台运行，按任意键退出...
pause
""")
    
    # 创建卸载脚本
    uninstall_script = installer_dir / "uninstall.bat"
    with open(uninstall_script, 'w', encoding='utf-8') as f:
        f.write("""@echo off
echo 用户行为监控系统卸载程序
echo ========================

echo 正在停止服务...
UserBehaviorMonitorService.exe stop

echo 正在卸载服务...
UserBehaviorMonitorService.exe remove

echo 卸载完成!
pause
""")
    
    # 创建README
    readme_file = installer_dir / "README.txt"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write("""用户行为监控系统
================

功能说明:
- 自动采集用户行为数据
- 基于机器学习进行异常检测
- 检测到异常时自动锁屏保护
- 支持手动触发告警测试

安装说明:
1. 以管理员身份运行 install.bat
2. 系统将自动安装并启动服务
3. 服务将在后台运行，无需用户干预

卸载说明:
1. 以管理员身份运行 uninstall.bat
2. 系统将停止并卸载服务

快捷键:
- 连续按 r 键4次: 重新采集和训练模型
- 连续按 a 键4次: 手动触发告警测试
- 连续按 q 键4次: 退出系统

日志文件位置:
- logs/user_behavior_monitor.log
- logs/windows_service.log

注意事项:
- 首次运行需要采集足够的数据才能开始检测
- 系统会自动在后台运行，无需手动启动
- 如遇问题请查看日志文件
""")
    
    print("安装包创建完成!")

def main():
    """主函数"""
    print("用户行为监控系统打包工具")
    print("=" * 30)
    
    # 检查操作系统
    if sys.platform != 'win32':
        print("错误: 此脚本只能在Windows系统上运行")
        return
    
    try:
        # 清理构建目录
        clean_build()
        
        # 安装依赖
        install_dependencies()
        
        # 构建主程序
        if build_exe():
            print("主程序构建成功!")
        else:
            print("主程序构建失败!")
            return
        
        # 构建服务程序
        if build_service_exe():
            print("服务程序构建成功!")
        else:
            print("服务程序构建失败!")
            return
        
        # 创建安装包
        create_installer()
        
        print("\n打包完成!")
        print("可执行文件位置: dist/")
        print("安装包位置: installer/")
        
    except Exception as e:
        print(f"打包过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 
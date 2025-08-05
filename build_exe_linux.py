#!/usr/bin/env python3
"""
PyInstaller打包脚本 - Linux版本
将用户行为监控系统打包为可执行文件
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
        'pynput',
        'xgboost',
        'scikit-learn',
        'pandas',
        'numpy',
        'pyyaml',
        'psutil',
        'matplotlib',
        'seaborn',
        'imbalanced-learn',
        'joblib',
        'scipy'
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                         check=True, capture_output=True)
            print(f"已安装 {dep}")
        except subprocess.CalledProcessError as e:
            print(f"安装 {dep} 失败: {e}")

def build_exe():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # PyInstaller命令
    cmd = [
        'pyinstaller',
        '--onefile',                    # 单文件
        '--name=UserBehaviorMonitor',   # 可执行文件名
        '--add-data=src/utils/config:src/utils/config',  # 配置文件
        '--hidden-import=pynput',
        '--hidden-import=xgboost',
        '--hidden-import=sklearn',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=yaml',
        '--hidden-import=psutil',
        '--hidden-import=matplotlib',
        '--hidden-import=seaborn',
        '--hidden-import=imblearn',
        '--hidden-import=joblib',
        '--hidden-import=scipy',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.ttk',
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

def build_optimized_exe():
    """构建优化版本的可执行文件"""
    print("构建优化版本的可执行文件...")
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--name=UserBehaviorMonitorOptimized',
        '--add-data=src/utils/config:src/utils/config',
        '--hidden-import=pynput',
        '--hidden-import=xgboost',
        '--hidden-import=sklearn',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=yaml',
        '--hidden-import=psutil',
        '--hidden-import=matplotlib',
        '--hidden-import=seaborn',
        '--hidden-import=imblearn',
        '--hidden-import=joblib',
        '--hidden-import=scipy',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.ttk',
        'user_behavior_monitor_optimized.py'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("优化版本构建成功!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"优化版本构建失败: {e}")
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
        "dist/UserBehaviorMonitor",
        "dist/UserBehaviorMonitorOptimized"
    ]
    
    for exe_file in exe_files:
        if os.path.exists(exe_file):
            shutil.copy2(exe_file, installer_dir)
            print(f"已复制 {exe_file}")
    
    # 创建安装脚本
    install_script = installer_dir / "install.sh"
    with open(install_script, 'w', encoding='utf-8') as f:
        f.write("""#!/bin/bash
echo "用户行为监控系统安装程序"
echo "========================"

echo "正在设置权限..."
chmod +x UserBehaviorMonitor
chmod +x UserBehaviorMonitorOptimized

echo "安装完成!"
echo "使用方法:"
echo "  ./UserBehaviorMonitor          # 运行标准版本"
echo "  ./UserBehaviorMonitorOptimized # 运行优化版本"
""")
    
    # 设置安装脚本权限
    os.chmod(install_script, 0o755)
    
    # 创建README
    readme_file = installer_dir / "README.txt"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write("""用户行为监控系统 - Linux版本
========================

功能说明:
- 自动采集用户行为数据
- 基于机器学习进行异常检测
- 检测到异常时自动锁屏保护
- 支持手动触发告警测试

安装说明:
1. 解压安装包
2. 运行 ./install.sh 设置权限
3. 运行 ./UserBehaviorMonitor 启动系统

使用方法:
- ./UserBehaviorMonitor          # 运行标准版本
- ./UserBehaviorMonitorOptimized # 运行优化版本

快捷键:
- 连续按 r 键4次: 重新采集和训练模型
- 连续按 a 键4次: 手动触发告警测试
- 连续按 q 键4次: 退出系统

日志文件位置:
- logs/user_behavior_monitor.log

注意事项:
- 首次运行需要采集足够的数据才能开始检测
- 系统会自动在后台运行，无需手动启动
- 如遇问题请查看日志文件
- 确保系统已安装必要的依赖库
""")
    
    print("安装包创建完成!")

def main():
    """主函数"""
    print("用户行为监控系统打包工具 - Linux版本")
    print("=" * 40)
    
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
        
        # 构建优化版本
        if build_optimized_exe():
            print("优化版本构建成功!")
        else:
            print("优化版本构建失败!")
            return
        
        # 创建安装包
        create_installer()
        
        print("\n打包完成!")
        print("可执行文件位置: dist/")
        print("安装包位置: installer/")
        print("\n使用方法:")
        print("  cd installer")
        print("  ./install.sh")
        print("  ./UserBehaviorMonitor")
        
    except Exception as e:
        print(f"打包过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 
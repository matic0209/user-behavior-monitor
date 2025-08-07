#!/usr/bin/env python3
"""
Windows环境依赖安装脚本
"""

import subprocess
import sys
import os

def install_dependencies():
    """安装所有必要的依赖"""
    print("Windows环境依赖安装脚本")
    print("=" * 40)
    
    # 需要安装的依赖列表
    dependencies = [
        'psutil',
        'pynput', 
        'keyboard',
        'pyyaml',
        'numpy',
        'pandas',
        'scikit-learn',
        'xgboost',
        'pywin32',  # Windows API支持
        'pyinstaller'
    ]
    
    print("开始安装依赖...")
    
    for dep in dependencies:
        print(f"正在安装 {dep}...")
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', dep
            ], check=True, capture_output=True, text=True)
            print(f"[SUCCESS] {dep} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] {dep} 安装失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False
    
    print("\n[SUCCESS] 所有依赖安装完成!")
    return True

def verify_installations():
    """验证安装"""
    print("\n验证安装...")
    
    test_imports = [
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
        'win32gui'
    ]
    
    failed_imports = []
    
    for module in test_imports:
        try:
            __import__(module)
            print(f"[SUCCESS] {module} 导入成功")
        except ImportError as e:
            print(f"[ERROR] {module} 导入失败: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n[WARNING] 以下模块导入失败: {failed_imports}")
        return False
    else:
        print("\n[SUCCESS] 所有模块导入成功!")
        return True

def main():
    """主函数"""
    print("Windows环境依赖安装和验证")
    print("=" * 50)
    
    # 安装依赖
    if not install_dependencies():
        print("\n[ERROR] 依赖安装失败，请检查网络连接和权限")
        return
    
    # 验证安装
    if not verify_installations():
        print("\n[WARNING] 部分模块可能未正确安装")
        print("请尝试手动安装失败的模块")
    
    print("\n" + "=" * 50)
    print("[SUCCESS] 依赖安装完成!")
    print("[TIP] 现在可以运行构建脚本:")
    print("    python build_safe.py")
    print("    python build_cross_platform.py")
    print("=" * 50)

if __name__ == "__main__":
    main()

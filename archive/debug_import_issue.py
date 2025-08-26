#!/usr/bin/env python3
"""
调试导入问题的脚本
用于诊断为什么quick_install成功但start_monitor仍然报缺失包的问题
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_environment():
    """检查Python环境"""
    print("=== Python环境检查 ===")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"Python路径列表: {sys.path}")
    
    # 检查是否在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"是否在虚拟环境中: {in_venv}")
    if in_venv:
        print(f"虚拟环境路径: {sys.prefix}")
    
    print()

def check_pip_installations():
    """检查pip安装的包"""
    print("=== pip安装检查 ===")
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                              capture_output=True, text=True, check=True)
        print("已安装的包:")
        for line in result.stdout.split('\n'):
            if any(pkg in line.lower() for pkg in ['scikit-learn', 'pyyaml', 'sklearn', 'yaml']):
                print(f"  {line}")
    except Exception as e:
        print(f"检查pip安装失败: {e}")
    
    print()

def check_import_attempts():
    """尝试导入包并显示详细信息"""
    print("=== 导入测试 ===")
    
    packages = [
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('scikit-learn', 'sklearn'),
        ('xgboost', 'xgboost'),
        ('scipy', 'scipy'),
        ('psutil', 'psutil'),
        ('matplotlib', 'matplotlib'),
        ('joblib', 'joblib'),
        ('pyyaml', 'yaml'),
        ('pynput', 'pynput')
    ]
    
    for package_name, import_name in packages:
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'unknown')
            location = getattr(module, '__file__', 'unknown')
            print(f"✓ {package_name}: 版本={version}, 位置={location}")
        except ImportError as e:
            print(f"✗ {package_name}: 导入失败 - {e}")
        except Exception as e:
            print(f"? {package_name}: 其他错误 - {e}")
    
    print()

def check_requirements_consistency():
    """检查requirements.txt与实际安装的一致性"""
    print("=== requirements.txt检查 ===")
    
    requirements_file = Path('requirements.txt')
    if requirements_file.exists():
        print("requirements.txt内容:")
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        print(f"  {line}")
        except UnicodeDecodeError:
            try:
                with open(requirements_file, 'r', encoding='gbk') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            print(f"  {line}")
            except UnicodeDecodeError:
                print("  - 文件编码问题，无法读取内容")
        except Exception as e:
            print(f"  - 读取文件失败: {e}")
    else:
        print("requirements.txt文件不存在")
    
    print()

def check_quick_install_script():
    """检查quick_install.py脚本"""
    print("=== quick_install.py检查 ===")
    
    quick_install_file = Path('quick_install.py')
    if quick_install_file.exists():
        print("quick_install.py存在")
        # 显示关键部分
        try:
            with open(quick_install_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'scikit-learn' in content:
                    print("  - 包含scikit-learn安装")
                if 'pyyaml' in content:
                    print("  - 包含pyyaml安装")
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试其他编码
            try:
                with open(quick_install_file, 'r', encoding='gbk') as f:
                    content = f.read()
                    if 'scikit-learn' in content:
                        print("  - 包含scikit-learn安装")
                    if 'pyyaml' in content:
                        print("  - 包含pyyaml安装")
            except UnicodeDecodeError:
                print("  - 文件编码问题，无法读取内容")
        except Exception as e:
            print(f"  - 读取文件失败: {e}")
    else:
        print("quick_install.py不存在")
    
    print()

def check_start_monitor_script():
    """检查start_monitor.py脚本"""
    print("=== start_monitor.py检查 ===")
    
    start_monitor_file = Path('start_monitor.py')
    if start_monitor_file.exists():
        print("start_monitor.py存在")
        # 显示依赖检查部分
        try:
            with open(start_monitor_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'required_packages' in content:
                    print("  - 包含required_packages列表")
                    # 提取包列表
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'required_packages' in line:
                            print(f"    行 {i+1}: {line.strip()}")
                            # 显示接下来的几行
                            for j in range(i+1, min(i+15, len(lines))):
                                if ']' in lines[j]:
                                    print(f"    行 {j+1}: {lines[j].strip()}")
                                    break
                                elif lines[j].strip() and not lines[j].strip().startswith('#'):
                                    print(f"    行 {j+1}: {lines[j].strip()}")
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试其他编码
            try:
                with open(start_monitor_file, 'r', encoding='gbk') as f:
                    content = f.read()
                    if 'required_packages' in content:
                        print("  - 包含required_packages列表")
            except UnicodeDecodeError:
                print("  - 文件编码问题，无法读取内容")
        except Exception as e:
            print(f"  - 读取文件失败: {e}")
    else:
        print("start_monitor.py不存在")
    
    print()

def run_quick_install_test():
    """运行quick_install测试"""
    print("=== 运行quick_install测试 ===")
    
    try:
        result = subprocess.run([sys.executable, "quick_install.py"], 
                              capture_output=True, text=True, timeout=60)
        print("quick_install.py输出:")
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("quick_install.py运行超时")
    except Exception as e:
        print(f"运行quick_install.py失败: {e}")
    
    print()

def run_start_monitor_test():
    """运行start_monitor测试"""
    print("=== 运行start_monitor测试 ===")
    
    try:
        result = subprocess.run([sys.executable, "start_monitor.py"], 
                              capture_output=True, text=True, timeout=30)
        print("start_monitor.py输出:")
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("start_monitor.py运行超时")
    except Exception as e:
        print(f"运行start_monitor.py失败: {e}")
    
    print()

def main():
    """主函数"""
    print("=" * 60)
    print("导入问题诊断工具")
    print("=" * 60)
    print()
    
    # 检查Python环境
    check_python_environment()
    
    # 检查pip安装
    check_pip_installations()
    
    # 检查导入
    check_import_attempts()
    
    # 检查requirements.txt
    check_requirements_consistency()
    
    # 检查脚本
    check_quick_install_script()
    check_start_monitor_script()
    
    # 运行测试
    run_quick_install_test()
    run_start_monitor_test()
    
    print("=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    main() 
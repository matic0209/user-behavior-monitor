#!/usr/bin/env python3
"""
依赖安装和故障排除脚本
用于解决Windows环境下的依赖安装问题
"""

import sys
import subprocess
import os
import platform
from pathlib import Path

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"\n=== {description} ===")
    print(f"执行命令: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ 命令执行成功")
            if result.stdout:
                print("输出:", result.stdout.strip())
        else:
            print("✗ 命令执行失败")
            if result.stderr:
                print("错误:", result.stderr.strip())
        return result.returncode == 0
    except Exception as e:
        print(f"✗ 命令执行异常: {e}")
        return False

def check_python_version():
    """检查Python版本"""
    print("=== 检查Python版本 ===")
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 7):
        print("✗ Python版本过低，建议使用3.7或更高版本")
        return False
    else:
        print("✓ Python版本符合要求")
        return True

def check_pip():
    """检查pip"""
    print("=== 检查pip ===")
    try:
        import pip
        print(f"✓ pip版本: {pip.__version__}")
        return True
    except ImportError:
        print("✗ pip未安装")
        return False

def upgrade_pip():
    """升级pip"""
    return run_command("python -m pip install --upgrade pip", "升级pip")

def install_package(package, description=None):
    """安装单个包"""
    if description is None:
        description = f"安装{package}"
    
    # 尝试不同的安装方法
    methods = [
        f"pip install {package}",
        f"python -m pip install {package}",
        f"pip install --user {package}",
        f"python -m pip install --user {package}"
    ]
    
    for method in methods:
        if run_command(method, description):
            return True
    
    return False

def install_from_requirements():
    """从requirements.txt安装依赖"""
    return run_command("pip install -r requirements.txt", "从requirements.txt安装依赖")

def install_windows_specific():
    """安装Windows特定依赖"""
    if platform.system() == "Windows":
        return run_command("pip install pywin32", "安装Windows API (pywin32)")
    else:
        print("非Windows系统，跳过Windows特定依赖")
        return True

def check_installed_packages():
    """检查已安装的包"""
    print("=== 检查已安装的包 ===")
    
    required_packages = [
        'numpy',
        'pandas', 
        'scikit-learn',
        'xgboost',
        'scipy',
        'psutil',
        'matplotlib',
        'joblib',
        'pyyaml',
        'pynput'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {package} (版本: {version})")
        except ImportError:
            print(f"✗ {package} (缺失)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n缺失的包: {', '.join(missing_packages)}")
        return False
    else:
        print("\n✓ 所有必需的包都已安装")
        return True

def create_virtual_environment():
    """创建虚拟环境"""
    print("=== 创建虚拟环境 ===")
    
    venv_name = "venv"
    if os.path.exists(venv_name):
        print(f"虚拟环境 {venv_name} 已存在")
        return True
    
    # 尝试创建虚拟环境
    methods = [
        f"python -m venv {venv_name}",
        f"python -m virtualenv {venv_name}",
        f"virtualenv {venv_name}"
    ]
    
    for method in methods:
        if run_command(method, f"创建虚拟环境 ({method})"):
            return True
    
    return False

def activate_virtual_environment():
    """激活虚拟环境"""
    print("=== 激活虚拟环境 ===")
    
    if platform.system() == "Windows":
        activate_script = "venv\\Scripts\\activate"
    else:
        activate_script = "venv/bin/activate"
    
    if os.path.exists(activate_script):
        print(f"虚拟环境激活脚本: {activate_script}")
        print("请手动激活虚拟环境:")
        if platform.system() == "Windows":
            print(f"  {activate_script}")
        else:
            print(f"  source {activate_script}")
        return True
    else:
        print("✗ 虚拟环境激活脚本不存在")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("依赖安装和故障排除工具")
    print("=" * 60)
    print()
    
    # 检查Python版本
    if not check_python_version():
        print("\n请升级Python版本后再试")
        return 1
    
    # 检查pip
    if not check_pip():
        print("\n请先安装pip")
        return 1
    
    # 升级pip
    upgrade_pip()
    
    # 检查是否在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✓ 当前在虚拟环境中")
    else:
        print("⚠ 当前不在虚拟环境中")
        print("建议创建并使用虚拟环境:")
        if create_virtual_environment():
            activate_virtual_environment()
            print("\n请激活虚拟环境后重新运行此脚本")
            return 1
    
    # 尝试安装依赖
    print("\n=== 安装依赖包 ===")
    
    # 首先尝试从requirements.txt安装
    if install_from_requirements():
        print("✓ 从requirements.txt安装成功")
    else:
        print("✗ 从requirements.txt安装失败，尝试单独安装")
        
        # 单独安装每个包
        packages = [
            ("numpy", "NumPy"),
            ("pandas", "Pandas"),
            ("scikit-learn", "Scikit-learn"),
            ("xgboost", "XGBoost"),
            ("scipy", "SciPy"),
            ("psutil", "psutil"),
            ("matplotlib", "Matplotlib"),
            ("joblib", "Joblib"),
            ("pyyaml", "PyYAML"),
            ("pynput", "pynput")
        ]
        
        for package, description in packages:
            install_package(package, f"安装{description}")
    
    # 安装Windows特定依赖
    install_windows_specific()
    
    # 检查安装结果
    print("\n=== 最终检查 ===")
    if check_installed_packages():
        print("\n✓ 所有依赖安装完成！")
        print("\n现在可以运行:")
        print("  python test_debug_logging.py")
        print("  python start_monitor.py")
        return 0
    else:
        print("\n✗ 仍有依赖未安装完成")
        print("\n故障排除建议:")
        print("1. 确保网络连接正常")
        print("2. 尝试使用国内镜像源:")
        print("   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt")
        print("3. 检查Python和pip版本兼容性")
        print("4. 尝试以管理员权限运行")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
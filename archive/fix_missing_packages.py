#!/usr/bin/env python3
"""
专门解决缺失包安装问题的脚本
针对 scikit-learn 和 pyyaml 的安装问题
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

def install_scikit_learn():
    """专门安装scikit-learn"""
    print("=== 专门安装scikit-learn ===")
    
    # 尝试不同的安装方法
    methods = [
        # 使用国内镜像源
        "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple scikit-learn",
        "pip install -i https://pypi.douban.com/simple scikit-learn",
        "pip install -i https://mirrors.aliyun.com/pypi/simple scikit-learn",
        
        # 使用用户安装
        "pip install --user scikit-learn",
        "python -m pip install --user scikit-learn",
        
        # 指定版本
        "pip install scikit-learn==1.3.0",
        "pip install --user scikit-learn==1.3.0",
        
        # 使用conda（如果可用）
        "conda install scikit-learn -y",
        
        # 最后尝试默认源
        "pip install scikit-learn",
        "python -m pip install scikit-learn"
    ]
    
    for method in methods:
        if run_command(method, f"尝试安装scikit-learn ({method})"):
            return True
    
    return False

def install_pyyaml():
    """专门安装pyyaml"""
    print("=== 专门安装pyyaml ===")
    
    # 尝试不同的安装方法
    methods = [
        # 使用国内镜像源
        "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyyaml",
        "pip install -i https://pypi.douban.com/simple pyyaml",
        "pip install -i https://mirrors.aliyun.com/pypi/simple pyyaml",
        
        # 使用用户安装
        "pip install --user pyyaml",
        "python -m pip install --user pyyaml",
        
        # 指定版本
        "pip install pyyaml==6.0",
        "pip install --user pyyaml==6.0",
        
        # 使用conda（如果可用）
        "conda install pyyaml -y",
        
        # 最后尝试默认源
        "pip install pyyaml",
        "python -m pip install pyyaml"
    ]
    
    for method in methods:
        if run_command(method, f"尝试安装pyyaml ({method})"):
            return True
    
    return False

def check_conda():
    """检查conda是否可用"""
    print("=== 检查conda ===")
    try:
        result = subprocess.run("conda --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ conda可用: {result.stdout.strip()}")
            return True
        else:
            print("✗ conda不可用")
            return False
    except:
        print("✗ conda不可用")
        return False

def install_with_conda():
    """使用conda安装缺失的包"""
    print("=== 使用conda安装缺失的包 ===")
    
    if not check_conda():
        print("conda不可用，跳过conda安装")
        return False
    
    success = True
    
    # 尝试使用conda安装scikit-learn
    if not run_command("conda install scikit-learn -y", "使用conda安装scikit-learn"):
        success = False
    
    # 尝试使用conda安装pyyaml
    if not run_command("conda install pyyaml -y", "使用conda安装pyyaml"):
        success = False
    
    return success

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
        return False, missing_packages
    else:
        print("\n✓ 所有必需的包都已安装")
        return True, []

def upgrade_pip():
    """升级pip"""
    print("=== 升级pip ===")
    
    methods = [
        "python -m pip install --upgrade pip",
        "pip install --upgrade pip",
        "python -m pip install --user --upgrade pip"
    ]
    
    for method in methods:
        if run_command(method, f"升级pip ({method})"):
            return True
    
    return False

def install_wheel():
    """安装wheel包（可能有助于解决编译问题）"""
    print("=== 安装wheel包 ===")
    
    methods = [
        "pip install wheel",
        "pip install --user wheel",
        "python -m pip install wheel",
        "python -m pip install --user wheel"
    ]
    
    for method in methods:
        if run_command(method, f"安装wheel ({method})"):
            return True
    
    return False

def install_compiler_tools():
    """安装编译工具（Windows）"""
    if platform.system() == "Windows":
        print("=== 安装Windows编译工具 ===")
        
        methods = [
            "pip install microsoft-visual-cpp-build-tools",
            "pip install --user microsoft-visual-cpp-build-tools"
        ]
        
        for method in methods:
            if run_command(method, f"安装编译工具 ({method})"):
                return True
    
    return False

def main():
    """主函数"""
    print("=" * 60)
    print("缺失包安装修复工具")
    print("=" * 60)
    print()
    
    # 检查Python版本
    if not check_python_version():
        print("\n请升级Python版本后再试")
        return 1
    
    # 升级pip
    upgrade_pip()
    
    # 安装wheel包
    install_wheel()
    
    # 安装编译工具（Windows）
    install_compiler_tools()
    
    # 检查当前已安装的包
    all_installed, missing_packages = check_installed_packages()
    
    if all_installed:
        print("\n✓ 所有包都已安装完成！")
        return 0
    
    print(f"\n需要安装的包: {', '.join(missing_packages)}")
    
    # 尝试使用conda安装
    if 'conda' in missing_packages or 'scikit-learn' in missing_packages or 'pyyaml' in missing_packages:
        print("\n尝试使用conda安装...")
        if install_with_conda():
            all_installed, missing_packages = check_installed_packages()
            if all_installed:
                print("\n✓ 使用conda安装成功！")
                return 0
    
    # 专门安装scikit-learn
    if 'scikit-learn' in missing_packages:
        print("\n专门安装scikit-learn...")
        if install_scikit_learn():
            print("✓ scikit-learn安装成功")
        else:
            print("✗ scikit-learn安装失败")
    
    # 专门安装pyyaml
    if 'pyyaml' in missing_packages:
        print("\n专门安装pyyaml...")
        if install_pyyaml():
            print("✓ pyyaml安装成功")
        else:
            print("✗ pyyaml安装失败")
    
    # 最终检查
    print("\n=== 最终检查 ===")
    all_installed, missing_packages = check_installed_packages()
    
    if all_installed:
        print("\n✓ 所有依赖安装完成！")
        print("\n现在可以运行:")
        print("  python test_debug_logging.py")
        print("  python start_monitor.py")
        return 0
    else:
        print(f"\n✗ 仍有依赖未安装完成: {', '.join(missing_packages)}")
        print("\n最终故障排除建议:")
        print("1. 尝试以管理员权限运行此脚本")
        print("2. 检查网络连接和防火墙设置")
        print("3. 尝试使用VPN或代理")
        print("4. 手动下载wheel文件安装:")
        print("   - 访问 https://www.lfd.uci.edu/~gohlke/pythonlibs/")
        print("   - 下载对应的.whl文件")
        print("   - 使用 pip install 文件名.whl 安装")
        print("5. 考虑使用Anaconda替代pip")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
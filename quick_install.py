#!/usr/bin/env python3
"""
快速安装脚本 - 专门解决scikit-learn和pyyaml安装问题
"""

import subprocess
import sys
import os

def run_cmd(cmd):
    """运行命令"""
    print(f"执行: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✓ 成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 失败: {e.stderr}")
        return False

def main():
    print("=" * 50)
    print("快速安装缺失的包")
    print("=" * 50)
    
    # 升级pip
    print("\n1. 升级pip...")
    run_cmd("python -m pip install --upgrade pip")
    
    # 安装wheel
    print("\n2. 安装wheel...")
    run_cmd("pip install wheel")
    
    # 尝试安装scikit-learn
    print("\n3. 安装scikit-learn...")
    methods = [
        "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple scikit-learn",
        "pip install --user scikit-learn",
        "pip install scikit-learn==1.3.0",
        "pip install scikit-learn"
    ]
    
    scikit_success = False
    for method in methods:
        if run_cmd(method):
            scikit_success = True
            break
    
    # 尝试安装pyyaml
    print("\n4. 安装pyyaml...")
    methods = [
        "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyyaml",
        "pip install --user pyyaml",
        "pip install pyyaml==6.0",
        "pip install pyyaml"
    ]
    
    yaml_success = False
    for method in methods:
        if run_cmd(method):
            yaml_success = True
            break
    
    # 检查结果
    print("\n5. 检查安装结果...")
    try:
        import sklearn
        print(f"✓ scikit-learn: {sklearn.__version__}")
    except ImportError:
        print("✗ scikit-learn: 未安装")
    
    try:
        import yaml
        print(f"✓ pyyaml: {yaml.__version__}")
    except ImportError:
        print("✗ pyyaml: 未安装")
    
    if scikit_success and yaml_success:
        print("\n✓ 所有包安装成功！")
        return 0
    else:
        print("\n✗ 部分包安装失败")
        print("\n建议:")
        print("1. 以管理员权限运行")
        print("2. 使用Anaconda: conda install scikit-learn pyyaml")
        print("3. 手动下载wheel文件安装")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
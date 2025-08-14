#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能下载兼容的Python依赖包
"""

import os
import subprocess
import sys
from pathlib import Path

def get_python_version():
    """获取当前Python版本"""
    version = sys.version_info
    return f"{version.major}.{version.minor}"

def download_compatible_dependencies():
    """下载兼容的Python依赖包"""
    
    # 设置路径
    package_dir = Path("user_behavior_monitor_uos20_offline_with_python")
    wheels_dir = package_dir / "dependencies" / "wheels"
    requirements_file = package_dir / "requirements_uos20_python37.txt"
    
    if not package_dir.exists():
        print("错误: 包目录不存在")
        return False
    
    if not requirements_file.exists():
        print("错误: requirements文件不存在")
        return False
    
    # 确保wheels目录存在
    wheels_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取当前Python版本
    current_version = get_python_version()
    print(f"当前Python版本: {current_version}")
    
    # 读取requirements文件
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"需要下载 {len(requirements)} 个Python包...")
    
    # 逐个下载包
    success_count = 0
    for requirement in requirements:
        print(f"下载: {requirement}")
        
        # 尝试多种下载方式，优先使用当前Python版本
        download_methods = [
            # 方法1: 使用当前Python版本
            [
                "pip3", "download",
                "--python-version", current_version,
                "--only-binary=:all:",
                "--dest", str(wheels_dir),
                requirement
            ],
            # 方法2: 不指定版本，让pip自动选择
            [
                "pip3", "download",
                "--only-binary=:all:",
                "--dest", str(wheels_dir),
                requirement
            ],
            # 方法3: 尝试Python 3.7兼容版本
            [
                "pip3", "download",
                "--python-version", "3.7",
                "--only-binary=:all:",
                "--dest", str(wheels_dir),
                requirement
            ],
            # 方法4: 尝试Python 3.8兼容版本
            [
                "pip3", "download",
                "--python-version", "3.8",
                "--only-binary=:all:",
                "--dest", str(wheels_dir),
                requirement
            ],
            # 方法5: 尝试Python 3.9兼容版本
            [
                "pip3", "download",
                "--python-version", "3.9",
                "--only-binary=:all:",
                "--dest", str(wheels_dir),
                requirement
            ],
            # 方法6: 尝试Python 3.10兼容版本
            [
                "pip3", "download",
                "--python-version", "3.10",
                "--only-binary=:all:",
                "--dest", str(wheels_dir),
                requirement
            ],
            # 方法7: 最简单的下载
            [
                "pip3", "download",
                "--dest", str(wheels_dir),
                requirement
            ]
        ]
        
        success = False
        for i, cmd in enumerate(download_methods, 1):
            try:
                print(f"  尝试方法{i}: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"  ✓ 成功下载: {requirement}")
                success = True
                break
            except subprocess.CalledProcessError as e:
                print(f"  ✗ 方法{i}失败: {e.stderr.strip()}")
                continue
        
        if success:
            success_count += 1
        else:
            print(f"  ✗ 所有方法都失败: {requirement}")
    
    print(f"\n下载完成: {success_count}/{len(requirements)} 个包成功")
    
    # 检查下载结果
    wheel_files = list(wheels_dir.glob("*.whl"))
    print(f"Wheel文件数量: {len(wheel_files)}")
    
    if wheel_files:
        print("下载的wheel文件:")
        for wheel in wheel_files:
            size_mb = wheel.stat().st_size / (1024 * 1024)
            print(f"  {wheel.name} ({size_mb:.2f} MB)")
    
    return success_count > 0

def clean_incompatible_wheels():
    """清理不兼容的wheel文件"""
    print("清理不兼容的wheel文件...")
    
    package_dir = Path("user_behavior_monitor_uos20_offline_with_python")
    wheels_dir = package_dir / "dependencies" / "wheels"
    
    if not wheels_dir.exists():
        return
    
    # 获取当前Python版本
    current_version = get_python_version()
    major, minor = map(int, current_version.split('.'))
    
    # 要删除的不兼容版本
    incompatible_versions = []
    
    # 如果当前是Python 3.11，删除3.11的wheel (因为可能有兼容性问题)
    if major == 3 and minor == 11:
        incompatible_versions.append("cp311")
    
    # 删除不兼容的文件
    for wheel_file in wheels_dir.glob("*.whl"):
        filename = wheel_file.name
        for version in incompatible_versions:
            if version in filename:
                print(f"删除不兼容文件: {filename}")
                wheel_file.unlink()
                break

if __name__ == "__main__":
    print("开始下载兼容的Python依赖包...")
    
    # 清理不兼容的wheel文件
    clean_incompatible_wheels()
    
    # 下载兼容的依赖
    success = download_compatible_dependencies()
    
    if success:
        print("\n✓ 兼容依赖包下载完成")
    else:
        print("\n✗ 依赖包下载失败")
        sys.exit(1) 
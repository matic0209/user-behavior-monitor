#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载Python依赖包脚本
"""

import os
import subprocess
import sys
from pathlib import Path

def download_dependencies():
    """下载所有Python依赖包"""
    
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
    
    # 读取requirements文件
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"需要下载 {len(requirements)} 个Python包...")
    
    # 逐个下载包
    success_count = 0
    for requirement in requirements:
        print(f"下载: {requirement}")
        
        # 尝试多种下载方式
        download_methods = [
            # 方法1: 指定平台和版本
            [
                "pip3", "download",
                "--platform", "linux_x86_64",
                "--python-version", "3.7",
                "--only-binary=:all:",
                "--dest", str(wheels_dir),
                requirement
            ],
            # 方法2: 不指定平台，指定版本
            [
                "pip3", "download",
                "--python-version", "3.7",
                "--only-binary=:all:",
                "--dest", str(wheels_dir),
                requirement
            ],
            # 方法3: 不指定平台和版本
            [
                "pip3", "download",
                "--only-binary=:all:",
                "--dest", str(wheels_dir),
                requirement
            ],
            # 方法4: 最简单的下载
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

if __name__ == "__main__":
    success = download_dependencies()
    if success:
        print("\n✓ 依赖包下载完成")
    else:
        print("\n✗ 依赖包下载失败")
        sys.exit(1) 
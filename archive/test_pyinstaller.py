#!/usr/bin/env python3
"""
测试PyInstaller是否正常工作
"""

import sys
import subprocess
import os

def test_pyinstaller():
    """测试PyInstaller是否正常工作"""
    print("测试PyInstaller...")
    
    # 测试方法1: 直接命令
    try:
        result = subprocess.run(['pyinstaller', '--version'], 
                             capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ 方法1成功: {result.stdout.strip()}")
            return True
    except Exception as e:
        print(f"✗ 方法1失败: {e}")
    
    # 测试方法2: python -m PyInstaller
    try:
        result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                             capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ 方法2成功: {result.stdout.strip()}")
            return True
    except Exception as e:
        print(f"✗ 方法2失败: {e}")
    
    # 测试方法3: python -m pyinstaller
    try:
        result = subprocess.run([sys.executable, '-m', 'pyinstaller', '--version'], 
                             capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ 方法3成功: {result.stdout.strip()}")
            return True
    except Exception as e:
        print(f"✗ 方法3失败: {e}")
    
    return False

def install_pyinstaller():
    """安装PyInstaller"""
    print("安装PyInstaller...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        print("✓ PyInstaller安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ PyInstaller安装失败: {e}")
        return False

def main():
    """主函数"""
    print("PyInstaller测试工具")
    print("=" * 30)
    
    # 检查操作系统
    if sys.platform != 'win32':
        print("❌ 此脚本只能在Windows系统上运行")
        return False
    
    # 测试PyInstaller
    if test_pyinstaller():
        print("\n✅ PyInstaller工作正常!")
        return True
    else:
        print("\n❌ PyInstaller未找到或无法运行")
        print("尝试安装PyInstaller...")
        
        if install_pyinstaller():
            print("重新测试PyInstaller...")
            if test_pyinstaller():
                print("\n✅ PyInstaller安装并测试成功!")
                return True
            else:
                print("\n❌ PyInstaller安装后仍无法正常工作")
                return False
        else:
            print("\n❌ PyInstaller安装失败")
            return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎉 可以开始构建exe文件了!")
    else:
        print("\n💡 建议:")
        print("1. 检查Python环境是否正确安装")
        print("2. 尝试手动安装: pip install pyinstaller")
        print("3. 检查PATH环境变量是否包含Python和pip") 
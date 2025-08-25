#!/usr/bin/env python3
"""
安装pyautogui依赖的脚本
用于Windows Git Bash环境下的测试脚本
"""

import sys
import subprocess
import importlib.util

def check_module(module_name):
    """检查模块是否已安装"""
    spec = importlib.util.find_spec(module_name)
    return spec is not None

def install_module(module_name):
    """安装模块"""
    try:
        print(f"正在安装 {module_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
        print(f"[OK] {module_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {module_name} 安装失败: {e}")
        return False

def main():
    print("检查和安装测试脚本依赖...")
    print("=" * 40)
    
    modules_to_check = ["pyautogui", "pillow"]
    missing_modules = []
    
    # 检查依赖
    for module in modules_to_check:
        if check_module(module):
            print(f"[OK] {module} 已安装")
        else:
            print(f"[MISSING] {module} 未安装")
            missing_modules.append(module)
    
    if not missing_modules:
        print("\n[SUCCESS] 所有依赖都已安装！")
        
        # 测试pyautogui功能
        print("\n测试pyautogui功能...")
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            width, height = pyautogui.size()
            print(f"[OK] 屏幕分辨率: {width}x{height}")
            print("[OK] pyautogui功能正常")
        except Exception as e:
            print(f"[WARNING] pyautogui测试失败: {e}")
            print("可能需要在Windows环境下运行，或安装额外的系统依赖")
        
        return True
    
    # 安装缺失的模块
    print(f"\n需要安装 {len(missing_modules)} 个模块...")
    success = True
    
    for module in missing_modules:
        if not install_module(module):
            success = False
    
    if success:
        print("\n[SUCCESS] 所有依赖安装完成！")
        print("现在可以运行测试脚本了")
    else:
        print("\n[ERROR] 部分依赖安装失败")
        print("请手动运行: pip install pyautogui pillow")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

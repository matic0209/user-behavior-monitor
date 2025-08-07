#!/usr/bin/env python3
"""
Windows构建脚本测试版本
专门用于验证各个步骤是否正常工作
"""

import os
import sys
import subprocess
import shutil
import time
import platform

def test_step1_windows_check():
    """测试步骤1: Windows环境检查"""
    print("=== 步骤1: Windows环境检查 ===")
    if platform.system() == 'Windows':
        print("[SUCCESS] 当前是Windows系统")
        return True
    else:
        print(f"[ERROR] 当前系统: {platform.system()}，此脚本只能在Windows上运行")
        return False

def test_step2_dependencies():
    """测试步骤2: 依赖检查"""
    print("\n=== 步骤2: 依赖检查 ===")
    
    required_modules = [
        'psutil', 'pynput', 'keyboard', 'yaml', 'numpy', 'pandas', 
        'sklearn', 'xgboost', 'win32api', 'win32con', 'win32gui'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"[SUCCESS] {module} 可用")
        except ImportError:
            print(f"[ERROR] {module} 缺失")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n[ERROR] 以下模块缺失: {missing_modules}")
        return False
    
    print("[SUCCESS] 所有依赖检查通过")
    return True

def test_step3_environment():
    """测试步骤3: 环境设置"""
    print("\n=== 步骤3: 环境设置 ===")
    
    try:
        # 设置编码
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        
        # 设置控制台编码
        os.system('chcp 65001 > nul 2>&1')
        print("[SUCCESS] 环境设置完成")
        return True
    except Exception as e:
        print(f"[ERROR] 环境设置失败: {e}")
        return False

def test_step4_process_kill():
    """测试步骤4: 进程结束"""
    print("\n=== 步骤4: 检查并结束冲突进程 ===")
    
    # 获取当前进程ID
    current_pid = os.getpid()
    print(f"当前进程ID: {current_pid}")
    
    processes = ['UserBehaviorMonitor.exe', 'pyinstaller.exe']
    
    for proc in processes:
        try:
            print(f"正在检查进程: {proc}")
            result = subprocess.run(['taskkill', '/f', '/im', proc], 
                                  capture_output=True, shell=True, timeout=10)
            if result.returncode == 0:
                print(f"[SUCCESS] 已结束进程: {proc}")
            else:
                print(f"[INFO] 进程 {proc} 未运行或无法结束 (返回码: {result.returncode})")
        except subprocess.TimeoutExpired:
            print(f"[WARNING] 结束进程 {proc} 超时")
        except Exception as e:
            print(f"[INFO] 进程 {proc} 检查时出错: {e}")
    
    # 检查其他Python进程，但不杀死当前进程
    try:
        print("检查其他Python进程...")
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, shell=True, timeout=5)
        if result.returncode == 0:
            output = result.stdout.decode()
            if 'python.exe' in output:
                print("[INFO] 发现其他Python进程，但不会杀死当前进程")
            else:
                print("[INFO] 没有发现其他Python进程")
    except Exception as e:
        print(f"[INFO] 检查Python进程时出错: {e}")
    
    print("[SUCCESS] 进程检查完成")
    return True

def test_step5_clean_build():
    """测试步骤5: 清理构建目录"""
    print("\n=== 步骤5: 清理构建目录 ===")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                print(f"正在删除目录: {dir_name}")
                shutil.rmtree(dir_name)
                print(f"[SUCCESS] 已删除: {dir_name}")
            except PermissionError as e:
                print(f"[WARNING] 无法删除 {dir_name}，可能正在使用: {e}")
                print("[INFO] 继续执行，稍后可能会影响构建")
            except Exception as e:
                print(f"[ERROR] 删除 {dir_name} 时出错: {e}")
                print("[INFO] 继续执行，稍后可能会影响构建")
        else:
            print(f"[INFO] 目录 {dir_name} 不存在，跳过")
    
    print("[SUCCESS] 目录清理完成")
    return True

def test_step6_wait():
    """测试步骤6: 等待文件系统稳定"""
    print("\n=== 步骤6: 等待文件系统稳定 ===")
    
    try:
        print("等待2秒...")
        time.sleep(2)
        print("[SUCCESS] 等待完成")
        return True
    except Exception as e:
        print(f"[ERROR] 等待过程中出错: {e}")
        return False

def test_step7_pyinstaller():
    """测试步骤7: PyInstaller检查"""
    print("\n=== 步骤7: PyInstaller检查 ===")
    
    try:
        result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"[SUCCESS] PyInstaller可用，版本: {result.stdout.strip()}")
            return True
        else:
            print(f"[ERROR] PyInstaller不可用: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] 检查PyInstaller时出错: {e}")
        return False

def main():
    """主函数"""
    print("Windows构建脚本测试工具")
    print("=" * 50)
    
    try:
        # 测试所有步骤
        steps = [
            test_step1_windows_check,
            test_step2_dependencies,
            test_step3_environment,
            test_step4_process_kill,
            test_step5_clean_build,
            test_step6_wait,
            test_step7_pyinstaller
        ]
        
        for i, step_func in enumerate(steps, 1):
            print(f"\n正在执行步骤 {i}...")
            if not step_func():
                print(f"\n[ERROR] 步骤 {i} 失败，停止测试")
                return
        
        print("\n" + "=" * 50)
        print("[SUCCESS] 所有步骤测试通过!")
        print("[TIP] 现在可以运行完整的构建脚本: python build_windows_full.py")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n[ERROR] 测试过程中出现未预期的错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

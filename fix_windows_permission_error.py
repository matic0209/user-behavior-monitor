#!/usr/bin/env python3
"""
Windows权限错误修复工具
解决Windows环境下的权限问题和编码问题
"""

import os
import sys
import subprocess
import shutil
import time
import threading
import platform
from pathlib import Path

def set_console_encoding():
    """设置控制台编码为UTF-8"""
    try:
        # 设置环境变量
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # Windows系统特殊处理
        if platform.system() == 'Windows':
            # 设置控制台代码页为UTF-8
            os.system('chcp 65001 > nul')
            print("[INFO] 已设置控制台编码为UTF-8")
    except Exception as e:
        print(f"[WARNING] 设置编码失败: {e}")

def kill_processes():
    """结束可能占用文件的进程"""
    print("检查并结束占用文件的进程...")
    
    processes_to_kill = [
        'python.exe',
        'UserBehaviorMonitor.exe',
        'pyinstaller.exe'
    ]
    
    for process_name in processes_to_kill:
        try:
            # 使用taskkill强制结束进程
            result = subprocess.run(
                ['taskkill', '/f', '/im', process_name],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0:
                print(f"[SUCCESS] 已结束进程: {process_name}")
            else:
                print(f"[INFO] 进程 {process_name} 未运行或已结束")
        except Exception as e:
            print(f"[WARNING] 结束进程 {process_name} 时出错: {e}")

def safe_remove_path(path, max_retries=5, delay=2):
    """安全删除路径，带重试机制"""
    for attempt in range(max_retries):
        try:
            if os.path.isfile(path):
                os.unlink(path)
                print(f"[SUCCESS] 已删除文件: {path}")
                return True
            elif os.path.isdir(path):
                shutil.rmtree(path)
                print(f"[SUCCESS] 已删除目录: {path}")
                return True
        except PermissionError as e:
            if attempt < max_retries - 1:
                print(f"[WARNING] 无法删除 {path} (尝试 {attempt + 1}/{max_retries})")
                print(f"[ERROR] {e}")
                print(f"[INFO] 等待 {delay} 秒后重试...")
                time.sleep(delay)
            else:
                print(f"[ERROR] 无法删除 {path}，文件可能正在使用中")
                print(f"[TIP] 请关闭所有相关程序后重试")
                return False
        except Exception as e:
            print(f"[ERROR] 删除 {path} 时出错: {e}")
            return False
    return False

def clean_build_directories():
    """清理构建目录"""
    print("清理构建目录...")
    
    # 需要清理的目录
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"[INFO] 正在清理 {dir_name}...")
            safe_remove_path(dir_name)
        else:
            print(f"[INFO] {dir_name} 目录不存在")
    
    # 清理spec文件
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        print(f"[INFO] 正在清理 {spec_file}...")
        safe_remove_path(spec_file)
    
    # 清理日志文件（保留目录，只删除旧文件）
    log_dirs = ['logs', 'dist/logs']
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            print(f"[INFO] 正在清理 {log_dir} 中的旧日志文件...")
            try:
                for log_file in Path(log_dir).glob('*.log'):
                    # 只删除1小时前的日志文件
                    if log_file.stat().st_mtime < time.time() - 3600:
                        safe_remove_path(log_file)
            except Exception as e:
                print(f"[WARNING] 清理日志文件时出错: {e}")

def check_file_permissions():
    """检查文件权限"""
    print("检查文件权限...")
    
    # 检查当前目录权限
    current_dir = os.getcwd()
    try:
        test_file = os.path.join(current_dir, 'test_permission.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(f"[SUCCESS] 当前目录 {current_dir} 有写入权限")
    except Exception as e:
        print(f"[ERROR] 当前目录 {current_dir} 权限不足: {e}")
        return False
    
    return True

def run_as_admin():
    """以管理员权限运行"""
    print("检查是否需要管理员权限...")
    
    if platform.system() == 'Windows':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                print("[WARNING] 建议以管理员权限运行此脚本")
                print("[TIP] 右键点击命令提示符，选择'以管理员身份运行'")
                return False
            else:
                print("[SUCCESS] 当前以管理员权限运行")
                return True
        except Exception as e:
            print(f"[WARNING] 无法检查管理员权限: {e}")
            return False
    
    return True

def fix_encoding_issues():
    """修复编码问题"""
    print("修复编码问题...")
    
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # Windows系统特殊处理
    if platform.system() == 'Windows':
        try:
            # 设置控制台代码页
            os.system('chcp 65001 > nul 2>&1')
            print("[SUCCESS] 已设置控制台编码为UTF-8")
        except Exception as e:
            print(f"[WARNING] 设置控制台编码失败: {e}")

def create_safe_build_script():
    """创建安全的构建脚本"""
    print("创建安全的构建脚本...")
    
    safe_build_script = '''#!/usr/bin/env python3
"""
安全的Windows构建脚本
"""

import os
import sys
import subprocess
import time

def main():
    """主函数"""
    print("开始安全构建...")
    
    # 设置编码
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # 构建命令
    build_cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name=UserBehaviorMonitor',
        'user_behavior_monitor.py'
    ]
    
    try:
        print("执行构建命令...")
        result = subprocess.run(build_cmd, check=True, capture_output=True, text=True)
        print("[SUCCESS] 构建成功!")
        print("输出:", result.stdout)
        
        # 检查生成的文件
        exe_path = 'dist/UserBehaviorMonitor.exe'
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"[SUCCESS] 可执行文件已生成: {exe_path}")
            print(f"[INFO] 文件大小: {size:.1f} MB")
        else:
            print("[ERROR] 可执行文件未生成")
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 构建失败: {e}")
        print(f"[ERROR] 错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"[ERROR] 构建过程中出错: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
'''
    
    with open('safe_build.py', 'w', encoding='utf-8') as f:
        f.write(safe_build_script)
    
    print("[SUCCESS] 已创建安全构建脚本: safe_build.py")

def main():
    """主函数"""
    print("Windows权限错误修复工具")
    print("=" * 40)
    
    # 设置编码
    set_console_encoding()
    
    # 检查管理员权限
    run_as_admin()
    
    # 修复编码问题
    fix_encoding_issues()
    
    # 结束占用文件的进程
    kill_processes()
    
    # 检查文件权限
    if not check_file_permissions():
        print("[ERROR] 文件权限检查失败，请以管理员权限运行")
        return
    
    # 清理构建目录
    clean_build_directories()
    
    # 创建安全的构建脚本
    create_safe_build_script()
    
    print("\n" + "=" * 40)
    print("[SUCCESS] 修复完成!")
    print("[INFO] 现在可以运行以下命令进行构建:")
    print("    python safe_build.py")
    print("=" * 40)

if __name__ == "__main__":
    main()

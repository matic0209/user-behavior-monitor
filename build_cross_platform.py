#!/usr/bin/env python3
"""
跨平台构建脚本
根据操作系统自动调整配置
"""

import os
import sys
import subprocess
import shutil
import time
import platform

def setup_environment():
    """设置环境"""
    # 设置编码
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    if platform.system() == 'Windows':
        os.system('chcp 65001 > nul 2>&1')
        print("[SUCCESS] 环境设置完成")

def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"[SUCCESS] 已删除: {dir_name}")
            except PermissionError:
                print(f"[WARNING] 无法删除 {dir_name}，可能正在使用")
            except Exception as e:
                print(f"[ERROR] 删除 {dir_name} 时出错: {e}")

def get_platform_config():
    """根据平台获取配置"""
    is_windows = platform.system() == 'Windows'
    
    config = {
        'data_separator': ';' if is_windows else ':',
        'exe_extension': '.exe' if is_windows else '',
        'hidden_imports': [],
        'collect_all': [],
        'exclude_modules': []
    }
    
    # 通用依赖
    config['hidden_imports'].extend([
        'psutil',
        'yaml',
        'numpy',
        'pandas',
        'sklearn',
        'xgboost',
        'urllib.request',
        'urllib.parse',
        'urllib.error',
        'threading',
        'json',
        'datetime',
        'pathlib',
        'time',
        'signal',
        'os',
        'sys',
        'traceback'
    ])
    
    # Windows特定依赖
    if is_windows:
        config['hidden_imports'].extend([
            'win32api',
            'win32con',
            'win32gui',
            'win32service',
            'win32serviceutil',
            'pynput',
            'keyboard'
        ])
    else:
        # Linux特定依赖
        config['hidden_imports'].extend([
            'pynput',
            'keyboard'
        ])
        config['exclude_modules'].extend([
            'win32api',
            'win32con',
            'win32gui',
            'win32service',
            'win32serviceutil'
        ])
    
    # 强制收集的模块
    config['collect_all'].extend([
        'xgboost',
        'sklearn',
        'pandas',
        'numpy',
        'psutil',
        'pynput'
    ])
    
    return config

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 获取平台配置
    config = get_platform_config()
    
    # 构建命令
    build_cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',                    # 单文件
        '--windowed',                   # 无控制台窗口
        '--name=UserBehaviorMonitor',   # 可执行文件名
        f'--add-data=src/utils/config{config["data_separator"]}src/utils/config',  # 配置文件
    ]
    
    # 添加隐藏导入
    for module in config['hidden_imports']:
        build_cmd.append(f'--hidden-import={module}')
    
    # 添加强制收集模块
    for module in config['collect_all']:
        build_cmd.append(f'--collect-all={module}')
    
    # 添加排除模块
    for module in config['exclude_modules']:
        build_cmd.append(f'--exclude-module={module}')
    
    # 添加主程序文件
    build_cmd.append('user_behavior_monitor.py')
    
    try:
        print("执行构建命令...")
        print(f"命令: {' '.join(build_cmd)}")
        
        result = subprocess.run(build_cmd, check=True, 
                              capture_output=True, text=True, encoding='utf-8')
        
        print("[SUCCESS] 构建成功!")
        print("构建输出:")
        print(result.stdout)
        
        # 检查生成的文件
        exe_path = f'dist/UserBehaviorMonitor{config["exe_extension"]}'
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"[SUCCESS] 可执行文件已生成: {exe_path}")
            print(f"[INFO] 文件大小: {size:.1f} MB")
            return True
        else:
            print("[ERROR] 可执行文件未生成")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 构建失败!")
        print(f"[ERROR] 返回码: {e.returncode}")
        print(f"[ERROR] 错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"[ERROR] 构建过程中出错: {e}")
        return False

def main():
    """主函数"""
    print("跨平台构建脚本")
    print("=" * 40)
    print(f"当前平台: {platform.system()}")
    
    # 设置环境
    setup_environment()
    
    # 清理构建目录
    clean_build()
    
    # 等待一下确保文件释放
    print("等待文件系统稳定...")
    time.sleep(2)
    
    # 构建可执行文件
    if build_executable():
        print("\n" + "=" * 40)
        print("[SUCCESS] 构建完成!")
        config = get_platform_config()
        exe_path = f'dist/UserBehaviorMonitor{config["exe_extension"]}'
        print(f"[INFO] 可执行文件位置: {exe_path}")
        print("=" * 40)
    else:
        print("\n" + "=" * 40)
        print("[ERROR] 构建失败!")
        print("[TIP] 请检查错误信息并重试")
        print("=" * 40)

if __name__ == "__main__":
    main()

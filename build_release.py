#!/usr/bin/env python3
"""
发布版构建脚本
包含所有必要的修复和优化
"""

import os
import sys
import subprocess
import shutil
import time
import platform
import sqlite3
from pathlib import Path

def setup_release_environment():
    """设置发布版环境"""
    print("设置发布版环境...")
    
    # 修复模块导入
    project_root = Path(__file__).parent
    src_path = project_root / 'src'
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # 创建必要的目录
    dirs_to_create = ['models', 'data', 'logs', 'data/processed']
    for dir_name in dirs_to_create:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # 初始化数据库
    fix_database_initialization()
    
    print("[SUCCESS] 发布版环境设置完成")

def fix_database_initialization():
    """初始化数据库"""
    try:
        db_dir = Path('data')
        db_dir.mkdir(exist_ok=True)
        
        db_path = db_dir / 'alerts.db'
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 创建所有必要的表
        tables = [
            'CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, alert_type TEXT NOT NULL, message TEXT NOT NULL, severity TEXT NOT NULL, data TEXT, timestamp REAL NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
            'CREATE TABLE IF NOT EXISTS user_behavior (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, session_id TEXT NOT NULL, timestamp REAL NOT NULL, x INTEGER, y INTEGER, button TEXT, event_type TEXT, data TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
            'CREATE TABLE IF NOT EXISTS model_info (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, model_path TEXT NOT NULL, scaler_path TEXT NOT NULL, features_path TEXT NOT NULL, accuracy REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        conn.commit()
        conn.close()
        
        print(f"[SUCCESS] 数据库初始化完成")
        
    except Exception as e:
        print(f"[ERROR] 数据库初始化失败: {e}")

def build_release_executable():
    """构建发布版可执行文件"""
    print("构建发布版可执行文件...")
    
    # 获取平台配置
    is_windows = platform.system() == 'Windows'
    data_separator = ';' if is_windows else ':'
    exe_extension = '.exe' if is_windows else ''
    
    # 构建命令
    build_cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',                    # 单文件
        '--windowed',                   # 无控制台窗口
        '--name=UserBehaviorMonitor',   # 可执行文件名
        f'--add-data=src/utils/config{data_separator}src/utils/config',  # 配置文件
        f'--add-data=src{data_separator}src',  # 添加整个src目录
        f'--add-data=data{data_separator}data',  # 添加data目录
        
        # Windows API
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32gui',
        '--hidden-import=win32service',
        '--hidden-import=win32serviceutil',
        
        # 核心依赖
        '--hidden-import=pynput',
        '--hidden-import=psutil',
        '--hidden-import=keyboard',
        '--hidden-import=yaml',
        '--hidden-import=numpy',
        '--hidden-import=pandas',
        '--hidden-import=sklearn',
        '--hidden-import=xgboost',
        '--hidden-import=sqlite3',
        
        # 网络通信模块
        '--hidden-import=urllib.request',
        '--hidden-import=urllib.parse',
        '--hidden-import=urllib.error',
        
        # 强制收集关键模块
        '--collect-all=xgboost',
        '--collect-all=sklearn',
        '--collect-all=pandas',
        '--collect-all=numpy',
        '--collect-all=psutil',
        '--collect-all=pynput',
        
        # 排除不需要的模块
        '--exclude-module=matplotlib',
        '--exclude-module=seaborn',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        '--exclude-module=notebook',
        
        'user_behavior_monitor.py'
    ]
    
    try:
        print("执行构建命令...")
        result = subprocess.run(build_cmd, check=True, 
                              capture_output=True, text=True, encoding='utf-8')
        
        print("[SUCCESS] 构建成功!")
        
        # 检查生成的文件
        exe_path = f'dist/UserBehaviorMonitor{exe_extension}'
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
    print("发布版构建脚本")
    print("=" * 40)
    
    try:
        # 设置发布版环境
        setup_release_environment()
        
        # 构建可执行文件
        if build_release_executable():
            print("\n" + "=" * 40)
            print("[SUCCESS] 发布版构建完成!")
            print("[INFO] 可执行文件已生成")
            print("=" * 40)
        else:
            print("\n" + "=" * 40)
            print("[ERROR] 发布版构建失败!")
            print("=" * 40)
            
    except Exception as e:
        print(f"\n[ERROR] 发布版构建过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

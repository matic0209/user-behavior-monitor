#!/usr/bin/env python3
"""
专门解决xgboost问题的PyInstaller打包脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除 {dir_name}")
    
    # 清理spec文件
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        spec_file.unlink()
        print(f"已删除 {spec_file}")

def check_pyinstaller():
    """检查PyInstaller是否可用"""
    print("检查PyInstaller...")
    
    # 方法1: 直接命令
    try:
        result = subprocess.run(['pyinstaller', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"PyInstaller版本: {result.stdout.strip()}")
        return ['pyinstaller']
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("pyinstaller命令不可用")
    
    # 方法2: python -m PyInstaller
    try:
        result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"PyInstaller模块版本: {result.stdout.strip()}")
        return [sys.executable, '-m', 'PyInstaller']
    except subprocess.CalledProcessError:
        print("PyInstaller模块也不可用")
        return None

def build_exe_with_xgboost_fix(pyinstaller_cmd):
    """构建可执行文件，专门解决xgboost问题"""
    print("开始构建可执行文件（xgboost修复版）...")
    
    cmd = pyinstaller_cmd + [
        '--onefile',                    # 单文件
        '--windowed',                   # 无控制台窗口
        '--name=UserBehaviorMonitor',   # 可执行文件名
        '--add-data=src/utils/config;src/utils/config',  # 配置文件
        
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
        
        # 数据处理
        '--hidden-import=numpy',
        '--hidden-import=pandas',
        
        # 机器学习 - 重点修复
        '--hidden-import=sklearn',
        '--hidden-import=sklearn.ensemble',
        '--hidden-import=sklearn.tree',
        '--hidden-import=sklearn.model_selection',
        '--hidden-import=sklearn.preprocessing',
        '--hidden-import=sklearn.metrics',
        '--hidden-import=sklearn.utils',
        '--hidden-import=sklearn.base',
        '--hidden-import=sklearn.exceptions',
        
        # xgboost - 重点修复
        '--hidden-import=xgboost',
        '--hidden-import=xgboost.sklearn',
        '--hidden-import=xgboost.core',
        '--hidden-import=xgboost.training',
        '--hidden-import=xgboost.callback',
        '--hidden-import=xgboost.compat',
        '--hidden-import=xgboost.libpath',
        
        # 标准库
        '--hidden-import=threading',
        '--hidden-import=json',
        '--hidden-import=datetime',
        '--hidden-import=pathlib',
        '--hidden-import=time',
        '--hidden-import=signal',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--hidden-import=traceback',
        
        # 强制收集所有相关模块
        '--collect-all=xgboost',
        '--collect-all=sklearn',
        '--collect-all=pandas',
        '--collect-all=numpy',
        '--collect-all=psutil',
        '--collect-all=pynput',
        
        # 排除不需要的模块以减小体积
        '--exclude-module=matplotlib',
        '--exclude-module=seaborn',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        '--exclude-module=notebook',
        '--exclude-module=tkinter',
        
        # 调试选项
        '--debug=imports',
        
        'user_behavior_monitor.py'
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def create_spec_file():
    """创建自定义的spec文件"""
    print("创建自定义spec文件...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

block_cipher = None

# 数据文件
datas = [
    ('src/utils/config', 'src/utils/config'),
]

# 隐藏导入
hiddenimports = [
    # Windows API
    'win32api', 'win32con', 'win32gui', 'win32service', 'win32serviceutil',
    
    # 核心依赖
    'pynput', 'psutil', 'keyboard', 'yaml',
    
    # 数据处理
    'numpy', 'pandas',
    
    # 机器学习
    'sklearn', 'sklearn.ensemble', 'sklearn.tree', 'sklearn.model_selection',
    'sklearn.preprocessing', 'sklearn.metrics', 'sklearn.utils', 'sklearn.base',
    'sklearn.exceptions',
    
    # xgboost
    'xgboost', 'xgboost.sklearn', 'xgboost.core', 'xgboost.training',
    'xgboost.callback', 'xgboost.compat', 'xgboost.libpath',
    
    # 标准库
    'threading', 'json', 'datetime', 'pathlib', 'time', 'signal',
    'os', 'sys', 'traceback',
]

# 排除模块
excludes = [
    'matplotlib', 'seaborn', 'IPython', 'jupyter', 'notebook', 'tkinter',
]

a = Analysis(
    ['user_behavior_monitor.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='UserBehaviorMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    spec_file = Path('user_behavior_monitor.spec')
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✓ 已创建spec文件: {spec_file}")
    return spec_file

def build_with_spec(pyinstaller_cmd):
    """使用spec文件构建"""
    print("使用spec文件构建...")
    
    spec_file = create_spec_file()
    
    cmd = pyinstaller_cmd + [str(spec_file)]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("xgboost修复版打包工具")
    print("=" * 60)
    
    # 检查操作系统
    if sys.platform != 'win32':
        print("错误: 此脚本只能在Windows系统上运行")
        return
    
    try:
        # 清理构建目录
        clean_build()
        
        # 检查PyInstaller
        pyinstaller_cmd = check_pyinstaller()
        if pyinstaller_cmd is None:
            print("错误: 无法找到PyInstaller")
            return
        
        # 选择构建方式
        print("\n选择构建方式:")
        print("1. 使用命令行参数构建")
        print("2. 使用spec文件构建（推荐）")
        
        choice = input("请选择 (1/2): ").strip()
        
        if choice == "1":
            success = build_exe_with_xgboost_fix(pyinstaller_cmd)
        elif choice == "2":
            success = build_with_spec(pyinstaller_cmd)
        else:
            print("无效选择，使用spec文件构建")
            success = build_with_spec(pyinstaller_cmd)
        
        if success:
            print("\n🎉 打包完成!")
            print("可执行文件位置: dist/UserBehaviorMonitor.exe")
            print("\n如果仍有xgboost问题，请尝试:")
            print("1. 重新安装xgboost: pip install --force-reinstall xgboost")
            print("2. 使用conda环境: conda install xgboost")
            print("3. 检查Python版本兼容性")
        else:
            print("\n❌ 打包失败!")
        
    except Exception as e:
        print(f"打包过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 
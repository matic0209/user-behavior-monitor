#!/usr/bin/env python3
"""
用户行为监控系统启动脚本
支持调试模式的详细日志输出
"""

import sys
import os
import time
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """设置运行环境"""
    print("=== 设置运行环境 ===")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 7):
        print("警告: 建议使用Python 3.7或更高版本")
    
    # 检查工作目录
    current_dir = os.getcwd()
    print(f"当前工作目录: {current_dir}")
    
    # 检查项目结构
    project_files = [
        'src/simple_monitor_main.py',
        'src/utils/logger/logger.py',
        'src/utils/config/config.yaml',
        'requirements.txt'
    ]
    
    missing_files = []
    for file_path in project_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("警告: 以下文件缺失:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    else:
        print("项目文件结构检查通过")
    
    # 创建必要的目录
    directories = ['logs', 'data', 'models']
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"创建目录: {directory}")
        else:
            print(f"目录已存在: {directory}")
    
    print("=== 环境设置完成 ===\n")

def check_dependencies():
    """检查依赖项"""
    print("=== 检查依赖项 ===")
    
    # 核心依赖包列表（与requirements.txt保持一致）
    # 注意：包名和模块名可能不同
    package_checks = [
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('scikit-learn', 'sklearn'),  # 包名是scikit-learn，模块名是sklearn
        ('xgboost', 'xgboost'),
        ('scipy', 'scipy'),
        ('psutil', 'psutil'),
        ('matplotlib', 'matplotlib'),
        ('joblib', 'joblib'),
        ('pyyaml', 'yaml'),  # 包名是pyyaml，模块名是yaml
        ('pynput', 'pynput')
    ]
    
    missing_packages = []
    for package_name, module_name in package_checks:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {package_name} (版本: {version})")
        except ImportError:
            missing_packages.append(package_name)
            print(f"✗ {package_name} (缺失)")
    
    if missing_packages:
        print(f"\n警告: 以下包缺失: {', '.join(missing_packages)}")
        print("请运行以下命令之一:")
        print("  1. python quick_install.py")
        print("  2. python fix_missing_packages.py")
        print("  3. pip install -r requirements.txt")
        print("  4. pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt")
        return False
    
    # 检查Windows特定依赖
    try:
        import win32api
        print("✓ pywin32 (Windows API)")
    except ImportError:
        print("✗ pywin32 (Windows API) - 缺失")
        print("注意: 在Linux环境下这是正常的")
        print("Windows用户请运行: pip install pywin32")
    
    print("=== 依赖项检查完成 ===\n")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("用户行为监控系统 - 调试模式")
    print("=" * 60)
    print()
    
    try:
        # 设置环境
        setup_environment()
        
        # 检查依赖项
        if not check_dependencies():
            print("依赖项检查失败，请安装缺失的包")
            return 1
        
        # 导入监控模块
        print("=== 导入监控模块 ===")
        try:
            from src.simple_monitor_main import main as monitor_main
            print("✓ 监控模块导入成功")
        except ImportError as e:
            print(f"✗ 监控模块导入失败: {e}")
            print(f"错误详情: {traceback.format_exc()}")
            return 1
        
        print("=== 模块导入完成 ===\n")
        
        # 显示系统信息
        print("=== 系统信息 ===")
        print(f"操作系统: {sys.platform}")
        print(f"Python路径: {sys.executable}")
        print(f"项目根目录: {project_root}")
        print(f"日志目录: {project_root / 'logs'}")
        print(f"数据目录: {project_root / 'data'}")
        print("=== 系统信息显示完成 ===\n")
        
        # 启动监控系统
        print("=== 启动监控系统 ===")
        print("注意: 系统将以调试模式运行，将输出详细的日志信息")
        print("日志文件位置:")
        print("  - 主日志: logs/monitor_*.log")
        print("  - 错误日志: logs/error_*.log")
        print("  - 调试日志: logs/debug_*.log")
        print("  - 告警日志: logs/alerts/")
        print()
        print("快捷键说明:")
        print("  cccc: 开始数据采集")
        print("  ssss: 停止数据采集")
        print("  ffff: 处理特征")
        print("  tttt: 训练模型")
        print("  pppp: 开始预测")
        print("  xxxx: 停止预测")
        print("  rrrr: 重新训练")
        print("  iiii: 显示状态")
        print("  qqqq: 退出系统")
        print()
        print("按 Ctrl+C 退出")
        print("=" * 60)
        print()
        
        # 启动监控
        monitor_main()
        
    except KeyboardInterrupt:
        print("\n\n收到中断信号，正在退出...")
        return 0
    except Exception as e:
        print(f"\n\n系统启动失败: {str(e)}")
        print(f"错误详情: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
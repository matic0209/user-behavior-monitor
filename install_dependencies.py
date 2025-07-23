#!/usr/bin/env python3
"""
依赖安装脚本
用于检查和安装项目所需的依赖包
"""

import subprocess
import sys
import platform
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("=== 检查Python版本 ===")
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("✗ Python版本过低，需要Python 3.7或更高版本")
        return False
    
    print("✓ Python版本符合要求")
    return True

def install_requirements():
    """安装requirements.txt中的依赖"""
    print("\n=== 安装依赖包 ===")
    
    try:
        # 升级pip
        print("升级pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # 安装requirements.txt中的依赖
        print("安装项目依赖...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 依赖包安装成功")
            return True
        else:
            print(f"✗ 依赖包安装失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ 安装过程中出现错误: {e}")
        return False

def check_imports():
    """检查关键模块是否可以导入"""
    print("\n=== 检查模块导入 ===")
    
    modules_to_check = [
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('sklearn', 'sklearn'),
        ('xgboost', 'xgboost'),
        ('scipy', 'scipy'),
        ('psutil', 'psutil'),
        ('matplotlib', 'matplotlib'),
        ('seaborn', 'seaborn'),
        ('imblearn', 'imbalanced-learn'),
        ('joblib', 'joblib'),
        ('yaml', 'pyyaml'),
        ('pynput', 'pynput'),
        ('keyboard', 'keyboard')
    ]
    
    # 在Windows上检查pywin32
    if platform.system() == 'Windows':
        modules_to_check.append(('win32api', 'pywin32'))
    
    failed_imports = []
    
    for module_name, package_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} - 导入失败")
            failed_imports.append(package_name)
    
    if failed_imports:
        print(f"\n失败的导入: {failed_imports}")
        return False
    else:
        print("\n✓ 所有模块导入成功")
        return True

def check_project_structure():
    """检查项目结构"""
    print("\n=== 检查项目结构 ===")
    
    required_files = [
        'src/classification.py',
        'src/core/feature_engineer/simple_feature_processor.py',
        'src/core/model_trainer/simple_model_trainer.py',
        'src/core/data_collector/windows_mouse_collector.py',
        'src/utils/config/config_loader.py',
        'src/utils/logger/logger.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - 文件不存在")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n缺失的文件: {missing_files}")
        return False
    else:
        print("\n✓ 项目结构完整")
        return True

def main():
    """主函数"""
    print("用户行为监控系统 - 依赖检查工具")
    print("=" * 50)
    
    # 检查Python版本
    python_ok = check_python_version()
    
    # 安装依赖
    install_ok = install_requirements()
    
    # 检查导入
    import_ok = check_imports()
    
    # 检查项目结构
    structure_ok = check_project_structure()
    
    # 总结
    print("\n" + "=" * 50)
    print("检查结果:")
    print(f"Python版本: {'✓ 正常' if python_ok else '✗ 异常'}")
    print(f"依赖安装: {'✓ 正常' if install_ok else '✗ 异常'}")
    print(f"模块导入: {'✓ 正常' if import_ok else '✗ 异常'}")
    print(f"项目结构: {'✓ 正常' if structure_ok else '✗ 异常'}")
    
    if all([python_ok, install_ok, import_ok, structure_ok]):
        print("\n🎉 所有检查通过！系统可以正常运行。")
        print("\n使用说明:")
        print("1. 运行 python start_monitor.py 启动系统")
        print("2. 按 cccc 开始数据采集")
        print("3. 按 ssss 停止数据采集")
        print("4. 按 ffff 处理特征")
        print("5. 按 tttt 训练模型")
        print("6. 按 qqqq 退出系统")
    else:
        print("\n❌ 存在一些问题，请根据上述信息进行修复。")
        
        if not python_ok:
            print("\n建议: 升级Python到3.7或更高版本")
        if not install_ok:
            print("\n建议: 手动运行 pip install -r requirements.txt")
        if not import_ok:
            print("\n建议: 检查网络连接，重新安装依赖包")
        if not structure_ok:
            print("\n建议: 检查项目文件是否完整")

if __name__ == "__main__":
    main() 
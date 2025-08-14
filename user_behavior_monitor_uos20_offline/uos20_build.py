#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UOS20系统打包工具
使用PyInstaller创建Linux可执行文件
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

class UOS20Builder:
    """UOS20系统打包器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.main_script = self.project_root / "user_behavior_monitor_uos20.py"
        
    def check_dependencies(self):
        """检查依赖"""
        print("检查系统依赖...")
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
            print("错误: 需要Python 3.7或更高版本")
            return False
        
        # 检查PyInstaller
        try:
            import PyInstaller
            print(f"✓ PyInstaller已安装: {PyInstaller.__version__}")
        except ImportError:
            print("错误: PyInstaller未安装")
            print("请运行: pip3 install pyinstaller")
            return False
        
        # 检查其他依赖
        required_packages = [
            "numpy", "pandas", "scikit-learn", "xgboost", 
            "psutil", "pynput", "keyboard", "pyyaml"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"✓ {package}已安装")
            except ImportError:
                missing_packages.append(package)
                print(f"✗ {package}未安装")
        
        if missing_packages:
            print(f"\n请安装缺失的包:")
            print(f"pip3 install {' '.join(missing_packages)}")
            return False
        
        print("✓ 所有依赖检查通过")
        return True
    
    def find_pyinstaller(self):
        """查找PyInstaller命令"""
        commands = [
            "pyinstaller",
            "python3 -m PyInstaller",
            "python -m PyInstaller"
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(
                    cmd.split() + ["--version"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"✓ 找到PyInstaller: {cmd}")
                    return cmd
            except Exception:
                continue
        
        print("错误: 未找到PyInstaller命令")
        return None
    
    def clean_build(self):
        """清理构建目录"""
        print("清理构建目录...")
        
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print(f"✓ 已删除: {self.dist_dir}")
        
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print(f"✓ 已删除: {self.build_dir}")
        
        # 删除.spec文件
        spec_files = list(self.project_root.glob("*.spec"))
        for spec_file in spec_files:
            spec_file.unlink()
            print(f"✓ 已删除: {spec_file}")
    
    def create_spec_file(self):
        """创建spec文件"""
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# 添加项目根目录到路径
project_root = r"{self.project_root}"
sys.path.insert(0, project_root)

# 数据文件
datas = [
    (os.path.join(project_root, 'src/utils/config'), 'src/utils/config'),
    (os.path.join(project_root, 'requirements_uos20.txt'), '.'),
    (os.path.join(project_root, 'uos20_service_manager.py'), '.'),
    (os.path.join(project_root, 'uos20_background_manager.py'), '.'),
]

# 隐藏导入
hiddenimports = [
    'numpy',
    'pandas',
    'sklearn',
    'xgboost',
    'psutil',
    'pynput',
    'keyboard',
    'yaml',
    'json',
    'logging',
    'threading',
    'time',
    'signal',
    'subprocess',
    'pathlib',
    'tkinter',
    'tkinter.messagebox',
]

# 分析配置
a = Analysis(
    [r"{self.main_script}"],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 打包配置
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 可执行文件配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='user_behavior_monitor_uos20',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
        
        spec_file = self.project_root / "user_behavior_monitor_uos20.spec"
        try:
            with open(spec_file, 'w', encoding='utf-8') as f:
                f.write(spec_content)
            print(f"✓ 已创建spec文件: {spec_file}")
            return spec_file
        except Exception as e:
            print(f"错误: 创建spec文件失败: {e}")
            return None
    
    def build_executable(self):
        """构建可执行文件"""
        print("开始构建可执行文件...")
        
        # 查找PyInstaller
        pyinstaller_cmd = self.find_pyinstaller()
        if not pyinstaller_cmd:
            return False
        
        # 创建spec文件
        spec_file = self.create_spec_file()
        if not spec_file:
            return False
        
        try:
            # 构建命令
            cmd = pyinstaller_cmd.split() + [
                "--clean",
                "--distpath", str(self.dist_dir),
                "--workpath", str(self.build_dir),
                str(spec_file)
            ]
            
            print(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True)
            
            if result.returncode == 0:
                print("✓ 构建成功!")
                return True
            else:
                print("错误: 构建失败")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"错误: 构建过程失败: {e}")
            return False
        except Exception as e:
            print(f"错误: 构建异常: {e}")
            return False
    
    def create_installer(self):
        """创建安装包"""
        print("创建安装包...")
        
        executable = self.dist_dir / "user_behavior_monitor_uos20"
        if not executable.exists():
            print("错误: 可执行文件不存在")
            return False
        
        # 创建安装目录
        install_dir = self.project_root / "install_uos20"
        if install_dir.exists():
            shutil.rmtree(install_dir)
        install_dir.mkdir()
        
        # 复制文件
        files_to_copy = [
            (executable, install_dir / "user_behavior_monitor_uos20"),
            (self.project_root / "uos20_service_manager.py", install_dir),
            (self.project_root / "uos20_background_manager.py", install_dir),
            (self.project_root / "requirements_uos20.txt", install_dir),
            (self.project_root / "README.md", install_dir),
        ]
        
        for src, dst in files_to_copy:
            if src.exists():
                if src.is_file():
                    shutil.copy2(src, dst)
                else:
                    shutil.copytree(src, dst)
                print(f"✓ 已复制: {src.name}")
        
        # 创建安装脚本
        install_script = install_dir / "install.sh"
        install_content = f"""#!/bin/bash
# UOS20用户行为监控系统安装脚本

echo "开始安装用户行为监控系统..."

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

# 安装依赖
echo "安装Python依赖..."
pip3 install -r requirements_uos20.txt

# 设置执行权限
chmod +x user_behavior_monitor_uos20
chmod +x uos20_service_manager.py
chmod +x uos20_background_manager.py

echo "安装完成!"
echo ""
echo "使用方法:"
echo "  直接运行: ./user_behavior_monitor_uos20"
echo "  后台运行: python3 uos20_background_manager.py start"
echo "  服务运行: sudo python3 uos20_service_manager.py install"
"""
        
        with open(install_script, 'w') as f:
            f.write(install_content)
        os.chmod(install_script, 0o755)
        
        # 创建压缩包
        archive_name = "user_behavior_monitor_uos20.tar.gz"
        try:
            shutil.make_archive(
                str(self.project_root / "user_behavior_monitor_uos20"),
                'gztar',
                install_dir
            )
            print(f"✓ 安装包已创建: {archive_name}")
            return True
        except Exception as e:
            print(f"错误: 创建安装包失败: {e}")
            return False
    
    def build(self):
        """执行完整构建流程"""
        print("=" * 50)
        print("UOS20系统打包工具")
        print("=" * 50)
        
        # 检查依赖
        if not self.check_dependencies():
            return False
        
        # 清理构建目录
        self.clean_build()
        
        # 构建可执行文件
        if not self.build_executable():
            return False
        
        # 创建安装包
        if not self.create_installer():
            return False
        
        print("\n" + "=" * 50)
        print("构建完成!")
        print("=" * 50)
        print(f"可执行文件: {self.dist_dir}/user_behavior_monitor_uos20")
        print(f"安装包: user_behavior_monitor_uos20.tar.gz")
        print("\n部署说明:")
        print("1. 解压安装包: tar -xzf user_behavior_monitor_uos20.tar.gz")
        print("2. 进入目录: cd user_behavior_monitor_uos20")
        print("3. 运行安装: ./install.sh")
        print("4. 启动程序: ./user_behavior_monitor_uos20")
        
        return True

def main():
    """主函数"""
    builder = UOS20Builder()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "clean":
            builder.clean_build()
        elif command == "check":
            builder.check_dependencies()
        elif command == "build":
            builder.build_executable()
        elif command == "installer":
            builder.create_installer()
        else:
            print("未知命令")
            print("可用命令: clean, check, build, installer")
    else:
        builder.build()

if __name__ == "__main__":
    main() 
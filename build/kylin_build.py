#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麒麟系统打包工具
基于UOS20打包脚本适配麒麟系统
支持银河麒麟、中标麒麟等发行版
"""

import os
import sys
import subprocess
import shutil
import json
import platform
from pathlib import Path

class KylinBuilder:
    """麒麟系统打包器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.absolute()
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build_temp"
        self.main_script = self.project_root / "user_behavior_monitor.py"
        
        # 检测麒麟系统版本
        self.kylin_version = self.detect_kylin_version()
        
    def detect_kylin_version(self):
        """检测麒麟系统版本"""
        version_info = {
            'name': '未知',
            'version': '未知',
            'arch': platform.machine()
        }
        
        # 检查麒麟版本文件
        kylin_files = [
            '/etc/kylin-release',
            '/etc/neokylin-release', 
            '/etc/os-release'
        ]
        
        for file_path in kylin_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '麒麟' in content or 'Kylin' in content:
                            version_info['name'] = '麒麟'
                            if '银河麒麟' in content:
                                version_info['name'] = '银河麒麟'
                            elif '中标麒麟' in content:
                                version_info['name'] = '中标麒麟'
                            # 提取版本号
                            lines = content.strip().split('\n')
                            for line in lines:
                                if 'VERSION' in line:
                                    version_info['version'] = line.split('=')[-1].strip('"')
                                    break
                            break
                except Exception:
                    continue
        
        return version_info
        
    def check_system_compatibility(self):
        """检查系统兼容性"""
        print("检查麒麟系统兼容性...")
        print(f"检测到系统: {self.kylin_version['name']} {self.kylin_version['version']} ({self.kylin_version['arch']})")
        
        # 检查架构支持
        supported_archs = ['x86_64', 'aarch64', 'loongarch64']
        if self.kylin_version['arch'] not in supported_archs:
            print(f"警告: 架构 {self.kylin_version['arch']} 可能不完全支持")
        
        return True
    
    def check_dependencies(self):
        """检查依赖"""
        print("检查系统依赖...")
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
            print("错误: 需要Python 3.7或更高版本")
            return False
        
        print(f"✓ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 检查PyInstaller
        try:
            import PyInstaller
            print(f"✓ PyInstaller已安装: {PyInstaller.__version__}")
        except ImportError:
            print("错误: PyInstaller未安装")
            print("请运行: pip3 install pyinstaller")
            return False
        
        # 检查核心依赖
        required_packages = [
            "numpy", "pandas", "scikit-learn", "xgboost", 
            "psutil", "pynput", "pyyaml"
        ]
        
        # 麒麟系统特定依赖
        if self.kylin_version['arch'] == 'loongarch64':
            print("检测到龙芯架构，跳过部分依赖检查...")
            # 龙芯架构可能缺少某些包
            required_packages = ["numpy", "psutil", "pyyaml"]
        
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
                    text=True,
                    timeout=10
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
        
        dirs_to_clean = [self.dist_dir, self.build_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"✓ 已删除: {dir_path}")
        
        # 删除.spec文件
        spec_files = list(self.project_root.glob("*.spec"))
        for spec_file in spec_files:
            spec_file.unlink()
            print(f"✓ 已删除: {spec_file}")
    
    def create_spec_file(self):
        """创建适用于麒麟系统的spec文件"""
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# 麒麟系统用户行为监控系统打包配置

import sys
import os

# 添加项目根目录到路径
project_root = r"{self.project_root}"
sys.path.insert(0, project_root)

# 数据文件
datas = [
    (os.path.join(project_root, 'src'), 'src'),
    (os.path.join(project_root, 'requirements.txt'), '.'),
]

# 隐藏导入 - 麒麟系统适配
hiddenimports = [
    'numpy',
    'pandas',
    'sklearn',
    'sklearn.ensemble',
    'sklearn.tree',
    'xgboost',
    'psutil',
    'pynput',
    'pynput.mouse',
    'pynput.keyboard',
    'yaml',
    'json',
    'logging',
    'threading',
    'time',
    'signal',
    'subprocess',
    'pathlib',
    'sqlite3',
    'datetime',
    'os',
    'sys',
    'platform',
    'pickle',
    'random',
    'math',
]

# 麒麟系统特定导入
if '{self.kylin_version['arch']}' == 'loongarch64':
    # 龙芯架构特殊处理
    hiddenimports.extend([
        'ctypes',
        'ctypes.util',
    ])
else:
    # x86_64和aarch64架构
    hiddenimports.extend([
        'tkinter',
        'tkinter.messagebox',
        'matplotlib',
        'seaborn',
    ])

# 排除的模块
excludes = [
    'matplotlib.tests',
    'numpy.tests',
    'pandas.tests',
    'sklearn.tests',
    'test',
    'tests',
    'testing',
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
    excludes=excludes,
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
    name='user_behavior_monitor_kylin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 麒麟系统建议关闭UPX压缩
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
        
        spec_file = self.project_root / "user_behavior_monitor_kylin.spec"
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
            print("正在构建，请耐心等待...")
            
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
        """创建麒麟系统安装包"""
        print("创建麒麟系统安装包...")
        
        executable = self.dist_dir / "user_behavior_monitor_kylin"
        if not executable.exists():
            print("错误: 可执行文件不存在")
            return False
        
        # 创建安装目录
        install_dir = self.project_root / "install_kylin"
        if install_dir.exists():
            shutil.rmtree(install_dir)
        install_dir.mkdir()
        
        # 复制文件
        files_to_copy = [
            (executable, install_dir / "user_behavior_monitor_kylin"),
            (self.project_root / "README.md", install_dir),
            (self.project_root / "QUICK_START.md", install_dir),
            (self.project_root / "requirements.txt", install_dir),
        ]
        
        # 复制工具脚本
        tools_dir = self.project_root / "tools"
        if tools_dir.exists():
            install_tools_dir = install_dir / "tools"
            shutil.copytree(tools_dir, install_tools_dir)
            print("✓ 已复制工具脚本")
        
        for src, dst in files_to_copy:
            if src.exists():
                if src.is_file():
                    shutil.copy2(src, dst)
                else:
                    shutil.copytree(src, dst)
                print(f"✓ 已复制: {src.name}")
        
        # 创建麒麟系统安装脚本
        install_script = install_dir / "install_kylin.sh"
        install_content = f"""#!/bin/bash
# 麒麟系统用户行为监控系统安装脚本
# 适用于银河麒麟、中标麒麟等发行版

echo "开始安装用户行为监控系统 (麒麟版)..."
echo "检测到系统: {self.kylin_version['name']} {self.kylin_version['version']} ({self.kylin_version['arch']})"

# 检查系统
if [[ "$(uname)" != "Linux" ]]; then
    echo "错误: 此脚本仅支持Linux系统"
    exit 1
fi

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    echo "请安装Python3: sudo yum install python3 python3-pip"
    exit 1
fi

# 安装系统依赖 (麒麟系统使用yum/dnf)
echo "安装系统依赖..."
if command -v dnf &> /dev/null; then
    # 使用dnf (较新的麒麟版本)
    sudo dnf install -y python3-devel python3-pip gcc gcc-c++ make
elif command -v yum &> /dev/null; then
    # 使用yum (较老的麒麟版本)
    sudo yum install -y python3-devel python3-pip gcc gcc-c++ make
else
    echo "警告: 无法自动安装系统依赖，请手动安装"
fi

# 安装Python依赖
echo "安装Python依赖..."
pip3 install -r requirements.txt --user

# 设置执行权限
chmod +x user_behavior_monitor_kylin

# 创建桌面快捷方式
DESKTOP_FILE="$HOME/Desktop/用户行为监控.desktop"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=用户行为监控系统
Comment=麒麟系统用户行为监控
Exec=$PWD/user_behavior_monitor_kylin
Icon=applications-system
Terminal=true
Type=Application
Categories=System;Security;
EOF

chmod +x "$DESKTOP_FILE"

echo "安装完成!"
echo ""
echo "使用方法:"
echo "  直接运行: ./user_behavior_monitor_kylin"
echo "  后台运行: nohup ./user_behavior_monitor_kylin &"
echo "  查看日志: tail -f logs/monitor.log"
echo ""
echo "快捷键控制:"
echo "  rrrr - 重新采集和训练"
echo "  aaaa - 手动触发告警"  
echo "  qqqq - 退出系统"
"""
        
        with open(install_script, 'w', encoding='utf-8') as f:
            f.write(install_content)
        os.chmod(install_script, 0o755)
        
        # 创建启动脚本
        start_script = install_dir / "start_monitor.sh"
        start_content = """#!/bin/bash
# 启动用户行为监控系统

cd "$(dirname "$0")"

echo "启动用户行为监控系统 (麒麟版)..."
./user_behavior_monitor_kylin
"""
        
        with open(start_script, 'w', encoding='utf-8') as f:
            f.write(start_content)
        os.chmod(start_script, 0o755)
        
        # 创建压缩包
        archive_name = f"user_behavior_monitor_kylin_{self.kylin_version['arch']}.tar.gz"
        try:
            shutil.make_archive(
                str(self.project_root / f"user_behavior_monitor_kylin_{self.kylin_version['arch']}"),
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
        print("=" * 60)
        print("麒麟系统打包工具")
        print("=" * 60)
        
        # 检查系统兼容性
        if not self.check_system_compatibility():
            return False
        
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
        
        print("\n" + "=" * 60)
        print("麒麟系统打包完成!")
        print("=" * 60)
        print(f"系统信息: {self.kylin_version['name']} {self.kylin_version['version']} ({self.kylin_version['arch']})")
        print(f"可执行文件: {self.dist_dir}/user_behavior_monitor_kylin")
        print(f"安装包: user_behavior_monitor_kylin_{self.kylin_version['arch']}.tar.gz")
        print("\n部署说明:")
        print("1. 解压安装包: tar -xzf user_behavior_monitor_kylin_*.tar.gz")
        print("2. 进入目录: cd install_kylin")
        print("3. 运行安装: ./install_kylin.sh")
        print("4. 启动程序: ./user_behavior_monitor_kylin")
        print("\n麒麟系统特点:")
        print("- 适配银河麒麟、中标麒麟")
        print("- 支持x86_64、aarch64、loongarch64架构")
        print("- 使用yum/dnf包管理器")
        print("- 包含桌面快捷方式")
        
        return True

def main():
    """主函数"""
    builder = KylinBuilder()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "clean":
            builder.clean_build()
        elif command == "check":
            builder.check_system_compatibility()
            builder.check_dependencies()
        elif command == "build":
            builder.build_executable()
        elif command == "installer":
            builder.create_installer()
        else:
            print("未知命令")
            print("可用命令:")
            print("  clean     - 清理构建目录")
            print("  check     - 检查系统和依赖")
            print("  build     - 仅构建可执行文件")
            print("  installer - 仅创建安装包")
            print("  (无参数)  - 完整构建流程")
    else:
        builder.build()

if __name__ == "__main__":
    main()


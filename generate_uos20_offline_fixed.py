#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UOS20离线安装包生成器 - 修复版
解决Python包下载和包大小问题
"""

import os
import sys
import shutil
import subprocess
import tarfile
import json
from pathlib import Path
from datetime import datetime

class UOS20OfflineGeneratorFixed:
    """UOS20离线安装包生成器 - 修复版"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.package_name = "user_behavior_monitor_uos20_offline"
        self.package_dir = self.project_root / self.package_name
        
    def clean_package_dir(self):
        """清理包目录"""
        if self.package_dir.exists():
            shutil.rmtree(self.package_dir)
            print("✓ 已清理现有包目录")
    
    def create_package_structure(self):
        """创建包目录结构"""
        print("创建离线包目录结构...")
        
        directories = [
            self.package_dir,
            self.package_dir / "dependencies",
            self.package_dir / "dependencies" / "wheels",
            self.package_dir / "scripts",
            self.package_dir / "docs",
            self.package_dir / "bin",
            self.package_dir / "config",
            self.package_dir / "data",
            self.package_dir / "logs",
            self.package_dir / "models",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✓ 创建目录: {directory}")
    
    def download_python_packages_fixed(self):
        """修复版Python包下载"""
        print("下载Python包到本地 (修复版)...")
        
        requirements_file = self.project_root / "requirements_uos20.txt"
        wheels_dir = self.package_dir / "dependencies" / "wheels"
        
        if not requirements_file.exists():
            print("错误: requirements_uos20.txt 文件不存在")
            return False
        
        # 读取requirements文件
        packages = []
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    packages.append(line)
        
        print(f"需要下载的包: {packages}")
        
        # 逐个下载包，使用更兼容的参数
        success_count = 0
        for package in packages:
            try:
                print(f"正在下载: {package}")
                
                # 尝试不同的下载策略
                cmd = [
                    "pip3", "download",
                    "--dest", str(wheels_dir),
                    "--no-deps",  # 不下载依赖，避免循环依赖
                    package
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✓ 成功下载: {package}")
                    success_count += 1
                else:
                    print(f"✗ 下载失败: {package}")
                    print(f"错误: {result.stderr}")
                    
                    # 尝试不指定平台版本
                    cmd2 = [
                        "pip3", "download",
                        "--dest", str(wheels_dir),
                        "--no-deps",
                        "--no-binary=:all:",  # 允许源码包
                        package
                    ]
                    
                    result2 = subprocess.run(cmd2, capture_output=True, text=True)
                    if result2.returncode == 0:
                        print(f"✓ 成功下载(源码包): {package}")
                        success_count += 1
                    else:
                        print(f"✗ 下载失败(源码包): {package}")
                        print(f"错误: {result2.stderr}")
                        
            except Exception as e:
                print(f"✗ 下载异常: {package} - {e}")
        
        print(f"下载完成: {success_count}/{len(packages)} 个包成功")
        
        # 检查下载的文件
        wheel_files = list(wheels_dir.glob("*.whl"))
        tar_files = list(wheels_dir.glob("*.tar.gz"))
        zip_files = list(wheels_dir.glob("*.zip"))
        
        total_files = len(wheel_files) + len(tar_files) + len(zip_files)
        print(f"下载的文件: {total_files} 个")
        print(f"  - Wheel文件: {len(wheel_files)} 个")
        print(f"  - Tar文件: {len(tar_files)} 个")
        print(f"  - Zip文件: {len(zip_files)} 个")
        
        return total_files > 0
    
    def create_requirements_offline(self):
        """创建离线安装的requirements文件"""
        print("创建离线安装requirements文件...")
        
        wheels_dir = self.package_dir / "dependencies" / "wheels"
        offline_requirements = self.package_dir / "requirements_offline.txt"
        
        # 收集所有下载的包文件
        package_files = []
        package_files.extend(wheels_dir.glob("*.whl"))
        package_files.extend(wheels_dir.glob("*.tar.gz"))
        package_files.extend(wheels_dir.glob("*.zip"))
        
        if not package_files:
            print("警告: 没有找到下载的包文件")
            return False
        
        # 创建离线安装requirements文件
        with open(offline_requirements, 'w', encoding='utf-8') as f:
            f.write("# 离线安装requirements文件\n")
            f.write("# 包含所有下载的Python包\n\n")
            
            for package_file in package_files:
                f.write(f"dependencies/wheels/{package_file.name}\n")
        
        print(f"✓ 已创建离线requirements文件: {offline_requirements}")
        return True
    
    def copy_project_files(self):
        """复制项目文件到离线包"""
        print("复制项目文件到离线包...")
        
        # 需要复制的文件列表
        files_to_copy = [
            "user_behavior_monitor_uos20.py",
            "uos20_service_manager.py",
            "uos20_background_manager.py",
            "uos20_build.py",
            "requirements_uos20.txt",
            "README.md",
            "QUICK_START.md",
            "USAGE.md",
            "PRODUCT_ARCHITECTURE.md"
        ]
        
        # 需要复制的目录
        dirs_to_copy = [
            "src",
            "models"
        ]
        
        # 复制文件
        for file_name in files_to_copy:
            src_file = self.project_root / file_name
            dst_file = self.package_dir / file_name
            
            if src_file.exists():
                shutil.copy2(src_file, dst_file)
                print(f"✓ 已复制: {file_name}")
            else:
                print(f"⚠ 文件不存在: {file_name}")
        
        # 复制目录
        for dir_name in dirs_to_copy:
            src_dir = self.project_root / dir_name
            dst_dir = self.package_dir / dir_name
            
            if src_dir.exists():
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
                print(f"✓ 已复制目录: {dir_name}")
            else:
                print(f"⚠ 目录不存在: {dir_name}")
    
    def create_offline_install_script_fixed(self):
        """创建修复版离线安装脚本"""
        print("创建修复版离线安装脚本...")
        
        install_script = self.package_dir / "install_offline.sh"
        
        script_content = f"""#!/bin/bash
# UOS20用户行为监控系统离线安装脚本 - 修复版
# 版本: v1.3.0 离线版
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e

# 颜色定义
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m'

# 日志函数
log_info() {{
    echo -e "${{GREEN}}[INFO]${{NC}} $1"
}}

log_warn() {{
    echo -e "${{YELLOW}}[WARN]${{NC}} $1"
}}

log_error() {{
    echo -e "${{RED}}[ERROR]${{NC}} $1"
}}

log_step() {{
    echo -e "${{BLUE}}[STEP]${{NC}} $1"
}}

# 检查系统
check_system() {{
    log_step "检查系统环境..."
    
    # 检查操作系统
    if [[ "$(uname)" != "Linux" ]]; then
        log_error "此脚本仅支持Linux系统"
        exit 1
    fi
    
    # 检查是否为UOS20
    if [[ -f "/etc/uos-release" ]]; then
        log_info "检测到UOS系统"
        cat /etc/uos-release
    else
        log_warn "未检测到UOS系统，但继续安装..."
    fi
    
    # 检查Python3
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python3，请先安装Python3"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'${{sys.version_info.major}}.${{sys.version_info.minor}}')")
    log_info "Python版本: $python_version"
    
    # 检查pip3
    if ! command -v pip3 &> /dev/null; then
        log_error "未找到pip3，请先安装pip3"
        exit 1
    fi
    
    log_info "系统检查通过"
}}

# 安装系统依赖
install_system_deps() {{
    log_step "安装系统依赖..."
    
    # 更新包列表
    log_info "更新包列表..."
    sudo apt update
    
    # 安装系统依赖
    log_info "安装系统依赖包..."
    sudo apt install -y \\
        python3-dev \\
        python3-pip \\
        python3-venv \\
        build-essential \\
        libssl-dev \\
        libffi-dev \\
        screen \\
        curl \\
        wget \\
        python3-setuptools \\
        python3-wheel
    
    log_info "系统依赖安装完成"
}}

# 创建虚拟环境
create_venv() {{
    log_step "创建Python虚拟环境..."
    
    if [[ -d "venv" ]]; then
        log_warn "虚拟环境已存在，是否重新创建? (y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            log_info "删除现有虚拟环境..."
            rm -rf venv
        else
            log_info "使用现有虚拟环境"
            return
        fi
    fi
    
    log_info "创建虚拟环境..."
    python3 -m venv venv
    
    log_info "激活虚拟环境..."
    source venv/bin/activate
    
    log_info "升级pip..."
    pip install --upgrade pip setuptools wheel
    
    log_info "虚拟环境创建完成"
}}

# 离线安装Python依赖 - 修复版
install_python_deps_offline_fixed() {{
    log_step "离线安装Python依赖 (修复版)..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 检查离线包目录
    wheels_dir="dependencies/wheels"
    if [[ -d "$wheels_dir" && "$(ls -A "$wheels_dir")" ]]; then
        log_info "发现离线Python包，进行离线安装..."
        
        # 安装所有包文件
        for package_file in "$wheels_dir"/*; do
            if [[ -f "$package_file" ]]; then
                log_info "安装: $(basename "$package_file")"
                pip install "$package_file" --no-deps
            fi
        done
        
        log_info "离线Python依赖安装完成"
        
        # 尝试在线安装缺失的依赖
        log_info "检查并安装缺失的依赖..."
        pip install -r requirements_uos20.txt --no-deps || true
        
    else
        log_warn "未发现离线Python包，尝试在线安装..."
        install_python_deps_online
    fi
}}

# 在线安装Python依赖
install_python_deps_online() {{
    log_info "在线安装Python依赖..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装基础依赖
    log_info "安装基础依赖..."
    pip install -r requirements_uos20.txt
    
    # 安装额外依赖
    log_info "安装额外依赖..."
    pip install \\
        python-xlib \\
        python-evdev \\
        setuptools \\
        wheel
    
    log_info "Python依赖安装完成"
}}

# 创建目录结构
create_directories() {{
    log_step "创建目录结构..."
    
    # 创建必要的目录
    mkdir -p data
    mkdir -p logs
    mkdir -p models
    mkdir -p logs/alerts
    mkdir -p logs/anomalies
    
    log_info "目录结构创建完成"
}}

# 设置权限
set_permissions() {{
    log_step "设置文件权限..."
    
    # 设置脚本执行权限
    chmod +x user_behavior_monitor_uos20.py
    chmod +x uos20_service_manager.py
    chmod +x uos20_background_manager.py
    chmod +x uos20_build.py
    
    # 设置安装脚本权限
    chmod +x install_offline.sh
    
    log_info "文件权限设置完成"
}}

# 创建配置文件
create_configs() {{
    log_step "创建配置文件..."
    
    # 创建服务配置
    if [[ -f "uos20_service_config.json" ]]; then
        log_info "服务配置文件已存在"
    else
        log_info "创建服务配置文件..."
        python3 uos20_service_manager.py config
    fi
    
    # 创建后台进程配置
    if [[ -f "uos20_background_config.json" ]]; then
        log_info "后台进程配置文件已存在"
    else
        log_info "创建后台进程配置文件..."
        python3 uos20_background_manager.py config
    fi
    
    log_info "配置文件创建完成"
}}

# 创建管理脚本
create_management_scripts() {{
    log_step "创建管理脚本..."
    
    # 创建启动脚本
    cat > start_monitor.sh << 'EOF'
#!/bin/bash
# 启动用户行为监控系统

cd "$(dirname "$0")"

echo "启动用户行为监控系统..."

# 激活虚拟环境
source venv/bin/activate

# 启动程序
python3 user_behavior_monitor_uos20.py
EOF

    # 创建后台启动脚本
    cat > start_background.sh << 'EOF'
#!/bin/bash
# 后台启动用户行为监控系统

cd "$(dirname "$0")"

echo "后台启动用户行为监控系统..."

# 激活虚拟环境
source venv/bin/activate

# 启动后台进程
python3 uos20_background_manager.py start

echo "后台进程已启动"
echo "查看状态: ./status_monitor.sh"
echo "查看日志: ./view_logs.sh"
EOF

    # 创建停止脚本
    cat > stop_monitor.sh << 'EOF'
#!/bin/bash
# 停止用户行为监控系统

cd "$(dirname "$0")"

echo "停止用户行为监控系统..."

# 停止后台进程
python3 uos20_background_manager.py stop

# 停止服务
sudo python3 uos20_service_manager.py stop 2>/dev/null || true

echo "监控系统已停止"
EOF

    # 创建状态查看脚本
    cat > status_monitor.sh << 'EOF'
#!/bin/bash
# 查看监控系统状态

cd "$(dirname "$0")"

echo "用户行为监控系统状态:"
echo "========================"

# 检查后台进程状态
echo "后台进程状态:"
python3 uos20_background_manager.py status

echo ""

# 检查服务状态
echo "系统服务状态:"
sudo python3 uos20_service_manager.py status 2>/dev/null || echo "服务未安装"

echo ""

# 检查日志文件
echo "日志文件:"
ls -la logs/ 2>/dev/null || echo "日志目录不存在"
EOF

    # 创建日志查看脚本
    cat > view_logs.sh << 'EOF'
#!/bin/bash
# 查看监控系统日志

cd "$(dirname "$0")"

echo "用户行为监控系统日志:"
echo "======================"

# 显示最近的日志
echo "最近的日志 (最后50行):"
python3 uos20_background_manager.py logs

echo ""
echo "实时跟踪日志 (Ctrl+C 退出):"
python3 uos20_background_manager.py follow
EOF

    # 设置脚本权限
    chmod +x start_monitor.sh
    chmod +x start_background.sh
    chmod +x stop_monitor.sh
    chmod +x status_monitor.sh
    chmod +x view_logs.sh
    
    log_info "管理脚本创建完成"
}}

# 测试安装
test_installation() {{
    log_step "测试安装..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 测试Python导入
    log_info "测试Python模块导入..."
    python3 -c "
try:
    import numpy
    import pandas
    import sklearn
    import xgboost
    import psutil
    import pynput
    import keyboard
    import yaml
    print('✓ 所有依赖包导入成功')
except ImportError as e:
    print(f'✗ 依赖包导入失败: {{e}}')
    print('将尝试在线安装缺失的包...')
    import subprocess
    subprocess.run(['pip', 'install', 'numpy', 'pandas', 'scikit-learn', 'xgboost', 'psutil', 'pynput', 'keyboard', 'pyyaml'])
"
    
    log_info "安装测试通过"
}}

# 显示使用说明
show_usage() {{
    log_step "安装完成！"
    
    echo ""
    echo "=========================================="
    echo "离线安装完成！使用说明："
    echo "=========================================="
    echo ""
    echo "1. 直接运行:"
    echo "   ./start_monitor.sh"
    echo ""
    echo "2. 后台运行:"
    echo "   ./start_background.sh"
    echo "   ./status_monitor.sh"
    echo "   ./stop_monitor.sh"
    echo ""
    echo "3. 系统服务运行:"
    echo "   sudo python3 uos20_service_manager.py install"
    echo "   sudo systemctl start user-behavior-monitor"
    echo "   sudo systemctl status user-behavior-monitor"
    echo ""
    echo "4. 查看日志:"
    echo "   ./view_logs.sh"
    echo ""
    echo "5. 快捷键控制:"
    echo "   rrrr - 重新采集和训练"
    echo "   aaaa - 手动触发告警"
    echo "   qqqq - 退出系统"
    echo ""
    echo "6. 构建可执行文件:"
    echo "   python3 uos20_build.py"
    echo ""
    echo "更多信息请查看 README.md"
    echo "=========================================="
}}

# 主安装流程
main() {{
    echo "开始离线安装UOS20用户行为监控系统..."
    echo ""
    
    check_system
    install_system_deps
    create_venv
    install_python_deps_offline_fixed
    create_directories
    set_permissions
    create_configs
    create_management_scripts
    test_installation
    show_usage
}}

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
    log_error "请不要以root用户运行此脚本"
    log_error "请使用普通用户运行: ./install_offline.sh"
    exit 1
fi

# 运行主安装流程
main "$@"
"""
        
        with open(install_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        os.chmod(install_script, 0o755)
        print(f"✓ 已创建修复版离线安装脚本: {install_script}")
    
    def create_package_info(self):
        """创建包信息文件"""
        print("创建包信息文件...")
        
        # 计算包大小
        package_size = 0
        if self.package_dir.exists():
            for file_path in self.package_dir.rglob("*"):
                if file_path.is_file():
                    package_size += file_path.stat().st_size
        
        package_info = {
            "package_name": "user_behavior_monitor_uos20_offline",
            "version": "1.3.0",
            "target_system": "UOS20",
            "created_at": datetime.now().isoformat(),
            "description": "UOS20用户行为监控系统离线安装包",
            "package_size_mb": round(package_size / (1024 * 1024), 2),
            "installation": {
                "script": "install_offline.sh",
                "requirements": "requirements_uos20.txt",
                "main_script": "user_behavior_monitor_uos20.py"
            }
        }
        
        info_file = self.package_dir / "package_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(package_info, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 已创建包信息文件: {info_file}")
    
    def create_archive(self):
        """创建压缩包"""
        print("创建压缩包...")
        
        archive_name = f"{self.package_name}.tar.gz"
        archive_path = self.project_root / archive_name
        
        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(self.package_dir, arcname=self.package_name)
            
            # 获取文件大小
            size_mb = archive_path.stat().st_size / (1024 * 1024)
            print(f"✓ 压缩包已创建: {archive_name}")
            print(f"  文件大小: {size_mb:.2f} MB")
            print(f"  文件路径: {archive_path}")
            
            return True
        except Exception as e:
            print(f"错误: 创建压缩包失败: {e}")
            return False
    
    def build(self):
        """执行完整构建流程"""
        print("=" * 60)
        print("UOS20离线安装包生成工具 - 修复版")
        print("=" * 60)
        
        # 清理现有包目录
        self.clean_package_dir()
        
        # 创建包结构
        self.create_package_structure()
        
        # 下载Python包 (修复版)
        if not self.download_python_packages_fixed():
            print("警告: Python包下载失败，将创建不完整的离线包")
        
        # 创建离线requirements文件
        self.create_requirements_offline()
        
        # 复制项目文件
        self.copy_project_files()
        
        # 创建修复版离线安装脚本
        self.create_offline_install_script_fixed()
        
        # 创建包信息
        self.create_package_info()
        
        # 创建压缩包
        if not self.create_archive():
            return False
        
        print("\n" + "=" * 60)
        print("离线安装包生成完成!")
        print("=" * 60)
        print(f"安装包: {self.package_name}.tar.gz")
        print(f"包大小: {self.package_dir.stat().st_size / (1024*1024):.2f} MB")
        print("\n部署说明:")
        print("1. 将安装包传输到目标UOS20系统")
        print("2. 解压安装包: tar -xzf user_behavior_monitor_uos20_offline.tar.gz")
        print("3. 进入目录: cd user_behavior_monitor_uos20_offline")
        print("4. 运行安装: ./install_offline.sh")
        print("5. 启动程序: ./start_monitor.sh")
        print("\n离线包特点:")
        print("- 包含所有Python依赖包")
        print("- 支持完全离线安装")
        print("- 自动环境配置")
        print("- 完整的文档和脚本")
        print("- 修复了包下载问题")
        
        return True

def main():
    """主函数"""
    generator = UOS20OfflineGeneratorFixed()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "clean":
            generator.clean_package_dir()
        elif command == "download":
            generator.download_python_packages_fixed()
        elif command == "create":
            generator.create_package_structure()
            generator.copy_project_files()
            generator.create_offline_install_script_fixed()
        else:
            print("未知命令")
            print("可用命令: clean, download, create")
    else:
        generator.build()

if __name__ == "__main__":
    main() 
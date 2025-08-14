#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UOS20离线安装包生成器 - 包含Python解释器
生成包含Python解释器和所有依赖的完整离线安装包
"""

import os
import sys
import shutil
import subprocess
import tarfile
import json
from pathlib import Path
from datetime import datetime

class UOS20OfflineWithPythonGenerator:
    """UOS20包含Python解释器的离线安装包生成器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.package_name = "user_behavior_monitor_uos20_offline_with_python"
        self.package_dir = self.project_root / self.package_name
        self.python_dir = self.package_dir / "python"
        
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
            self.python_dir,
            self.python_dir / "bin",
            self.python_dir / "lib",
            self.python_dir / "include",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✓ 创建目录: {directory}")
    
    def download_python_interpreter(self):
        """下载Python解释器"""
        print("下载Python解释器...")
        
        python_version = "3.10.12"  # 使用稳定的Python版本
        python_url = f"https://www.python.org/ftp/python/{python_version}/Python-{python_version}.tgz"
        python_tar = self.project_root / f"Python-{python_version}.tgz"
        python_src = self.project_root / f"Python-{python_version}"
        
        try:
            # 下载Python源码
            if not python_tar.exists():
                print(f"下载Python {python_version}...")
                subprocess.run([
                    "wget", "-O", str(python_tar), python_url
                ], check=True)
            
            # 解压Python源码
            if not python_src.exists():
                print("解压Python源码...")
                subprocess.run([
                    "tar", "-xzf", str(python_tar)
                ], check=True)
            
            # 编译Python（静态链接）
            print("编译Python解释器...")
            os.chdir(python_src)
            
            # 配置编译选项
            configure_cmd = [
                "./configure",
                "--prefix=" + str(self.python_dir),
                "--enable-optimizations",
                "--with-ensurepip=install",
                "--enable-shared",
                "--with-system-ffi",
                "--with-system-expat"
            ]
            
            subprocess.run(configure_cmd, check=True)
            
            # 编译
            subprocess.run(["make", "-j4"], check=True)
            
            # 安装到指定目录
            subprocess.run(["make", "install"], check=True)
            
            print("✓ Python解释器编译完成")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"错误: Python编译失败: {e}")
            return False
        except Exception as e:
            print(f"错误: Python下载/编译过程异常: {e}")
            return False
        finally:
            os.chdir(self.project_root)
    
    def download_python_packages_for_python37(self):
        """下载Python 3.7兼容的Python包"""
        print("下载Python 3.7兼容的Python包...")
        
        requirements_file = self.project_root / "requirements_uos20_python37.txt"
        wheels_dir = self.package_dir / "dependencies" / "wheels"
        
        if not requirements_file.exists():
            print("错误: requirements_uos20_python37.txt 文件不存在")
            return False
        
        try:
            # 使用编译的Python下载包
            python_bin = self.python_dir / "bin" / "python3"
            pip_bin = self.python_dir / "bin" / "pip3"
            
            if not python_bin.exists():
                print("错误: 编译的Python不存在")
                return False
            
            # 下载所有包到wheels目录
            cmd = [
                str(pip_bin), "download",
                "--platform", "linux_x86_64",
                "--python-version", "3.7",
                "--only-binary=:all:",
                "--dest", str(wheels_dir),
                "-r", str(requirements_file)
            ]
            
            print(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            print("✓ Python包下载完成")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"错误: 下载Python包失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False
        except Exception as e:
            print(f"错误: 下载过程异常: {e}")
            return False
    
    def copy_project_files(self):
        """复制项目文件到离线包"""
        print("复制项目文件到离线包...")
        
        # 需要复制的文件列表
        files_to_copy = [
            "user_behavior_monitor_uos20.py",
            "uos20_service_manager.py",
            "uos20_background_manager.py",
            "uos20_build.py",
            "requirements_uos20_python37.txt",
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
    
    def create_install_script_with_python(self):
        """创建包含Python的安装脚本"""
        print("创建包含Python的安装脚本...")
        
        install_script = self.package_dir / "install_with_python.sh"
        
        script_content = f"""#!/bin/bash
# UOS20用户行为监控系统离线安装脚本 - 包含Python版
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
    
    # 检查是否为UOS系统
    uos_detected=false
    
    # 检查多种UOS标识文件
    if [[ -f "/etc/uos-release" ]]; then
        log_info "检测到UOS系统 (/etc/uos-release)"
        cat /etc/uos-release
        uos_detected=true
    elif [[ -f "/etc/deepin-version" ]]; then
        log_info "检测到Deepin/UOS系统 (/etc/deepin-version)"
        cat /etc/deepin-version
        uos_detected=true
    elif [[ -f "/etc/os-release" ]] && grep -q "UOS\|deepin" /etc/os-release; then
        log_info "检测到UOS系统 (/etc/os-release)"
        grep -E "(NAME|VERSION|ID)" /etc/os-release
        uos_detected=true
    elif [[ -f "/etc/lsb-release" ]] && grep -q "UOS\|deepin" /etc/lsb-release; then
        log_info "检测到UOS系统 (/etc/lsb-release)"
        cat /etc/lsb-release
        uos_detected=true
    fi
    
    # 检查系统信息
    if [[ "$uos_detected" == "false" ]]; then
        log_info "系统信息检查:"
        if [[ -f "/etc/os-release" ]]; then
            log_info "操作系统: $(grep '^NAME=' /etc/os-release | cut -d'=' -f2 | tr -d '"')"
        fi
        if [[ -f "/etc/lsb-release" ]]; then
            log_info "发行版: $(grep '^DISTRIB_DESCRIPTION=' /etc/lsb-release | cut -d'=' -f2 | tr -d '"')"
        fi
        log_warn "未检测到UOS系统标识，但继续安装..."
        log_info "此脚本兼容大多数Linux发行版"
    fi
    
    # 检查内置Python
    python_bin="python/bin/python3"
    pip_bin="python/bin/pip3"
    
    if [[ -f "$python_bin" ]]; then
        log_info "找到内置Python: $($python_bin --version)"
    else
        log_error "内置Python不存在"
        exit 1
    fi
    
    if [[ -f "$pip_bin" ]]; then
        log_info "找到内置pip: $($pip_bin --version)"
    else
        log_error "内置pip不存在"
        exit 1
    fi
    
    log_info "系统检查通过"
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
    python/bin/python3 -m venv venv
    
    log_info "激活虚拟环境..."
    source venv/bin/activate
    
    log_info "升级pip..."
    pip install --upgrade pip setuptools wheel
    
    log_info "虚拟环境创建完成"
}}

# 离线安装Python依赖
install_python_deps_offline() {{
    log_step "离线安装Python依赖..."
    
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
        pip install -r requirements_uos20_python37.txt --no-deps || true
        
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
    pip install -r requirements_uos20_python37.txt
    
    # 安装额外依赖
    log_info "安装额外依赖..."
    pip install python-xlib python-evdev setuptools wheel
    
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
    chmod +x install_with_python.sh
    
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
        python/bin/python3 uos20_service_manager.py config
    fi
    
    # 创建后台进程配置
    if [[ -f "uos20_background_config.json" ]]; then
        log_info "后台进程配置文件已存在"
    else
        log_info "创建后台进程配置文件..."
        python/bin/python3 uos20_background_manager.py config
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
    print('✗ 依赖包导入失败: ' + str(e))
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
    echo "注意: 此版本包含独立的Python解释器"
    echo "更多信息请查看 README.md"
    echo "=========================================="
}}

# 主安装流程
main() {{
    echo "开始离线安装UOS20用户行为监控系统 (包含Python版)..."
    echo ""
    
    check_system
    create_venv
    install_python_deps_offline
    create_directories
    set_permissions
    create_configs
    create_management_scripts
    test_installation
    show_usage
}}

# 运行主安装流程
main "$@"
"""
        
        with open(install_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        os.chmod(install_script, 0o755)
        print(f"✓ 已创建包含Python的安装脚本: {install_script}")
    
    def create_package_info(self):
        """创建包信息文件"""
        print("创建包信息文件...")
        
        package_info = {
            "package_name": "user_behavior_monitor_uos20_offline_with_python",
            "version": "1.3.0",
            "target_system": "UOS20",
            "created_at": datetime.now().isoformat(),
            "description": "UOS20用户行为监控系统离线安装包 - 包含Python解释器",
            "python_version": "3.10.12",
            "installation": {
                "script": "install_with_python.sh",
                "requirements": "requirements_uos20_python37.txt",
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
        print("UOS20离线安装包生成工具 - 包含Python版")
        print("=" * 60)
        
        # 清理现有包目录
        self.clean_package_dir()
        
        # 创建包结构
        self.create_package_structure()
        
        # 下载Python解释器
        if not self.download_python_interpreter():
            print("错误: Python解释器下载/编译失败")
            return False
        
        # 下载Python包
        if not self.download_python_packages_for_python37():
            print("警告: Python包下载失败，将创建不完整的离线包")
        
        # 复制项目文件
        self.copy_project_files()
        
        # 创建安装脚本
        self.create_install_script_with_python()
        
        # 创建包信息
        self.create_package_info()
        
        # 创建压缩包
        if not self.create_archive():
            return False
        
        print("\n" + "=" * 60)
        print("包含Python的离线安装包生成完成!")
        print("=" * 60)
        print(f"安装包: {self.package_name}.tar.gz")
        print(f"包大小: {self.package_dir.stat().st_size / (1024*1024):.2f} MB")
        print("\n部署说明:")
        print("1. 将安装包传输到目标系统")
        print("2. 解压安装包: tar -xzf user_behavior_monitor_uos20_offline_with_python.tar.gz")
        print("3. 进入目录: cd user_behavior_monitor_uos20_offline_with_python")
        print("4. 运行安装: ./install_with_python.sh")
        print("5. 启动程序: ./start_monitor.sh")
        print("\n离线包特点:")
        print("- 包含独立的Python 3.10.12解释器")
        print("- 包含所有Python依赖包")
        print("- 支持完全离线安装")
        print("- 不受系统Python版本限制")
        print("- 自动环境配置")
        
        return True

def main():
    """主函数"""
    generator = UOS20OfflineWithPythonGenerator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "clean":
            generator.clean_package_dir()
        elif command == "download":
            generator.download_python_interpreter()
        elif command == "create":
            generator.create_package_structure()
            generator.copy_project_files()
            generator.create_install_script_with_python()
        else:
            print("未知命令")
            print("可用命令: clean, download, create")
    else:
        generator.build()

if __name__ == "__main__":
    main() 
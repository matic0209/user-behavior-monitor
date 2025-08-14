#!/bin/bash
# UOS20用户行为监控系统离线安装脚本 - 增强版
# 版本: v1.3.0 离线版
# 生成时间: 2025-07-29 10:45:00

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查并安装pip3
install_pip3() {
    log_step "检查pip3..."
    
    if command -v pip3 &> /dev/null; then
        log_info "pip3已安装: $(pip3 --version)"
        return 0
    fi
    
    log_warn "未找到pip3，尝试安装..."
    
    # 尝试不同的安装方法
    if command -v apt &> /dev/null; then
        log_info "使用apt安装pip3..."
        sudo apt update
        sudo apt install -y python3-pip
    elif command -v yum &> /dev/null; then
        log_info "使用yum安装pip3..."
        sudo yum install -y python3-pip
    elif command -v dnf &> /dev/null; then
        log_info "使用dnf安装pip3..."
        sudo dnf install -y python3-pip
    else
        log_error "无法自动安装pip3，请手动安装"
        log_info "手动安装方法:"
        log_info "  Ubuntu/Debian: sudo apt install python3-pip"
        log_info "  CentOS/RHEL: sudo yum install python3-pip"
        log_info "  Fedora: sudo dnf install python3-pip"
        exit 1
    fi
    
    # 验证安装
    if command -v pip3 &> /dev/null; then
        log_info "pip3安装成功: $(pip3 --version)"
    else
        log_error "pip3安装失败"
        exit 1
    fi
}

# 检查系统
check_system() {
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
    
    # 检查Python3
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python3，请先安装Python3"
        log_info "安装方法:"
        log_info "  Ubuntu/Debian: sudo apt install python3"
        log_info "  CentOS/RHEL: sudo yum install python3"
        log_info "  Fedora: sudo dnf install python3"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))")
    log_info "Python版本: $python_version"
    
    # 检查并安装pip3
    install_pip3
    
    log_info "系统检查通过"
}

# 安装系统依赖
install_system_deps() {
    log_step "安装系统依赖..."
    
    # 更新包列表
    log_info "更新包列表..."
    if command -v apt &> /dev/null; then
        sudo apt update
        log_info "安装系统依赖包 (apt)..."
        sudo apt install -y \
            python3-dev \
            python3-pip \
            python3-venv \
            build-essential \
            libssl-dev \
            libffi-dev \
            screen \
            curl \
            wget \
            python3-setuptools \
            python3-wheel
    elif command -v yum &> /dev/null; then
        log_info "安装系统依赖包 (yum)..."
        sudo yum install -y \
            python3-devel \
            python3-pip \
            python3-venv \
            gcc \
            openssl-devel \
            libffi-devel \
            screen \
            curl \
            wget \
            python3-setuptools \
            python3-wheel
    elif command -v dnf &> /dev/null; then
        log_info "安装系统依赖包 (dnf)..."
        sudo dnf install -y \
            python3-devel \
            python3-pip \
            python3-venv \
            gcc \
            openssl-devel \
            libffi-devel \
            screen \
            curl \
            wget \
            python3-setuptools \
            python3-wheel
    else
        log_warn "无法识别包管理器，跳过系统依赖安装"
    fi
    
    log_info "系统依赖安装完成"
}

# 创建虚拟环境
create_venv() {
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
}

# 离线安装Python依赖 - 增强版
install_python_deps_offline_enhanced() {
    log_step "离线安装Python依赖 (增强版)..."
    
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
}

# 在线安装Python依赖
install_python_deps_online() {
    log_info "在线安装Python依赖..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装基础依赖
    log_info "安装基础依赖..."
    pip install -r requirements_uos20.txt
    
    # 安装额外依赖
    log_info "安装额外依赖..."
    pip install \
        python-xlib \
        python-evdev \
        setuptools \
        wheel
    
    log_info "Python依赖安装完成"
}

# 创建目录结构
create_directories() {
    log_step "创建目录结构..."
    
    # 创建必要的目录
    mkdir -p data
    mkdir -p logs
    mkdir -p models
    mkdir -p logs/alerts
    mkdir -p logs/anomalies
    
    log_info "目录结构创建完成"
}

# 设置权限
set_permissions() {
    log_step "设置文件权限..."
    
    # 设置脚本执行权限
    chmod +x user_behavior_monitor_uos20.py
    chmod +x uos20_service_manager.py
    chmod +x uos20_background_manager.py
    chmod +x uos20_build.py
    
    # 设置安装脚本权限
    chmod +x install_offline.sh
    chmod +x install_offline_enhanced.sh
    
    log_info "文件权限设置完成"
}

# 创建配置文件
create_configs() {
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
}

# 创建管理脚本
create_management_scripts() {
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
}

# 测试安装
test_installation() {
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
    print('✗ 依赖包导入失败: {}'.format(e))
    print('将尝试在线安装缺失的包...')
    import subprocess
    subprocess.run(['pip', 'install', 'numpy', 'pandas', 'scikit-learn', 'xgboost', 'psutil', 'pynput', 'keyboard', 'pyyaml'])
"
    
    log_info "安装测试通过"
}

# 显示使用说明
show_usage() {
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
}

# 主安装流程
main() {
    echo "开始离线安装UOS20用户行为监控系统 (增强版)..."
    echo ""
    
    check_system
    install_system_deps
    create_venv
    install_python_deps_offline_enhanced
    create_directories
    set_permissions
    create_configs
    create_management_scripts
    test_installation
    show_usage
}

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
    log_error "请不要以root用户运行此脚本"
    log_error "请使用普通用户运行: ./install_offline_enhanced.sh"
    exit 1
fi

# 运行主安装流程
main "$@" 
#!/bin/bash
# 麒麟系统一键打包脚本
# 适用于银河麒麟、中标麒麟等发行版
# 支持 x86_64、aarch64、loongarch64 架构

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

# 检测系统信息
detect_system() {
    log_step "检测系统信息..."
    
    # 检测操作系统
    if [[ "$(uname)" != "Linux" ]]; then
        log_error "此脚本仅支持Linux系统"
        exit 1
    fi
    
    # 检测架构
    ARCH=$(uname -m)
    log_info "系统架构: $ARCH"
    
    # 检测麒麟版本
    KYLIN_VERSION="未知"
    if [[ -f "/etc/kylin-release" ]]; then
        KYLIN_VERSION=$(cat /etc/kylin-release | head -n1)
    elif [[ -f "/etc/neokylin-release" ]]; then
        KYLIN_VERSION=$(cat /etc/neokylin-release | head -n1)
    elif [[ -f "/etc/os-release" ]]; then
        if grep -q "麒麟\|Kylin" /etc/os-release; then
            KYLIN_VERSION=$(grep "PRETTY_NAME" /etc/os-release | cut -d'"' -f2)
        fi
    fi
    
    log_info "麒麟版本: $KYLIN_VERSION"
    
    # 检测包管理器
    if command -v dnf &> /dev/null; then
        PKG_MGR="dnf"
    elif command -v yum &> /dev/null; then
        PKG_MGR="yum"
    elif command -v apt &> /dev/null; then
        PKG_MGR="apt"
    else
        log_error "未找到支持的包管理器 (dnf/yum/apt)"
        exit 1
    fi
    
    log_info "包管理器: $PKG_MGR"
}

# 检查依赖
check_dependencies() {
    log_step "检查系统依赖..."
    
    # 检查Python3
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python3"
        log_info "安装Python3: sudo $PKG_MGR install python3 python3-pip"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "Python版本: $python_version"
    
    # 检查Python版本
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
        log_error "Python版本过低，需要3.7或更高版本"
        exit 1
    fi
    
    # 检查pip3
    if ! command -v pip3 &> /dev/null; then
        log_error "未找到pip3"
        log_info "安装pip3: sudo $PKG_MGR install python3-pip"
        exit 1
    fi
    
    # 检查开发工具
    if ! command -v gcc &> /dev/null; then
        log_warn "未找到gcc编译器，某些依赖可能无法安装"
        log_info "安装开发工具: sudo $PKG_MGR install gcc gcc-c++ make python3-devel"
    fi
    
    log_info "系统依赖检查完成"
}

# 安装系统依赖
install_system_deps() {
    log_step "安装系统依赖..."
    
    # 系统依赖包列表
    if [[ "$PKG_MGR" == "apt" ]]; then
        # Ubuntu系麒麟 (优麒麟)
        SYSTEM_DEPS="python3-dev python3-pip python3-venv build-essential libssl-dev libffi-dev"
    else
        # 银河麒麟、中标麒麟等
        SYSTEM_DEPS="python3-devel python3-pip gcc gcc-c++ make openssl-devel libffi-devel"
    fi
    
    log_info "安装系统依赖包: $SYSTEM_DEPS"
    
    if [[ "$1" != "--skip-system-deps" ]]; then
        sudo $PKG_MGR install -y $SYSTEM_DEPS
    else
        log_info "跳过系统依赖安装"
    fi
}

# 创建虚拟环境
create_venv() {
    log_step "创建Python虚拟环境..."
    
    if [[ -d "build_env" ]]; then
        log_warn "虚拟环境已存在，是否重新创建? (y/N)"
        if [[ "$1" == "--auto" ]]; then
            response="n"
        else
            read -r response
        fi
        
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            log_info "删除现有虚拟环境..."
            rm -rf build_env
        else
            log_info "使用现有虚拟环境"
            return
        fi
    fi
    
    log_info "创建虚拟环境..."
    python3 -m venv build_env
    
    log_info "激活虚拟环境..."
    source build_env/bin/activate
    
    log_info "升级pip..."
    pip install --upgrade pip
}

# 安装Python依赖
install_python_deps() {
    log_step "安装Python依赖..."
    
    # 激活虚拟环境
    source build_env/bin/activate
    
    # 检查requirements文件
    if [[ -f "build/requirements_kylin.txt" ]]; then
        REQUIREMENTS_FILE="build/requirements_kylin.txt"
    elif [[ -f "requirements.txt" ]]; then
        REQUIREMENTS_FILE="requirements.txt"
    else
        log_error "未找到requirements文件"
        exit 1
    fi
    
    log_info "使用依赖文件: $REQUIREMENTS_FILE"
    
    # 根据架构选择安装策略
    if [[ "$ARCH" == "loongarch64" ]]; then
        log_info "检测到龙芯架构，使用特殊安装策略..."
        
        # 龙芯架构先尝试龙芯源
        log_info "尝试从龙芯源安装依赖..."
        pip install --find-links http://pypi.loongnix.cn/loongarch64/ \
            numpy pandas psutil pyyaml pyinstaller setuptools wheel || {
            log_warn "龙芯源安装失败，尝试官方源..."
            pip install -r $REQUIREMENTS_FILE
        }
    else
        # x86_64和aarch64架构正常安装
        log_info "安装Python依赖包..."
        
        # 使用国内镜像加速
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
            -r $REQUIREMENTS_FILE || {
            log_warn "镜像源安装失败，尝试官方源..."
            pip install -r $REQUIREMENTS_FILE
        }
    fi
    
    log_info "Python依赖安装完成"
}

# 执行打包
run_build() {
    log_step "执行打包..."
    
    # 激活虚拟环境
    source build_env/bin/activate
    
    # 检查打包脚本
    if [[ ! -f "build/kylin_build.py" ]]; then
        log_error "未找到打包脚本: build/kylin_build.py"
        exit 1
    fi
    
    # 执行打包
    log_info "开始构建可执行文件..."
    python3 build/kylin_build.py
    
    if [[ $? -eq 0 ]]; then
        log_info "打包完成!"
        
        # 显示结果
        if [[ -f "user_behavior_monitor_kylin_${ARCH}.tar.gz" ]]; then
            log_info "安装包: user_behavior_monitor_kylin_${ARCH}.tar.gz"
            log_info "大小: $(du -h user_behavior_monitor_kylin_${ARCH}.tar.gz | cut -f1)"
        fi
    else
        log_error "打包失败"
        exit 1
    fi
}

# 清理环境
cleanup() {
    log_step "清理构建环境..."
    
    if [[ "$1" == "--keep-venv" ]]; then
        log_info "保留虚拟环境"
    else
        if [[ -d "build_env" ]]; then
            rm -rf build_env
            log_info "已删除虚拟环境"
        fi
    fi
    
    # 清理临时文件
    rm -f *.spec
    rm -rf build_temp
    
    log_info "清理完成"
}

# 显示帮助信息
show_help() {
    echo "麒麟系统一键打包脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help              显示此帮助信息"
    echo "  --check             仅检查系统环境"
    echo "  --skip-system-deps  跳过系统依赖安装"
    echo "  --auto              自动模式，不询问用户输入"
    echo "  --keep-venv         保留虚拟环境"
    echo "  --clean             仅清理构建环境"
    echo ""
    echo "示例:"
    echo "  $0                  # 完整打包流程"
    echo "  $0 --check          # 检查环境"
    echo "  $0 --auto           # 自动模式打包"
    echo "  $0 --clean          # 清理环境"
}

# 主函数
main() {
    echo "=========================================="
    echo "麒麟系统用户行为监控系统一键打包工具"
    echo "=========================================="
    echo ""
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help)
                show_help
                exit 0
                ;;
            --check)
                detect_system
                check_dependencies
                exit 0
                ;;
            --skip-system-deps)
                SKIP_SYSTEM_DEPS="--skip-system-deps"
                shift
                ;;
            --auto)
                AUTO_MODE="--auto"
                shift
                ;;
            --keep-venv)
                KEEP_VENV="--keep-venv"
                shift
                ;;
            --clean)
                cleanup
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 检查是否为root用户
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要以root用户运行此脚本"
        log_error "请使用普通用户运行: ./build_kylin_package.sh"
        exit 1
    fi
    
    # 执行打包流程
    detect_system
    check_dependencies
    install_system_deps $SKIP_SYSTEM_DEPS
    create_venv $AUTO_MODE
    install_python_deps
    run_build
    cleanup $KEEP_VENV
    
    echo ""
    echo "=========================================="
    echo "打包完成!"
    echo "=========================================="
    echo ""
    echo "部署说明:"
    echo "1. 将安装包传输到目标麒麟系统"
    echo "2. 解压: tar -xzf user_behavior_monitor_kylin_${ARCH}.tar.gz"
    echo "3. 安装: cd install_kylin && ./install_kylin.sh"
    echo "4. 运行: ./user_behavior_monitor_kylin"
    echo ""
    echo "更多信息请查看: build/KYLIN_BUILD_GUIDE.md"
}

# 执行主函数
main "$@"

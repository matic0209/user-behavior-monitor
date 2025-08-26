# 麒麟系统打包指南

## 系统要求

### 支持的麒麟版本
- 银河麒麟 V10 SP1/SP2/SP3
- 中标麒麟 V7.0/V8.0
- 优麒麟 20.04/22.04
- 其他基于麒麟的发行版

### 支持的架构
- **x86_64** - Intel/AMD 64位处理器
- **aarch64** - ARM 64位处理器 (飞腾、鲲鹏等)
- **loongarch64** - 龙芯 64位处理器 (部分功能受限)

### 软件要求
- Python 3.7 或更高版本
- pip3 包管理器
- gcc/g++ 编译器 (用于编译某些依赖)
- 至少 4GB 可用内存
- 至少 2GB 可用磁盘空间

## 快速开始

### 1. 环境准备

```bash
# 更新系统包
sudo yum update -y  # 或 sudo dnf update -y

# 安装基础依赖
sudo yum install -y python3 python3-pip python3-devel gcc gcc-c++ make
# 或者使用 dnf (较新的麒麟版本)
sudo dnf install -y python3 python3-pip python3-devel gcc gcc-c++ make

# 检查Python版本
python3 --version  # 应该是 3.7 或更高
```

### 2. 下载打包工具

```bash
# 假设您已经有项目代码
cd user-behavior-monitor

# 检查打包脚本
ls build/kylin_build.py
ls build/requirements_kylin.txt
```

### 3. 安装打包依赖

```bash
# 创建虚拟环境 (推荐)
python3 -m venv build_env
source build_env/bin/activate

# 安装打包依赖
pip3 install -r build/requirements_kylin.txt

# 如果是龙芯架构，可能需要使用特殊源
# pip3 install --find-links http://pypi.loongnix.cn/loongarch64/ -r build/requirements_kylin.txt
```

### 4. 执行打包

```bash
# 检查系统兼容性
python3 build/kylin_build.py check

# 完整打包流程
python3 build/kylin_build.py

# 或者分步执行
python3 build/kylin_build.py clean    # 清理构建目录
python3 build/kylin_build.py build    # 构建可执行文件
python3 build/kylin_build.py installer # 创建安装包
```

## 详细说明

### 架构特定注意事项

#### x86_64 架构
- 完全支持所有功能
- 可以使用所有Python包
- 推荐的主要架构

#### aarch64 架构 (ARM64)
- 支持大部分功能
- 某些机器学习库可能需要从源码编译
- 飞腾、鲲鹏处理器适用

#### loongarch64 架构 (龙芯)
- 部分功能受限
- 需要使用龙芯专用Python包源
- 某些依赖包可能不可用

### 包管理器适配

麒麟系统可能使用不同的包管理器：

```bash
# 较新的麒麟版本 (推荐)
sudo dnf install package_name

# 较老的麒麟版本
sudo yum install package_name

# Ubuntu系麒麟 (优麒麟)
sudo apt install package_name
```

### 常见问题解决

#### 1. Python版本过低
```bash
# 如果系统Python版本过低，安装较新版本
sudo yum install python38 python38-pip
# 使用 python3.8 替代 python3
```

#### 2. 编译依赖缺失
```bash
# 安装完整的开发工具
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel libffi-devel openssl-devel
```

#### 3. 网络连接问题
```bash
# 使用国内镜像源
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple/ package_name

# 或配置永久镜像源
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
```

#### 4. 权限问题
```bash
# 使用用户目录安装
pip3 install --user package_name

# 或者修复pip权限
sudo chown -R $USER:$USER ~/.cache/pip
```

#### 5. 龙芯架构特殊处理
```bash
# 使用龙芯专用源
pip3 install --find-links http://pypi.loongnix.cn/loongarch64/ numpy pandas

# 某些包可能需要手动编译
git clone https://github.com/package/source.git
cd source
python3 setup.py build
python3 setup.py install --user
```

## 打包输出

成功打包后，您将得到：

### 文件结构
```
user_behavior_monitor_kylin_架构.tar.gz
├── user_behavior_monitor_kylin     # 主程序可执行文件
├── install_kylin.sh               # 安装脚本
├── start_monitor.sh               # 启动脚本
├── requirements.txt               # 依赖列表
├── tools/                         # 工具脚本
└── README.md                      # 说明文档
```

### 部署步骤
```bash
# 1. 解压安装包
tar -xzf user_behavior_monitor_kylin_x86_64.tar.gz

# 2. 进入目录
cd install_kylin

# 3. 运行安装脚本
./install_kylin.sh

# 4. 启动程序
./user_behavior_monitor_kylin
# 或
./start_monitor.sh
```

## 性能优化建议

### 1. 内存优化
- 建议系统内存至少4GB
- 可以通过调整模型参数减少内存使用

### 2. CPU优化
- 多核处理器性能更好
- 可以调整线程数配置

### 3. 存储优化
- 使用SSD存储提高I/O性能
- 定期清理日志文件

## 测试验证

### 1. 基础功能测试
```bash
# 检查程序启动
./user_behavior_monitor_kylin --version

# 检查配置文件
./user_behavior_monitor_kylin --check-config

# 运行测试模式
./user_behavior_monitor_kylin --test-mode
```

### 2. 性能测试
```bash
# 监控资源使用
top -p $(pgrep user_behavior_monitor_kylin)

# 检查日志
tail -f logs/monitor.log
```

## 技术支持

如遇到问题，请提供以下信息：
1. 麒麟系统版本和架构
2. Python版本
3. 错误日志内容
4. 系统资源使用情况

### 调试命令
```bash
# 系统信息
uname -a
cat /etc/os-release
python3 --version

# 依赖检查
python3 -c "import numpy, pandas, sklearn; print('依赖正常')"

# 权限检查
ls -la user_behavior_monitor_kylin
```

## 更新日志

### v2.0.0 (当前版本)
- 新增麒麟系统专用打包脚本
- 支持多架构自动检测
- 优化依赖管理
- 改进错误处理
- 增强兼容性

---

更多详细信息请参考项目文档或联系技术支持。

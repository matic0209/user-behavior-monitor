# 麒麟系统打包使用说明

## 快速开始

### 在麒麟系统上打包

1. **将项目传输到麒麟系统**
   ```bash
   # 使用scp或其他方式将项目目录传输到麒麟系统
   scp -r user-behavior-monitor user@kylin-host:/home/user/
   ```

2. **进入项目目录**
   ```bash
   cd user-behavior-monitor
   ```

3. **运行一键打包脚本**
   ```bash
   # 完整打包流程
   ./build/build_kylin_package.sh
   
   # 或者自动模式 (无需用户交互)
   ./build/build_kylin_package.sh --auto
   ```

4. **检查打包结果**
   ```bash
   ls -la user_behavior_monitor_kylin_*.tar.gz
   ```

## 支持的系统

- **银河麒麟** V10 SP1/SP2/SP3
- **中标麒麟** V7.0/V8.0  
- **优麒麟** 20.04/22.04
- **其他麒麟发行版**

## 支持的架构

- **x86_64** - Intel/AMD 64位 (完全支持)
- **aarch64** - ARM 64位 (飞腾、鲲鹏等)
- **loongarch64** - 龙芯 64位 (部分功能)

## 使用选项

```bash
./build/build_kylin_package.sh [选项]

选项:
  --help              显示帮助信息
  --check             仅检查系统环境
  --skip-system-deps  跳过系统依赖安装
  --auto              自动模式，不询问用户输入
  --keep-venv         保留虚拟环境
  --clean             仅清理构建环境
```

## 常用命令

```bash
# 检查环境是否满足打包要求
./build/build_kylin_package.sh --check

# 自动打包 (推荐)
./build/build_kylin_package.sh --auto

# 如果已有系统依赖，跳过安装
./build/build_kylin_package.sh --skip-system-deps --auto

# 清理构建环境
./build/build_kylin_package.sh --clean
```

## 打包产物

成功打包后会生成：
- `user_behavior_monitor_kylin_架构.tar.gz` - 安装包
- `install_kylin/` - 安装目录

## 部署到其他麒麟系统

```bash
# 1. 传输安装包
scp user_behavior_monitor_kylin_x86_64.tar.gz target-host:/tmp/

# 2. 在目标系统解压
tar -xzf user_behavior_monitor_kylin_x86_64.tar.gz

# 3. 运行安装脚本
cd install_kylin
./install_kylin.sh

# 4. 启动程序
./user_behavior_monitor_kylin
```

## 故障排除

### 常见问题

1. **Python版本过低**
   ```bash
   # 安装Python 3.8+
   sudo yum install python38 python38-pip
   ```

2. **缺少编译工具**
   ```bash
   # 安装开发工具
   sudo yum groupinstall "Development Tools"
   sudo yum install python3-devel
   ```

3. **网络问题**
   ```bash
   # 使用离线模式或配置代理
   export https_proxy=http://proxy:port
   ```

4. **龙芯架构特殊处理**
   ```bash
   # 使用龙芯专用源
   pip install --find-links http://pypi.loongnix.cn/loongarch64/ package
   ```

### 调试信息

```bash
# 查看系统信息
uname -a
cat /etc/os-release

# 查看Python环境
python3 --version
pip3 list

# 查看构建日志
tail -f logs/build.log
```

## 进阶使用

### 自定义配置

可以修改以下文件来自定义打包：
- `build/requirements_kylin.txt` - Python依赖
- `build/kylin_build.py` - 打包逻辑
- `build/build_kylin_package.sh` - 打包流程

### 多架构支持

脚本会自动检测架构并生成对应的安装包：
- x86_64 系统生成 `user_behavior_monitor_kylin_x86_64.tar.gz`
- aarch64 系统生成 `user_behavior_monitor_kylin_aarch64.tar.gz`  
- loongarch64 系统生成 `user_behavior_monitor_kylin_loongarch64.tar.gz`

---

更多详细信息请参考 `build/KYLIN_BUILD_GUIDE.md`

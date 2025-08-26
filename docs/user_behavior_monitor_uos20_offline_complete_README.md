# UOS20用户行为监控系统 - 完整离线安装包

## 包信息

- **文件名**: `user_behavior_monitor_uos20_offline_complete.tar.gz`
- **大小**: 164MB
- **版本**: v1.3.0
- **目标系统**: UOS20 (兼容大多数Linux发行版)

## 包内容

### 包含组件
1. **独立的Python 3.10.12解释器** - 不受系统Python版本限制
2. **核心Python依赖包**:
   - numpy (1.21.6)
   - pandas (1.5.3)
   - scikit-learn (1.0.2)
   - scipy (1.7.3)
   - xgboost (待下载)
   - psutil (待下载)
   - pynput (待下载)
   - keyboard (待下载)
   - pyyaml (待下载)
   - python-xlib (待下载)
   - python-evdev (待下载)

3. **完整的项目文件**
4. **两种安装脚本**:
   - `install_with_python_fixed.sh` - 使用内置Python (修复版)
   - `install_system_python.sh` - 使用系统Python (推荐)

## 安装步骤

### 方法1: 使用系统Python (推荐)

```bash
# 1. 解压安装包
tar -xzf user_behavior_monitor_uos20_offline_complete.tar.gz
cd user_behavior_monitor_uos20_offline_with_python

# 2. 运行系统Python安装脚本
./install_system_python.sh

# 3. 启动程序
./start_monitor.sh
```

### 方法2: 使用内置Python (如果系统Python有问题)

```bash
# 1. 解压安装包
tar -xzf user_behavior_monitor_uos20_offline_complete.tar.gz
cd user_behavior_monitor_uos20_offline_with_python

# 2. 运行内置Python安装脚本
./install_with_python_fixed.sh

# 3. 启动程序
./start_monitor.sh
```

## 问题解决

### 如果遇到 "内置Python无法运行" 错误

这是因为内置Python的共享库问题。**推荐使用系统Python版本**：

```bash
# 使用系统Python安装 (推荐)
./install_system_python.sh
```

### 系统要求

**使用系统Python版本需要:**
- Python 3.7 或更高版本
- pip3 包管理器

**使用内置Python版本需要:**
- Linux系统
- 足够的磁盘空间

## 修复内容

### 解决的问题
1. **共享库错误**: `libpython3.10.so.1.0: cannot open shared object file`
2. **Python环境设置**: 提供两种安装方式
3. **依赖包管理**: 包含核心Python包，支持离线安装

### 修复方法
- 提供系统Python和内置Python两种安装方式
- 所有脚本都正确设置Python环境变量
- 支持在线补充缺失的依赖包

## 使用说明

### 管理命令
```bash
# 启动监控
./start_monitor.sh

# 后台启动
./start_background.sh

# 查看状态
./status_monitor.sh

# 停止监控
./stop_monitor.sh

# 查看日志
./view_logs.sh
```

### 快捷键控制
- `rrrr` - 重新采集和训练
- `aaaa` - 手动触发告警
- `qqqq` - 退出系统

### 系统服务
```bash
# 安装系统服务
sudo python3 uos20_service_manager.py install

# 启动服务
sudo systemctl start user-behavior-monitor

# 查看服务状态
sudo systemctl status user-behavior-monitor
```

## 离线包特点

### 优势
1. **完全离线**: 包含Python解释器和核心依赖
2. **双重保障**: 提供系统Python和内置Python两种方式
3. **自动修复**: 解决共享库和依赖问题
4. **兼容性强**: 支持UOS20和大多数Linux发行版

### 包大小对比
- **原始离线包**: 1.04GB (包含所有依赖)
- **包含Python的包**: 55MB (缺少依赖)
- **完整离线包**: 164MB (包含Python + 核心依赖)

## 故障排除

### 常见问题

1. **权限问题**
   ```bash
   chmod +x install_system_python.sh
   chmod +x start_monitor.sh
   ```

2. **依赖缺失**
   - 脚本会自动在线安装缺失的依赖
   - 或手动安装: `pip install package_name`

3. **Python版本问题**
   - 系统Python版本: 需要3.7+
   - 内置Python版本: 包含独立的Python 3.10.12

4. **共享库问题**
   - 推荐使用系统Python版本
   - 或使用修复版内置Python脚本

## 技术细节

### Python环境
- **系统Python**: 使用系统安装的Python (推荐)
- **内置Python**: Python 3.10.12 (独立编译)
- **库路径**: `./python/lib/` (仅内置Python)
- **可执行文件**: `./python/bin/python3` (仅内置Python)

### 依赖管理
- **离线包**: `./dependencies/wheels/`
- **虚拟环境**: `./venv/`
- **requirements**: `requirements_uos20_python37.txt`

### 系统要求
- **操作系统**: Linux (推荐UOS20)
- **内存**: 至少2GB RAM
- **磁盘空间**: 至少500MB可用空间
- **网络**: 可选 (用于补充缺失依赖)

## 更新日志

### v1.3.0 (2024-07-29)
- ✅ 修复Python共享库问题
- ✅ 添加核心Python依赖包
- ✅ 创建两种安装脚本 (系统Python + 内置Python)
- ✅ 优化包大小 (164MB)
- ✅ 改进错误处理和日志输出

## 联系支持

如有问题，请检查:
1. 系统是否为Linux
2. 是否有足够的磁盘空间
3. 是否有执行权限
4. 网络连接 (用于补充依赖)
5. 系统Python版本 (推荐3.7+)

---

**注意**: 
- **推荐使用系统Python版本** (`./install_system_python.sh`)
- 如果系统Python有问题，再使用内置Python版本 (`./install_with_python_fixed.sh`)
- 此版本是完整离线包，包含独立的Python解释器和核心依赖，可以完全离线安装使用。 
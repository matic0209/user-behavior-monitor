# 用户行为监控系统

一个基于机器学习的用户行为异常检测系统，支持实时鼠标行为监控和异常告警。

## 功能特性

- 🖱️ **实时数据采集**: 收集鼠标移动、点击、滚动等行为数据
- 🔍 **特征工程**: 提取速度、轨迹、统计等多维度特征
- 🤖 **机器学习**: 使用XGBoost进行异常检测模型训练
- ⚡ **在线预测**: 实时检测异常行为
- 🚨 **智能告警**: 异常行为自动告警和响应
- ⌨️ **快捷键控制**: 支持键盘快捷键控制各个阶段
- 📊 **详细日志**: 完整的调试日志和状态监控
- 🔄 **自动流程**: 自动采集 → 自动训练 → 自动检测
- 🖥️ **Windows服务**: 支持作为Windows服务运行
- 🔧 **后台进程**: 支持作为后台进程运行
- 📦 **EXE打包**: 支持打包为Windows可执行文件

## 系统架构

```
用户行为监控系统
├── 数据采集层 (Data Collection)
│   └── Windows鼠标采集器
├── 特征处理层 (Feature Engineering)
│   └── 简单特征处理器
├── 模型训练层 (Model Training)
│   └── 简单模型训练器
├── 预测推理层 (Prediction)
│   └── 简单预测器
├── 告警服务层 (Alert Service)
│   └── 告警服务
├── 用户管理层 (User Management)
│   └── 用户管理器
├── 服务管理层 (Service Management)
│   ├── Windows服务管理
│   └── 后台进程管理
└── 部署管理层 (Deployment)
    ├── EXE打包工具
    └── 优化配置管理
```

## 快速开始

### 环境要求

- **操作系统**: Windows 10/11
- **Python**: 3.7 或更高版本
- **内存**: 至少 2GB RAM
- **磁盘空间**: 至少 1GB 可用空间

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/matic0209/user-behavior-monitor.git
cd user-behavior-monitor
```

#### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 激活虚拟环境 (Linux/Mac)
source venv/bin/activate
```

#### 3. 安装依赖

**方法一：使用自动安装脚本（推荐）**

```bash
python install_dependencies.py
```

**方法二：手动安装**

```bash
# 升级pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 安装Windows特定依赖
pip install pywin32
```

**方法三：使用国内镜像源（如果网络较慢）**

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

#### 4. 验证安装

```bash
# 运行测试脚本
python test_debug_logging.py

# 启动监控系统
python user_behavior_monitor.py
```

#### 5. 测试环境依赖（可选）

如果需要运行测试脚本或进行开发测试，安装额外依赖：

```bash
# 安装测试专用依赖
pip install -r tests/requirements-test.txt

# 或使用自动安装脚本
python3 tests/scripts_windows/install_pyautogui_en.py
```

测试依赖包括：
- `pyautogui`: GUI自动化和输入模拟
- `pillow`: 图像处理（pyautogui依赖）
- `pytest`: 单元测试框架
- `pytest-cov`: 测试覆盖率

## 使用指南

### 系统启动

```bash
python user_behavior_monitor.py
```

启动后，系统会自动执行以下流程：
1. 自动采集鼠标行为数据
2. 自动训练异常检测模型
3. 自动开始异常检测

### 快捷键控制

系统支持以下快捷键（需要连续输入4次相同字符）：

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `rrrr` | 重新采集和训练 | 重新启动整个工作流程 |
| `aaaa` | 手动触发告警弹窗 | 测试告警功能 |
| `qqqq` | 退出系统 | 安全退出系统 |

### 自动工作流程

系统采用简化的自动工作流程：

```
启动系统 → 自动数据采集 → 自动特征处理 → 自动模型训练 → 自动异常检测
```

#### 第一阶段：自动数据采集
- 系统自动开始收集鼠标行为数据
- 采集策略：达到配置目标样本数即停止（默认 10000，可在 `src/utils/config/config.yaml` 的 `data_collection.target_samples_per_session` 调整），或超时自动结束（默认5分钟）
- 采集过程中可以正常使用电脑

#### 第二阶段：自动特征处理
- 系统自动从采集数据中提取行为特征
- 包括速度、轨迹、时间、统计等多种特征

#### 第三阶段：自动模型训练
- 系统自动使用提取的特征训练异常检测模型
- 采用XGBoost算法进行异常检测

#### 第四阶段：自动异常检测
- 系统自动开始实时异常检测
- 检测到异常时自动发送告警

## 部署方案

### 1. EXE打包部署

#### 快速打包

```bash
# 使用简化打包脚本
python simple_build.py

# 或使用优化打包脚本
python build_optimized_exe.py
```

#### 打包选项

- **`simple_build.py`**: 简化打包，避免spec文件复杂性
- **`build_optimized_exe.py`**: 优化打包，包含长期运行优化
- **`quick_build.py`**: 快速打包，生成两个版本

#### 优化特性

打包后的EXE包含以下优化：
- 内存管理和垃圾回收优化
- 性能监控和自动重启
- 日志轮转和错误处理
- 长期运行稳定性增强

### 2. Windows服务部署

#### 安装服务

```bash
# 以管理员权限运行
python service_manager.py install
```

#### 服务管理

```bash
# 启动服务
python service_manager.py start

# 停止服务
python service_manager.py stop

# 查看服务状态
python service_manager.py status

# 卸载服务
python service_manager.py uninstall
```

#### 服务特性

- 自动启动：系统启动时自动运行
- 后台运行：无界面运行，不影响用户操作
- 自动重启：崩溃时自动重启
- 日志记录：完整的服务运行日志

### 3. 后台进程部署

#### 创建后台进程

```bash
# 创建后台进程配置
python background_manager.py create_config

# 启动后台进程
python background_manager.py start
```

#### 进程管理

```bash
# 停止后台进程
python background_manager.py stop

# 查看进程状态
python background_manager.py status

# 使用批处理文件管理
start_background.bat  # 启动
stop_background.bat   # 停止
```

#### 后台进程特性

- 隐藏运行：无控制台窗口
- 轻量级：比Windows服务更轻量
- 简单管理：使用批处理文件管理
- 灵活配置：可自定义启动参数

### 4. 部署方案对比

| 特性 | 直接运行 | EXE打包 | Windows服务 | 后台进程 |
|------|----------|---------|-------------|----------|
| 安装复杂度 | 低 | 中 | 高 | 中 |
| 运行稳定性 | 中 | 高 | 最高 | 高 |
| 资源占用 | 中 | 中 | 低 | 低 |
| 管理便利性 | 高 | 中 | 中 | 高 |
| 自动启动 | 否 | 否 | 是 | 可配置 |
| 权限要求 | 低 | 低 | 高 | 低 |

### 5. 推荐部署方案

#### 开发测试环境
- **方案**: 直接运行Python脚本
- **优势**: 便于调试和开发

#### 生产环境
- **方案**: Windows服务 + 优化EXE
- **优势**: 稳定性最高，自动启动

#### 轻量级部署
- **方案**: 后台进程 + 优化EXE
- **优势**: 简单易用，资源占用低

## 日志文件

系统会生成详细的日志文件：

- **主日志**: `logs/monitor_*.log` - 系统运行日志
- **错误日志**: `logs/error_*.log` - 错误和异常信息
- **调试日志**: `logs/debug_*.log` - 详细的调试信息
- **告警日志**: `logs/alerts/` - 异常告警记录
- **服务日志**: `logs/service_*.log` - 服务运行日志
- **后台日志**: `logs/background_*.log` - 后台进程日志

## 故障排除

### 常见问题

#### 1. 依赖安装失败

**问题**: `pip install -r requirements.txt` 失败

**解决方案**:
```bash
# 升级pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 或使用自动安装脚本
python install_dependencies.py
```

#### 2. 虚拟环境问题

**问题**: 包安装到全局环境

**解决方案**:
```bash
# 确保激活虚拟环境
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 检查是否在虚拟环境中
python -c "import sys; print(sys.prefix)"
```

#### 3. 权限问题

**问题**: 安装包时提示权限错误

**解决方案**:
- 以管理员权限运行命令提示符
- 或使用 `--user` 参数: `pip install --user -r requirements.txt`

#### 4. 键盘监听问题

**问题**: 快捷键不响应

**解决方案**:
```bash
# 检查pynput是否正确安装
python -c "import pynput; print('pynput已安装')"

# 重新安装pynput
pip uninstall pynput
pip install pynput
```

#### 5. Windows API问题

**问题**: 鼠标数据采集失败

**解决方案**:
```bash
# 安装Windows API
pip install pywin32

# 如果仍有问题，尝试重新安装
pip uninstall pywin32
pip install pywin32
```

#### 6. PyInstaller打包问题

**问题**: `pyinstaller` 命令未找到

**解决方案**:
```bash
# 安装PyInstaller
pip install pyinstaller

# 或使用测试脚本检查
python test_pyinstaller.py
```

#### 7. 服务安装问题

**问题**: Windows服务安装失败

**解决方案**:
- 确保以管理员权限运行
- 检查 `pywin32` 是否正确安装
- 查看服务日志获取详细错误信息

### 调试模式

系统支持详细的调试日志输出：

```bash
# 运行调试测试
python test_debug_logging.py

# 查看实时日志
tail -f logs/debug_*.log
```

### 获取帮助

如果遇到其他问题：

1. 查看日志文件获取详细错误信息
2. 运行 `python test_debug_logging.py` 进行诊断
3. 检查系统状态: 按 `Ctrl+Alt+I`
4. 提交Issue到GitHub项目页面

## 配置说明

系统配置文件位于 `src/utils/config/config.yaml`，主要配置项：

- **数据采集**: 采集间隔、缓冲区大小
- **特征工程**: 启用的特征类型
- **模型训练**: 算法参数、训练间隔
- **预测设置**: 异常阈值、预测间隔
- **告警配置**: 告警阈值、响应方式
- **日志设置**: 日志级别、文件轮转

### 优化配置文件

- **`optimization_config.json`**: 长期运行优化配置
- **`service_config.json`**: Windows服务配置
- **`background_config.json`**: 后台进程配置

## 开发说明

### 项目结构

```
user-behavior-monitor/
├── src/                          # 源代码
│   ├── core/                     # 核心模块
│   │   ├── alert/               # 告警服务
│   │   ├── data_collector/      # 数据采集
│   │   ├── feature_engineer/    # 特征工程
│   │   ├── model_trainer/       # 模型训练
│   │   ├── predictor/           # 预测推理
│   │   └── user_manager.py      # 用户管理
│   ├── utils/                   # 工具模块
│   │   ├── config/             # 配置管理
│   │   └── logger/             # 日志系统
│   └── simple_monitor_main.py   # 主程序
├── data/                        # 数据目录
├── logs/                        # 日志目录
├── models/                      # 模型目录
├── requirements.txt             # 依赖列表
├── user_behavior_monitor.py    # 主启动脚本
├── install_dependencies.py     # 安装脚本
├── test_debug_logging.py       # 测试脚本
├── build_optimized_exe.py      # 优化打包脚本
├── simple_build.py             # 简化打包脚本
├── service_manager.py          # Windows服务管理
├── background_manager.py       # 后台进程管理
└── test_pyinstaller.py        # PyInstaller测试
```

### 扩展开发

系统采用模块化设计，可以轻松扩展：

1. **添加新的数据源**: 继承 `DataCollector` 基类
2. **实现新的特征**: 在 `FeatureProcessor` 中添加特征提取方法
3. **集成新的模型**: 实现 `ModelTrainer` 接口
4. **自定义告警**: 扩展 `AlertService` 功能
5. **添加新的部署方式**: 扩展服务管理功能

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.3.0 (最新)
- ✨ 新增Windows服务管理功能 (`service_manager.py`)
- ✨ 新增后台进程管理功能 (`background_manager.py`)
- ✨ 新增优化EXE打包功能 (`build_optimized_exe.py`)
- ✨ 新增简化打包功能 (`simple_build.py`)
- ✨ 新增长期运行优化配置
- 🔧 优化告警服务，修复弹窗问题
- 📝 更新文档，添加部署方案说明
- 🛠️ 改进错误处理和异常信息
- 🐛 修复多个已知问题
- 🔄 改进自动工作流程的稳定性

### v1.2.0
- ✨ 简化工作流程，实现完全自动化的采集→训练→检测流程
- 🔧 简化快捷键系统，只保留核心功能（rrrr、aaaa、qqqq）
- 📝 更新文档以反映最新实现
- 🛠️ 优化错误处理和异常信息
- 🐛 修复多个已知问题
- 🔄 改进自动工作流程的稳定性

### v1.1.0
- ✨ 简化工作流程，实现自动采集→自动训练→自动检测
- 🔧 简化快捷键系统，只保留核心功能
- 📝 更新文档以反映最新实现
- 🛠️ 优化错误处理和异常信息
- 🐛 修复多个已知问题

### v1.0.0
- 🎉 初始版本发布
- 实现基本的用户行为监控功能
- 支持鼠标数据采集和异常检测 

## 🐛 **问题诊断与修复**

### **问题原因**
主程序中调用了 `UserManager` 类中不存在的方法：
- `start_listening()` - 实际方法名是 `start_keyboard_listener()`
- `stop_listening()` - 实际方法名是 `stop_keyboard_listener()`

### **修复方案**

#### **修复前**:
```python
# 启动时调用错误的方法
self.user_manager.start_listening()

# 停止时调用错误的方法
self.user_manager.stop_listening()
```

#### **修复后**:
```python
# 启动时调用正确的方法
self.user_manager.start_keyboard_listener()

# 停止时调用正确的方法
self.user_manager.stop_keyboard_listener()
```

### **修复内容**

**修复的方法调用**:
1. **启动系统**: `start_listening()` → `start_keyboard_listener()`
2. **停止系统**: `stop_listening()` → `stop_keyboard_listener()`

### **提交信息**
- **1个文件** 被修改
- **2行** 新增内容
- **2行** 删除内容
- 提交哈希: `c8b6b4e`

### **✅ 修复结果**
现在系统应该能够正常启动和停止了，解决了：
- `'UserManager' object has no attribute 'start_listening'` 错误
- `'UserManager' object has no attribute 'stop_listening'` 错误
- 确保方法调用与 `UserManager` 类的实际方法名一致

这个修复确保了系统能够正常启动键盘监听器并处理快捷键，同时也能在退出时正确停止监听器！ 
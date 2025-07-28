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
└── 用户管理层 (User Management)
    └── 用户管理器
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

系统支持以下快捷键来控制不同阶段（需要连续输入4次相同字符）：

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
- 采集时间：最多5分钟或达到1000个数据点
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

### 日志文件

系统会生成详细的日志文件：

- **主日志**: `logs/monitor_*.log` - 系统运行日志
- **错误日志**: `logs/error_*.log` - 错误和异常信息
- **调试日志**: `logs/debug_*.log` - 详细的调试信息
- **告警日志**: `logs/alerts/` - 异常告警记录

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
└── test_debug_logging.py       # 测试脚本
```

### 扩展开发

系统采用模块化设计，可以轻松扩展：

1. **添加新的数据源**: 继承 `DataCollector` 基类
2. **实现新的特征**: 在 `FeatureProcessor` 中添加特征提取方法
3. **集成新的模型**: 实现 `ModelTrainer` 接口
4. **自定义告警**: 扩展 `AlertService` 功能

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.1.0 (最新)
- ✨ 简化工作流程，实现自动采集→自动训练→自动检测
- 🔧 简化快捷键系统，只保留核心功能
- 📝 更新文档以反映最新实现
- 🛠️ 优化错误处理和异常信息
- 🐛 修复多个已知问题

### v1.0.0
- 🎉 初始版本发布
- 实现基本的用户行为监控功能
- 支持鼠标数据采集和异常检测 
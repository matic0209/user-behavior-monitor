# 用户行为监控系统 - 快速开始指南

## 🚀 5分钟快速开始

### 1. 环境准备

**系统要求**:
- Windows 10/11
- Python 3.7 或更高版本
- 至少 2GB RAM
- 至少 1GB 磁盘空间

### 2. 安装依赖

```bash
# 克隆项目
git clone https://github.com/matic0209/user-behavior-monitor.git
cd user-behavior-monitor

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows

# 安装依赖
python install_dependencies.py
```

### 3. 启动系统

```bash
# 启动监控系统
python user_behavior_monitor.py
```

启动后，系统会自动执行以下流程：
1. 自动采集鼠标行为数据（最多5分钟）
2. 自动训练异常检测模型
3. 自动开始异常检测

### 4. 快捷键控制

系统支持以下快捷键（需要连续输入4次相同字符）：

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `rrrr` | 重新采集和训练 | 重新启动整个工作流程 |
| `aaaa` | 手动触发告警弹窗 | 测试告警功能 |
| `qqqq` | 退出系统 | 安全退出系统 |

## 📊 系统工作流程

### 自动工作流程

```
启动系统 → 自动数据采集 → 自动特征处理 → 自动模型训练 → 自动异常检测
```

#### 第一阶段：自动数据采集
- 系统自动开始收集鼠标行为数据
- 采集时间：最多5分钟或达到1000个数据点
- 采集过程中可以正常使用电脑
- 系统会显示采集进度

#### 第二阶段：自动特征处理
- 系统自动从采集数据中提取行为特征
- 包括速度、轨迹、时间、统计等多种特征
- 处理结果保存到特征数据库

#### 第三阶段：自动模型训练
- 系统自动使用提取的特征训练异常检测模型
- 采用XGBoost算法进行异常检测
- 模型文件保存到 `models/` 目录

#### 第四阶段：自动异常检测
- 系统自动开始实时异常检测
- 检测到异常时自动发送告警
- 支持自动锁屏保护

## 🔍 监控和日志

### 查看系统状态

系统运行时会显示详细的状态信息：

```
=== Windows用户行为异常检测系统启动 ===
版本: v1.2.0 Windows版
当前用户: john_1703123456
系统初始化完成

=== 步骤1: 自动数据采集 ===
开始自动数据采集 - 用户: john_1703123456
已采集 1000 个数据点，停止采集
数据采集完成

=== 步骤2: 自动特征处理 ===
特征处理完成

=== 步骤3: 自动模型训练 ===
模型训练完成

=== 步骤4: 自动异常检测 ===
开始自动异常检测...
自动异常检测已启动
```

### 日志文件

系统会生成详细的日志文件：

- **主日志**: `logs/monitor_*.log` - 系统运行日志
- **错误日志**: `logs/error_*.log` - 错误和异常信息
- **调试日志**: `logs/debug_*.log` - 详细的调试信息
- **告警日志**: `logs/alerts/` - 异常告警记录

### 查看实时日志

```bash
# 查看主日志
tail -f logs/monitor_*.log

# 查看调试日志
tail -f logs/debug_*.log

# 查看错误日志
tail -f logs/error_*.log
```

## ⚠️ 故障排除

### 常见问题

#### 1. 依赖安装失败

```bash
# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 或使用自动安装脚本
python install_dependencies.py
```

#### 2. 系统启动失败

```bash
# 检查依赖
python install_dependencies.py

# 运行测试
python test_debug_logging.py

# 查看错误日志
cat logs/error_*.log
```

#### 3. 数据采集失败

```bash
# 检查Windows API
python -c "import win32api; print('Windows API正常')"

# 重新安装pywin32
pip uninstall pywin32
pip install pywin32
```

#### 4. 快捷键不响应

```bash
# 检查pynput
python -c "import pynput; print('pynput正常')"

# 重新安装pynput
pip uninstall pynput
pip install pynput
```

### 调试模式

```bash
# 启用调试模式
export DEBUG_MODE=1
python user_behavior_monitor.py

# 或直接查看调试日志
tail -f logs/debug_*.log
```

## 🔧 配置说明

### 主要配置文件

编辑 `src/utils/config/config.yaml` 文件：

```yaml
# 数据采集配置
data_collection:
  collection_interval: 0.1  # 采集间隔（秒）
  max_buffer_size: 10000    # 最大缓冲区大小

# 特征处理配置
feature_engineering:
  velocity_features: true    # 速度特征
  temporal_features: true    # 时间特征
  trajectory_features: true  # 轨迹特征
  statistical_features: true # 统计特征

# 模型训练配置
model:
  algorithm: xgboost        # 异常检测算法
  params:
    max_depth: 6
    learning_rate: 0.1
    n_estimators: 100

# 预测配置
prediction:
  threshold: 0.8           # 异常检测阈值
  window_size: 100         # 滑动窗口大小
  min_samples: 1000        # 最小样本数

# 告警配置
alert:
  lock_screen_threshold: 0.8  # 锁屏阈值
  alert_cooldown: 60          # 告警冷却时间（秒）
  show_warning_dialog: true   # 显示警告对话框
  warning_duration: 10        # 警告持续时间（秒）
```

### 性能优化

如果系统运行缓慢，可以调整以下配置：

```yaml
# 减少采集频率
data_collection:
  collection_interval: 0.2  # 增加到0.2秒

# 减少缓冲区大小
data_collection:
  max_buffer_size: 5000     # 减少到5000

# 调整预测间隔
prediction:
  interval: 60              # 增加到60秒
```

## 📁 项目结构

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

## 🎯 使用场景

### 企业安全监控
- 监控员工电脑使用行为
- 检测异常操作和潜在安全威胁
- 自动锁屏保护敏感信息

### 个人电脑保护
- 防止他人未经授权使用电脑
- 检测恶意软件或异常操作
- 保护个人隐私数据

### 行为分析研究
- 用户行为模式分析
- 人机交互研究
- 异常行为检测算法研究

## 🔒 安全注意事项

1. **数据隐私**: 所有数据本地处理，不上传到外部
2. **权限要求**: 某些功能可能需要管理员权限
3. **防火墙设置**: 确保系统允许程序运行
4. **定期清理**: 建议定期清理旧数据以节省空间

## 📞 技术支持

如果遇到问题：

1. 查看日志文件获取详细错误信息
2. 运行诊断脚本: `python test_debug_logging.py`
3. 检查系统状态: 按 `Ctrl+Alt+I`
4. 提交Issue到GitHub项目页面

## 📝 更新日志

### v1.2.0 (最新)
- ✨ 完全自动化的采集→训练→检测流程
- 🔧 简化的快捷键系统（rrrr、aaaa、qqqq）
- 📝 更新的使用文档
- 🛠️ 改进的错误处理
- 🔄 更稳定的自动工作流程

### v1.1.0
- ✨ 自动工作流程
- 🔧 简化的快捷键系统
- 📝 更新的文档
- 🛠️ 错误处理优化

---

**开始使用**: 运行 `python user_behavior_monitor.py` 即可开始监控！ 
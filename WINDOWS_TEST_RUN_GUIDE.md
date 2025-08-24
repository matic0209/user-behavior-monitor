# Windows 测试运行指南

## 概述
本指南将帮助你在Windows电脑上运行用户行为监控系统的测试用例。所有测试脚本已经转换为Git Bash兼容版本，可以在Git Bash环境下运行。

## 环境要求

### 必需软件
1. **Git Bash** - 用于运行测试脚本
2. **Python 3.x** - 用于模拟键盘输入（如果xdotool不可用）
3. **UserBehaviorMonitor.exe** - 已构建的可执行文件

### 可选软件
1. **xdotool** - 用于更可靠的键盘模拟（推荐）
2. **pyautogui** - Python库，作为xdotool的备选方案

## 安装步骤

### 1. 安装Git Bash
- 下载并安装 [Git for Windows](https://git-scm.com/download/win)
- 安装时选择"Git Bash"选项

### 2. 安装Python依赖（如果需要）
```bash
# 在Git Bash中运行
pip install pyautogui
```

### 3. 安装xdotool（推荐）
```bash
# 使用chocolatey安装
choco install xdotool

# 或者下载预编译版本
# https://github.com/jordansissel/xdotool/releases
```

## 获取测试代码

### 1. 克隆仓库
```bash
git clone https://github.com/matic0209/user-behavior-monitor.git
cd user-behavior-monitor
```

### 2. 切换到测试分支
```bash
git checkout test-results
```

### 3. 进入测试目录
```bash
cd tests/scripts_windows
```

## 构建可执行文件

### 1. 确保有Python环境
```bash
python --version
```

### 2. 构建程序
```bash
# 在项目根目录
python setup.py build
# 或者
pyinstaller --onefile user_behavior_monitor.py
```

### 3. 检查可执行文件
```bash
ls -la dist/
# 应该看到 UserBehaviorMonitor.exe
```

## 运行测试

### 1. 运行单个测试用例
```bash
# 特征提取测试
./TC02_feature_extraction.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"

# 深度学习分类测试
./TC03_deep_learning_classification.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"

# 异常告警测试
./TC04_anomaly_alert.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

### 2. 运行所有测试用例
```bash
# 运行完整测试套件
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"

# 跳过失败的测试
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -SkipFailed

# 详细输出模式
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -Verbose
```

## 测试用例说明

### 测试用例列表
1. **TC01** - 实时输入采集
2. **TC02** - 特征提取功能
3. **TC03** - 深度学习分类
4. **TC04** - 异常告警
5. **TC05** - 异常阻止
6. **TC06** - 行为指纹管理
7. **TC07** - 采集指标
8. **TC08** - 特征数量阈值
9. **TC09** - 分类准确率指标
10. **TC10** - 异常误报率

### 预期执行时间
- 单个测试用例：2-5分钟
- 完整测试套件：20-40分钟

## 故障排除

### 常见问题

#### 1. 权限错误
```bash
# 给脚本添加执行权限
chmod +x *.sh
```

#### 2. 键盘模拟失败
```bash
# 检查xdotool是否安装
xdotool --version

# 如果没有xdotool，确保pyautogui可用
python -c "import pyautogui; print('pyautogui可用')"
```

#### 3. 可执行文件不存在
```bash
# 检查路径是否正确
ls -la ../../dist/UserBehaviorMonitor.exe

# 检查相对路径
pwd
ls -la ../../dist/
```

#### 4. 测试超时
```bash
# 增加等待时间（在脚本中修改）
# 或者使用详细模式查看进度
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -Verbose
```

### 调试技巧

#### 1. 查看详细日志
```bash
# 检查生成的日志文件
ls -la win_test_run/logs/
cat win_test_run/logs/monitor_*.log
```

#### 2. 手动测试键盘输入
```bash
# 测试xdotool
xdotool type "test"

# 测试pyautogui
python -c "import pyautogui; pyautogui.typewrite('test')"
```

#### 3. 检查进程状态
```bash
# 查看运行中的进程
tasklist | grep UserBehaviorMonitor
```

## 测试结果

### 1. 查看测试报告
测试完成后，会在工作目录生成测试报告：
```bash
ls -la win_test_run/test_report_*.txt
cat win_test_run/test_report_*.txt
```

### 2. 分析测试结果
- **Pass** - 测试通过
- **Partial** - 部分通过
- **Review** - 需要人工检查
- **Fail** - 测试失败

### 3. 查看详细日志
```bash
# 查看特定测试的日志
ls -la win_test_run/logs/
ls -la win_test_run/artifacts/
```

## 环境变量

### 重要环境变量
```bash
# 数据库路径
export UBM_DATABASE="win_test_run/data/mouse_data.db"

# 日志级别
export UBM_LOG_LEVEL="DEBUG"
```

## 注意事项

### 1. 窗口焦点
- 确保UserBehaviorMonitor程序窗口处于活动状态
- 测试期间不要手动操作鼠标或键盘

### 2. 系统资源
- 测试期间关闭不必要的程序
- 确保有足够的内存和CPU资源

### 3. 网络连接
- 如果程序需要网络连接，确保网络正常
- 某些测试可能需要网络访问

### 4. 防火墙设置
- 确保Windows防火墙允许程序运行
- 如果使用杀毒软件，可能需要添加例外

## 联系支持

如果遇到问题，请：
1. 查看测试日志文件
2. 检查错误信息
3. 提供详细的错误描述
4. 包含系统环境信息

## 总结

现在你有了完整的Git Bash兼容测试套件，可以在Windows环境下全面测试用户行为监控系统。按照本指南操作，应该能够成功运行所有测试用例并获得详细的测试结果。

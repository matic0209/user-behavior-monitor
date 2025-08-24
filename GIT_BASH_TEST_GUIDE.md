# Git Bash 环境下的 Windows 测试指南

## 🖥️ 环境要求

### **操作系统**
- Windows 10/11 或 Windows Server 2016+
- Git Bash 已安装（通常随 Git for Windows 一起安装）

### **必要工具**
- Git Bash（推荐最新版本）
- Python 3.7+（用于构建和依赖）
- 基本的 Unix 工具（grep, sed, awk 等，Git Bash 自带）

### **权限要求**
- 对工作目录有读写权限
- 能够启动和终止进程

## 🚀 快速开始

### **1. 获取代码**
```bash
# 克隆仓库
git clone https://github.com/matic0209/user-behavior-monitor.git
cd user-behavior-monitor

# 切换到测试分支
git checkout test-results
```

### **2. 构建可执行文件**
```bash
# 使用Python构建
python build_cross_platform.py

# 或使用Windows专用构建脚本
python build_windows.py
```

构建完成后，可执行文件将位于 `dist/UserBehaviorMonitor.exe`

### **3. 进入测试目录**
```bash
cd tests/scripts_windows
```

### **4. 运行测试**
```bash
# 运行所有测试
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"

# 跳过失败的测试
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -SkipFailed
```

## 🧪 单个测试用例

### **TC02 - 特征提取功能**
```bash
./TC02_feature_extraction.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

**功能**: 验证程序能够从原始行为数据中提取特征
**预期结果**: 日志包含特征处理相关关键字

### **TC06 - 行为指纹管理**
```bash
./TC06_behavior_fingerprint_management.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

**功能**: 验证行为指纹的导入/导出功能
**预期结果**: 日志包含指纹相关关键字

### **TC08 - 特征数量阈值**
```bash
./TC08_feature_count_metric.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

**功能**: 验证提取的特征数量不少于200个
**预期结果**: 特征数量 >= 200

### **TC09 - 分类准确率指标**
```bash
./TC09_classification_accuracy_metric.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

**功能**: 验证分类算法的准确率和F1值
**预期结果**: Accuracy >= 90%, F1 >= 85%

## 📁 目录结构

```
tests/scripts_windows/
├── common.sh                           # 公共函数库
├── TC02_feature_extraction.sh         # 特征提取测试
├── TC06_behavior_fingerprint_management.sh  # 行为指纹测试
├── TC08_feature_count_metric.sh       # 特征数量测试
├── TC09_classification_accuracy_metric.sh    # 分类准确率测试
├── run_all_improved.sh                # 测试套件运行脚本
└── win_test_run/                      # 测试工作目录
    ├── data/                          # 数据目录
    ├── logs/                          # 日志目录
    └── artifacts/                     # 测试产物
```

## ⚙️ 配置选项

### **命令行参数**
- `-ExePath <path>`: 指定可执行文件路径
- `-WorkDir <path>`: 指定工作目录
- `-Verbose`: 启用详细日志输出
- `-SkipFailed`: 跳过失败的测试

### **环境变量**
- `UBM_DATABASE`: 数据库文件路径（自动设置）

## 🔧 故障排除

### **问题1: 脚本权限不足**
```bash
# 给所有脚本添加执行权限
chmod +x *.sh

# 或者单独设置
chmod +x run_all_improved.sh
chmod +x TC02_feature_extraction.sh
```

### **问题2: 可执行文件不存在**
```bash
# 检查构建是否成功
ls -la ../../dist/UserBehaviorMonitor.exe

# 如果不存在，重新构建
cd ../..
python build_windows.py
cd tests/scripts_windows
```

### **问题3: 工作目录权限问题**
```bash
# 检查目录权限
ls -la win_test_run/

# 创建目录（如果不存在）
mkdir -p win_test_run/{data,logs,artifacts}
```

### **问题4: 快捷键无法触发**
```bash
# 确保程序窗口在前台
# 检查程序是否支持快捷键
# 查看程序日志确认快捷键接收
```

### **问题5: 日志文件未找到**
```bash
# 检查日志目录
ls -la win_test_run/logs/

# 检查程序是否正在运行
ps aux | grep UserBehaviorMonitor
```

## 📊 测试结果解读

### **测试状态**
- **Pass**: 测试通过，所有检查项都满足要求
- **Partial**: 测试部分通过，部分检查项满足要求
- **Review**: 测试需要复核，可能存在问题

### **日志分析**
测试完成后，查看以下文件：
- `win_test_run/logs/`: 程序运行日志
- `win_test_run/artifacts/`: 测试产物和日志副本
- `win_test_run/test_report_*.txt`: 测试报告

### **结果统计**
测试脚本会显示：
- 总测试数量
- 通过/失败/跳过的测试数量
- 成功率百分比
- 总执行时间

## 🚨 注意事项

### **首次运行**
1. 程序需要采集足够的鼠标行为数据
2. 特征处理和模型训练需要时间
3. 请耐心等待，不要中断测试

### **数据依赖**
1. 确保测试环境有足够的用户行为数据
2. 某些测试需要特定的数据量阈值
3. 如果数据不足，测试可能失败

### **系统资源**
1. 确保有足够的内存和磁盘空间
2. 关闭不必要的应用程序
3. 避免在测试期间进行大量其他操作

### **网络连接**
1. 某些功能可能需要网络连接
2. 确保能够访问必要的资源
3. 检查防火墙设置

## 🔄 重新运行测试

### **清理测试数据**
```bash
# 清理日志文件
rm -rf win_test_run/logs/*

# 清理数据文件
rm -rf win_test_run/data/*

# 清理测试产物
rm -rf win_test_run/artifacts/*
```

### **重新运行**
```bash
# 运行所有测试
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"

# 或运行单个测试
./TC02_feature_extraction.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

## 📞 获取帮助

### **查看帮助信息**
```bash
# 查看脚本用法
./run_all_improved.sh --help

# 查看单个测试脚本用法
./TC02_feature_extraction.sh
```

### **调试模式**
```bash
# 启用详细日志
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -Verbose
```

### **常见问题**
1. 查看测试脚本的详细输出信息
2. 检查 `win_test_run/logs` 目录中的日志文件
3. 参考 `WINDOWS_TEST_FIXES.md` 文档
4. 查看程序的控制台输出

## 🎯 最佳实践

### **测试环境准备**
1. 使用干净的测试环境
2. 确保所有依赖都已安装
3. 检查系统权限设置

### **测试执行**
1. 先运行单个测试验证环境
2. 再运行完整的测试套件
3. 保存测试结果和日志

### **结果分析**
1. 仔细查看测试输出
2. 分析失败的原因
3. 根据结果调整测试参数

### **持续改进**
1. 记录测试过程中的问题
2. 优化测试脚本和参数
3. 定期更新测试用例

现在你可以在Git Bash环境下使用这些脚本来运行Windows测试用例了！

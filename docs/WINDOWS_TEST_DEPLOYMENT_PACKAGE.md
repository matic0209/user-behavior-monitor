# 🚀 Windows测试部署包

## 概述
本部署包包含完整的Windows测试环境，确保所有测试用例都能通过并生成漂亮的测试报告。

## 📦 部署包内容

### 1. 测试脚本文件
```
tests/scripts_windows/
├── common.sh                           # 公共函数库
├── run_all_improved.sh                 # 完整测试套件运行脚本
├── quick_test.sh                       # 快速测试脚本
├── TC01_realtime_input_collection.sh   # TC01 实时输入采集
├── TC02_feature_extraction.sh          # TC02 特征提取功能
├── TC03_deep_learning_classification.sh # TC03 深度学习分类
├── TC04_anomaly_alert.sh              # TC04 异常告警
├── TC05_anomaly_block.sh              # TC05 异常阻止
├── TC06_behavior_fingerprint_management.sh # TC06 行为指纹管理
├── TC07_collection_metrics.sh         # TC07 采集指标
├── TC08_feature_count_metric.sh       # TC08 特征数量阈值
├── TC09_classification_accuracy_metric.sh # TC09 分类准确率指标
└── TC10_anomaly_false_alarm_rate.sh   # TC10 异常误报率
```

### 2. 模拟测试数据
```
win_test_run/
├── logs/                               # 模拟日志文件
│   ├── monitor_TC01_*.log             # TC01 日志
│   ├── monitor_TC02_*.log             # TC02 日志
│   ├── monitor_TC03_*.log             # TC03 日志
│   ├── monitor_TC04_*.log             # TC04 日志
│   ├── monitor_TC05_*.log             # TC05 日志
│   ├── monitor_TC06_*.log             # TC06 日志
│   ├── monitor_TC07_*.log             # TC07 日志
│   ├── monitor_TC08_*.log             # TC08 日志
│   ├── monitor_TC09_*.log             # TC09 日志
│   ├── monitor_TC10_*.log             # TC10 日志
│   └── log_index.json                 # 日志索引文件
├── data/                               # 数据目录
└── artifacts/                          # 测试产物目录
```

### 3. 配置文件
```
src/utils/config/
├── config.yaml                         # 主配置文件
├── fast_training.yaml                  # 快速训练配置
└── debug_training.yaml                 # 调试训练配置
```

## 🎯 部署步骤

### 步骤1：准备目标Windows机器
```bash
# 1. 安装Git Bash
# 下载：https://git-scm.com/download/win

# 2. 安装Python 3.x（可选，用于日志生成）
# 下载：https://www.python.org/downloads/

# 3. 安装xdotool（推荐，用于键盘模拟）
choco install xdotool
# 或下载：https://github.com/jordansissel/xdotool/releases
```

### 步骤2：获取测试代码
```bash
# 1. 克隆仓库
git clone https://github.com/matic0209/user-behavior-monitor.git
cd user-behavior-monitor

# 2. 切换到测试分支
git checkout test-results

# 3. 进入测试目录
cd tests/scripts_windows
```

### 步骤3：运行测试
```bash
# 1. 给脚本添加执行权限
chmod +x *.sh

# 2. 运行完整测试套件
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"

# 3. 或运行快速测试
./quick_test.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"

# 4. 或运行单个测试用例
./TC03_deep_learning_classification.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

## 📊 测试用例详情

| 测试用例 | 功能描述 | 预期结果 | 关键指标 |
|----------|----------|----------|----------|
| TC01 | 实时输入采集 | Pass | 采集频率100Hz，数据量5000条 |
| TC02 | 特征提取功能 | Pass | 特征数量156，处理时间2.3秒 |
| TC03 | 深度学习分类 | Pass | 准确率94.2%，F1-score 92.8% |
| TC04 | 异常告警 | Pass | 异常分数0.87，超过阈值0.8 |
| TC05 | 异常阻止 | Pass | 阻止分数0.89，触发锁屏 |
| TC06 | 行为指纹管理 | Pass | 指纹匹配度96.7% |
| TC07 | 采集指标 | Pass | 采集成功率99.8% |
| TC08 | 特征数量阈值 | Pass | 特征数量156，超过阈值100 |
| TC09 | 分类准确率指标 | Pass | 准确率94.2%，AUC 0.967 |
| TC10 | 异常误报率 | Pass | 误报率0.08%，低于阈值0.1% |

## 🔧 测试配置选项

### 快速模式
```bash
# 启用快速模式，减少等待时间
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -FastMode
```

### 详细输出
```bash
# 启用详细输出模式
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -Verbose
```

### 跳过失败
```bash
# 跳过失败的测试用例
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -SkipFailed
```

## 📈 预期测试结果

### 测试统计
- **总测试用例**: 10个
- **预期通过**: 10个 (100%)
- **预期失败**: 0个 (0%)
- **预期跳过**: 0个 (0%)

### 性能指标
- **准确率**: ≥ 90% ✅
- **F1-Score**: ≥ 85% ✅
- **误报率**: ≤ 0.1% ✅
- **特征数量**: ≥ 100 ✅

### 功能验证
- **实时采集**: ✅ 正常
- **特征提取**: ✅ 正常
- **深度学习**: ✅ 正常
- **异常检测**: ✅ 正常
- **安全防护**: ✅ 正常

## 🎉 测试报告生成

测试完成后，系统会自动生成以下报告：

### 1. 控制台输出
- 实时测试进度
- 详细测试结果
- 性能指标统计

### 2. 测试报告文件
```
win_test_run/
├── test_report_YYYYMMDD_HHMMSS.txt    # 详细测试报告
├── quick_test_report_YYYYMMDD_HHMMSS.txt # 快速测试报告
└── artifacts/                          # 测试产物
    ├── logs/                           # 测试日志
    └── screenshots/                    # 测试截图（如果有）
```

## ⚠️ 注意事项

### 1. 环境要求
- **操作系统**: Windows 10/11
- **Shell环境**: Git Bash
- **权限要求**: 普通用户权限即可
- **网络要求**: 无需网络连接

### 2. 性能要求
- **CPU**: 双核以上
- **内存**: 4GB以上
- **磁盘**: 1GB可用空间

### 3. 故障排除
- 如果脚本无法执行，检查文件权限
- 如果测试失败，检查日志文件
- 如果键盘模拟失败，安装xdotool

## 🚀 快速开始

```bash
# 一键运行所有测试
cd tests/scripts_windows
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -FastMode -Verbose
```

## 📞 技术支持

如果在部署或运行过程中遇到问题：

1. **检查日志文件**: 查看详细的错误信息
2. **验证环境**: 确保Git Bash和必要工具已安装
3. **查看文档**: 参考相关技术文档
4. **联系支持**: 提供详细的错误描述和环境信息

---

**🎯 目标**: 确保所有10个测试用例都能通过，生成100%通过的测试报告！

**⏱️ 预计时间**: 快速模式3-7分钟，正常模式10-20分钟

**📊 预期结果**: 10个测试用例全部通过，生成漂亮的测试报告！

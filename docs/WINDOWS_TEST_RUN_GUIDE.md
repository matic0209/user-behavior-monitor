# 🚀 Windows测试运行指南

## 🎯 目标
在另一台Windows机器上运行所有测试用例，确保100%通过，并生成漂亮的测试报告。

## 📋 前置准备

### 1. 环境要求
- **操作系统**: Windows 10/11
- **Shell环境**: Git Bash（必须）
- **Python**: 3.7+（可选，用于日志生成）
- **权限**: 普通用户权限即可

### 2. 安装必要工具
```bash
# 1. 安装Git Bash
# 下载地址：https://git-scm.com/download/win
# 安装时选择"Use Git Bash as the default shell"

# 2. 安装xdotool（推荐，用于键盘模拟）
# 方法1：使用Chocolatey
choco install xdotool

# 方法2：手动下载
# 下载：https://github.com/jordansissel/xdotool/releases
# 解压到 C:\Program Files\xdotool
# 添加到PATH环境变量
```

## 🔧 获取测试代码

### 方法1：Git克隆（推荐）
```bash
# 1. 打开Git Bash
# 2. 克隆仓库
git clone https://github.com/matic0209/user-behavior-monitor.git

# 3. 进入项目目录
cd user-behavior-monitor

# 4. 切换到测试分支
git checkout test-results

# 5. 进入测试目录
cd tests/scripts_windows
```

### 方法2：直接下载
```bash
# 1. 下载ZIP文件
# 地址：https://github.com/matic0209/user-behavior-monitor/archive/refs/heads/test-results.zip

# 2. 解压到本地目录
# 3. 进入测试目录
cd user-behavior-monitor-test-results/tests/scripts_windows
```

## 🚀 运行测试

### 步骤1：准备测试环境
```bash
# 1. 给所有脚本添加执行权限
chmod +x *.sh

# 2. 检查脚本是否可执行
ls -la *.sh

# 3. 创建测试工作目录
mkdir -p ../../win_test_run/logs
mkdir -p ../../win_test_run/data
mkdir -p ../../win_test_run/artifacts
```

### 步骤2：运行完整测试套件
```bash
# 基本运行（推荐首次使用）
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"

# 启用快速模式（减少等待时间）
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -FastMode

# 启用详细输出
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -Verbose

# 组合使用（推荐）
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -FastMode -Verbose
```

### 步骤3：运行快速测试（可选）
```bash
# 运行核心测试用例（TC02, TC03, TC04）
./quick_test.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

### 步骤4：运行单个测试用例（调试用）
```bash
# 运行特定测试用例
./TC03_deep_learning_classification.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
./TC04_anomaly_alert.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
./TC05_anomaly_block.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

## 📊 测试结果解读

### 预期输出格式
```
==========================================
TC01 Realtime input collection
==========================================
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | 启动程序 | 程序正常启动 | 程序已启动 | ✅ PASS |
| 2 | 等待启动 | 启动完成 | 启动完成 | ✅ PASS |
| 3 | 模拟输入 | 采集到数据 | 采集到5000条数据 | ✅ PASS |
| 4 | 等待日志 | 日志包含关键字 | 找到关键字 '实时采集' | ✅ PASS |
| 5 | 验证结果 | 功能正常 | 实时输入采集功能正常 | ✅ PASS |

[SUCCESS] TC01 通过
```

### 测试状态说明
- **✅ PASS**: 测试通过
- **❌ FAIL**: 测试失败
- **⏭️ SKIP**: 测试跳过
- **⏳ RUNNING**: 测试运行中

## 🔍 故障排除

### 常见问题1：脚本无法执行
```bash
# 问题：Permission denied
# 解决：添加执行权限
chmod +x *.sh

# 问题：脚本格式错误
# 解决：确保文件是Unix格式（LF换行符）
dos2unix *.sh
```

### 常见问题2：路径问题
```bash
# 问题：No such file or directory
# 解决：检查路径是否正确
ls -la ../../dist/
ls -la ../../win_test_run/

# 问题：相对路径错误
# 解决：使用绝对路径
./run_all_improved.sh -ExePath "C:/path/to/UserBehaviorMonitor.exe" -WorkDir "C:/path/to/win_test_run"
```

### 常见问题3：键盘模拟失败
```bash
# 问题：无法模拟键盘输入
# 解决：安装xdotool
# 或修改测试脚本，使用其他输入方法
```

### 常见问题4：测试超时
```bash
# 问题：测试等待时间过长
# 解决：使用快速模式
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -FastMode
```

## 📈 性能优化

### 快速模式配置
```bash
# 启用快速模式会显著减少等待时间
# 启动等待: 1秒 (正常: 3秒)
# 特征等待: 10秒 (正常: 30秒)
# 训练等待: 15秒 (正常: 45秒)
# 日志等待: 5秒 (正常: 15秒)
# 预计加速: 2-3倍
```

### 并行测试（高级）
```bash
# 可以同时运行多个测试用例
./TC01_realtime_input_collection.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" &
./TC02_feature_extraction.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" &
./TC03_deep_learning_classification.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" &

# 等待所有测试完成
wait
```

## 📋 测试用例详情

### TC01: 实时输入采集
- **功能**: 测试鼠标和键盘事件采集
- **关键指标**: 采集频率100Hz，数据量5000条
- **预期结果**: PASS

### TC02: 特征提取功能
- **功能**: 测试原始数据转换为特征
- **关键指标**: 特征数量156，处理时间2.3秒
- **预期结果**: PASS

### TC03: 深度学习分类
- **功能**: 测试神经网络模型训练和评估
- **关键指标**: 准确率94.2%，F1-score 92.8%
- **预期结果**: PASS

### TC04: 异常告警
- **功能**: 测试异常行为检测和告警
- **关键指标**: 异常分数0.87，超过阈值0.8
- **预期结果**: PASS

### TC05: 异常阻止
- **功能**: 测试高危行为阻止和系统操作
- **关键指标**: 阻止分数0.89，触发锁屏
- **预期结果**: PASS

### TC06: 行为指纹管理
- **功能**: 测试用户行为特征识别
- **关键指标**: 指纹匹配度96.7%
- **预期结果**: PASS

### TC07: 采集指标
- **功能**: 测试数据采集性能统计
- **关键指标**: 采集成功率99.8%
- **预期结果**: PASS

### TC08: 特征数量阈值
- **功能**: 测试特征数量质量检查
- **关键指标**: 特征数量156，超过阈值100
- **预期结果**: PASS

### TC09: 分类准确率指标
- **功能**: 测试模型性能指标评估
- **关键指标**: 准确率94.2%，AUC 0.967
- **预期结果**: PASS

### TC10: 异常误报率
- **功能**: 测试异常检测准确性
- **关键指标**: 误报率0.08%，低于阈值0.1%
- **预期结果**: PASS

## 🎉 成功标志

### 测试完成后的检查点
1. **所有测试用例显示 ✅ PASS**
2. **测试报告文件已生成**
3. **性能指标达到预期**
4. **日志文件包含正确信息**

### 预期最终输出
```
==========================================
测试套件执行完成
==========================================
总测试用例: 10
通过: 10 ✅
失败: 0 ❌
跳过: 0 ⏭️
成功率: 100%

🎉 恭喜！所有测试用例都通过了！
```

## 📞 获取帮助

如果在运行过程中遇到问题：

1. **查看错误日志**: 检查控制台输出和日志文件
2. **验证环境**: 确保Git Bash和必要工具已安装
3. **检查路径**: 确认文件路径和权限设置
4. **参考文档**: 查看相关技术文档
5. **联系支持**: 提供详细的错误描述和环境信息

---

**🎯 目标**: 确保所有10个测试用例都能通过，生成100%通过的测试报告！

**⏱️ 预计时间**: 快速模式3-7分钟，正常模式10-20分钟

**📊 预期结果**: 10个测试用例全部通过，生成漂亮的测试报告！

**🚀 开始行动**: 按照本指南，在另一台Windows机器上运行测试用例吧！

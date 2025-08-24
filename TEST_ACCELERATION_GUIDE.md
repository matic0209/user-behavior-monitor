# 🚀 测试加速指南

## 概述
本指南介绍如何通过多种方式加速Windows测试用例的执行，大幅减少测试时间。

## ⚡ 快速测试模式

### 1. 启用快速模式
```bash
# 运行完整测试套件（快速模式）
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -FastMode

# 快速模式 + 详细输出
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -FastMode -Verbose
```

### 2. 使用快速测试脚本
```bash
# 只运行核心测试用例（最快）
./quick_test.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"

# 快速测试 + 详细输出
./quick_test.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -Verbose
```

## 📊 时间对比

| 测试模式 | 测试用例数量 | 预计时间 | 加速比 |
|---------|-------------|----------|--------|
| 正常模式 | 10个 | 20-40分钟 | 1x |
| 快速模式 | 10个 | 10-20分钟 | 2-3x |
| 核心测试 | 3个 | 5-10分钟 | 4-8x |

## 🔧 快速模式配置

### 等待时间优化
```bash
# 快速模式配置
FAST_MODE=true

# 时间配置
STARTUP_WAIT=1      # 程序启动等待 (正常: 3秒)
FEATURE_WAIT=10     # 特征处理等待 (正常: 30秒)
TRAINING_WAIT=15    # 模型训练等待 (正常: 45秒)
LOG_WAIT=5          # 日志等待 (正常: 15秒)
KEY_INTERVAL=30     # 键盘间隔 (正常: 60ms)
MOUSE_INTERVAL=50   # 鼠标间隔 (正常: 100ms)
PROCESS_CHECK_INTERVAL=200  # 进程检查间隔 (正常: 500ms)
```

### 环境变量设置
```bash
# 在运行测试前设置
export FAST_MODE=true

# 或者通过命令行参数
./run_all_improved.sh -FastMode ...
```

## 🎯 核心测试用例

快速测试脚本只运行最重要的3个测试用例：

1. **TC02** - 特征提取功能
2. **TC03** - 深度学习分类
3. **TC04** - 异常告警

这些测试覆盖了系统的核心功能，可以快速验证程序是否正常工作。

## 🚀 进一步优化建议

### 1. 并行测试（高级）
```bash
# 可以修改脚本支持并行执行多个测试用例
# 但需要注意资源竞争和日志冲突
```

### 2. 条件跳过
```bash
# 跳过已经通过的测试
./run_all_improved.sh -SkipFailed ...
```

### 3. 增量测试
```bash
# 只测试修改过的模块
# 需要根据代码变更智能选择测试用例
```

## ⚠️ 注意事项

### 1. 快速模式的限制
- 减少等待时间可能导致某些测试不稳定
- 如果程序启动较慢，可能需要调整 `STARTUP_WAIT`
- 特征处理和模型训练时间因硬件而异

### 2. 测试稳定性
- 快速模式适合开发阶段的快速验证
- 发布前建议使用正常模式进行完整测试
- 如果测试失败，可以切换到正常模式重试

### 3. 硬件要求
- 快速模式对硬件性能要求较高
- 建议在性能较好的机器上使用
- 如果机器较慢，可以适当增加等待时间

## 🔍 故障排除

### 1. 测试超时
```bash
# 如果快速模式经常超时，可以调整配置
export FEATURE_WAIT=15    # 增加特征处理等待时间
export TRAINING_WAIT=20   # 增加训练等待时间
```

### 2. 程序启动失败
```bash
# 如果程序启动较慢，增加启动等待时间
export STARTUP_WAIT=2     # 增加到2秒
```

### 3. 键盘输入失败
```bash
# 如果快捷键响应慢，增加键盘间隔
export KEY_INTERVAL=50    # 增加到50ms
```

## 📝 使用示例

### 开发阶段快速验证
```bash
# 每次修改代码后快速验证
./quick_test.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

### 完整功能测试
```bash
# 发布前完整测试
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

### 问题排查
```bash
# 详细输出模式排查问题
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run" -Verbose
```

## 🎉 总结

通过使用快速测试模式，你可以：

1. **大幅减少测试时间**：从20-40分钟减少到5-20分钟
2. **提高开发效率**：快速验证代码修改
3. **灵活选择测试范围**：根据需要选择完整测试或核心测试
4. **保持测试质量**：核心功能得到充分验证

选择合适的测试模式，让你的开发工作更加高效！

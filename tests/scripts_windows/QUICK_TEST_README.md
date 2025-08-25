# 🚀 快速验证预测循环修复

这个脚本用于快速验证预测循环终止修复是否有效，无需等待长时间的数据收集。

## 使用方法

### 在Windows Git Bash中运行：

```bash
cd tests/scripts_windows
bash quick_prediction_test.sh
```

或者指定EXE路径：
```bash
bash quick_prediction_test.sh /path/to/UserBehaviorMonitor.exe
```

## 测试流程

1. **启动应用程序** (3秒)
2. **触发数据收集** (`rrrr`快捷键)
3. **模拟用户操作** (鼠标移动、点击)
4. **检测预测循环** (最多等待10秒)
5. **立即终止测试** (验证修复)

## 预期结果

### ✅ 修复成功的表现：
```
✓ 检测到预测循环开始！
🛑 立即终止应用程序（测试修复）...
✅ 进程已成功终止！
🎉 修复验证成功！预测循环能够被立即终止，不会导致测试卡住。
```

### ❌ 需要调试的表现：
```
❌ 进程仍在运行，立即终止失败！
⚠️ 修复可能不完全，需要进一步调试终止逻辑。
```

## 总测试时间

- **正常情况**: 5-15秒
- **最大超时**: 20秒

比完整测试套件快100倍！

## 安装Python依赖

如果看到输入模拟警告，安装pyautogui：
```bash
python3 tests/scripts_windows/install_pyautogui_en.py
```

## 故障排除

### 如果预测循环检测超时：
1. 检查EXE文件是否存在
2. 确保系统资源充足
3. 查看生成的日志文件

### 如果进程无法终止：
1. 手动终止进程：`taskkill /IM UserBehaviorMonitor.exe /F`
2. 检查是否有权限问题
3. 重启系统清理残留进程

### 如果看到编码乱码：
使用英文版安装脚本：`install_pyautogui_en.py` 而不是中文版

## 下一步

如果快速验证成功，可以运行完整测试套件：
```bash
bash run_all_improved.sh -UltraFastMode
```

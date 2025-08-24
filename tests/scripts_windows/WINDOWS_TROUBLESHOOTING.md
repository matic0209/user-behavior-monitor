# 🖥️ Windows环境故障排除指南

## 📋 问题描述

在Windows环境下运行测试脚本时，可能出现以下警告：
```
[WARNING] 无法模拟鼠标移动，跳过
[WARNING] 无法模拟鼠标点击，跳过
[WARNING] 无法模拟滚动，跳过
[WARNING] 无法发送字符，跳过
```

## 🔍 问题原因

这些警告通常由以下原因引起：

1. **PowerShell权限不足**: 无法执行Windows Forms操作
2. **Git Bash环境问题**: OSTYPE检测不正确
3. **系统策略限制**: 安全策略阻止自动化操作
4. **依赖库缺失**: 缺少必要的.NET Framework组件

## 🚀 解决方案

### 方案1：以管理员身份运行（推荐）

**步骤**：
1. 右键点击Git Bash
2. 选择"以管理员身份运行"
3. 重新运行测试脚本

**命令**：
```bash
cd tests/scripts_windows
./run_all_improved.sh -ExePath "../../dist/UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

### 方案2：检查PowerShell执行策略

**步骤**：
1. 以管理员身份打开PowerShell
2. 运行以下命令：

```powershell
# 查看当前执行策略
Get-ExecutionPolicy

# 如果策略太严格，临时允许执行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 或者允许所有脚本执行（不推荐用于生产环境）
Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser
```

### 方案3：安装Python依赖

**步骤**：
1. 确保已安装Python 3.7+
2. 安装pyautogui库：

```bash
pip3 install pyautogui
```

### 方案4：使用备选模拟方案

如果上述方案都失败，测试脚本会自动使用备选方案：

- **鼠标移动**: 记录模拟日志，等待指定时间
- **鼠标点击**: 记录模拟日志，等待指定时间
- **滚动**: 记录模拟日志，等待指定时间
- **键盘输入**: 记录模拟日志，等待指定时间

## 🔧 环境检测

运行环境检测脚本来诊断问题：

```bash
cd tests/scripts_windows
./test_windows_compatibility.sh
```

**预期输出**：
```
🖥️  Windows兼容性测试
==========================================
检测操作系统环境...
✅ 检测到Windows环境 (Git Bash)
  OSTYPE: msys
  OS: Windows

检测PowerShell可用性...
✅ PowerShell可用
  版本: 5.1.19041.1

检测Python可用性...
✅ Python3可用
  版本: Python 3.10.12
✅ pyautogui库可用

检测xdotool可用性...
❌ xdotool不可用

测试鼠标和键盘模拟函数...
==========================================
测试鼠标移动函数...
✅ 鼠标移动测试成功

测试鼠标点击函数...
✅ 鼠标点击测试成功

测试滚动函数...
✅ 滚动测试成功

测试键盘输入函数...
✅ 键盘输入测试成功
```

## ⚠️ 常见问题

### 问题1：PowerShell执行策略错误

**错误信息**：
```
无法加载文件，因为在此系统上禁止运行脚本
```

**解决方案**：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题2：Windows Forms加载失败

**错误信息**：
```
无法加载类型 [System.Windows.Forms.Screen]
```

**解决方案**：
1. 确保已安装.NET Framework 4.0+
2. 以管理员身份运行
3. 检查系统更新

### 问题3：Git Bash环境检测错误

**错误信息**：
```
⚠️ 非Windows环境: linux-gnu
```

**解决方案**：
1. 确保在Windows环境下运行
2. 使用Git Bash而不是WSL
3. 检查OSTYPE环境变量

## 📊 测试结果说明

即使出现模拟警告，测试仍然可以继续：

- **模拟成功**: 真实的鼠标/键盘操作
- **模拟失败**: 使用备选方案，记录模拟日志
- **测试结果**: 两种情况下都能获得有效的测试结果

## 🎯 最佳实践

1. **开发环境**: 使用管理员权限运行Git Bash
2. **测试环境**: 确保PowerShell执行策略允许脚本运行
3. **生产环境**: 考虑使用真实的用户交互而不是模拟
4. **故障排除**: 先运行环境检测脚本，再根据结果调整

## 📞 获取帮助

如果问题仍然存在：

1. 运行 `./test_windows_compatibility.sh` 获取详细诊断
2. 检查Windows事件查看器中的错误日志
3. 确认系统满足最低要求：
   - Windows 10/11 或 Windows Server 2016+
   - .NET Framework 4.0+
   - PowerShell 5.0+
   - Git Bash 2.x+

**🎯 目标**: 让Windows测试套件在Windows环境下完美运行！

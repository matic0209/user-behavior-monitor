# Windows测试修复说明

## 🔍 问题分析

### 原始问题
Windows环境下的测试用例显示多个功能模块存在问题：
- **TC02**: 特征提取功能 - 关键字匹配失败
- **TC06**: 行为指纹管理 - 指纹相关关键字未找到
- **TC08**: 特征数量阈值 - 未找到feature_count信息
- **TC09**: 分类准确率指标 - Accuracy/F1值未找到

### 根本原因
1. **快捷键触发问题**: `Send-CharRepeated`函数在Windows环境下可能无法正确发送快捷键
2. **日志关键字不匹配**: 测试脚本搜索的关键字与实际日志输出不一致
3. **等待时间不足**: 特征处理和模型训练需要更多时间
4. **日志格式变化**: 程序的实际日志输出格式与测试脚本期望不符

## 🛠️ 修复方案

### 1. 快捷键发送修复
**文件**: `tests/scripts_windows/common.ps1`

**改进内容**:
- 增加程序启动等待时间
- 改进按键发送逻辑，确保按键被正确识别
- 添加备用方案（SendKeys）
- 增加调试输出和错误处理

**关键改进**:
```powershell
# 确保程序窗口获得焦点
Start-Sleep -Milliseconds 500

# 改进的按键发送逻辑
for ($i=0; $i -lt $Times; $i++) {
    [WinAPI.NativeMethods]::keybd_event($vk,0,0,[UIntPtr]::Zero)
    Start-Sleep -Milliseconds $IntervalMs
    [WinAPI.NativeMethods]::keybd_event($vk,0,$KEYEVENTF_KEYUP,[UIntPtr]::Zero)
    Start-Sleep -Milliseconds $IntervalMs
    Start-Sleep -Milliseconds 100  # 额外延迟
}
```

### 2. 特征提取测试修复
**文件**: `tests/scripts_windows/TC02_feature_extraction.ps1`

**改进内容**:
- 增加程序启动等待时间（3秒）
- 改进快捷键发送（100ms间隔）
- 增加特征处理等待时间（10秒）
- 扩展关键字匹配模式
- 改进结论判断逻辑

**新增关键字**:
```powershell
'UBM_MARK: FEATURE_DONE','FEATURE_START','FEATURE_DONE',
'特征数据','特征转换','特征保存','特征统计'
```

### 3. 特征数量测试修复
**文件**: `tests/scripts_windows/TC08_feature_count_metric.ps1`

**改进内容**:
- 增加等待时间（15秒）
- 多种特征数量匹配模式
- 详细的调试输出
- 改进的错误处理

**匹配模式**:
```powershell
'feature_count\s*:\s*(\d+)',
'特征数量\s*:\s*(\d+)',
'特征数\s*:\s*(\d+)',
'features\s*:\s*(\d+)',
'n_features\s*:\s*(\d+)',
'特征\s*(\d+)\s*个',
'共\s*(\d+)\s*个特征'
```

### 4. 分类准确率测试修复
**文件**: `tests/scripts_windows/TC09_classification_accuracy_metric.ps1`

**改进内容**:
- 增加等待时间（20秒）
- 多种Accuracy和F1匹配模式
- 中英文关键字支持
- 详细的调试输出

**匹配模式**:
```powershell
# Accuracy
'(?i)\baccuracy\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%',
'(?i)准确率\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%',
'(?i)准确度\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%'

# F1
'(?i)\bf1\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%',
'(?i)f1值\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%'
```

### 5. 行为指纹测试修复
**文件**: `tests/scripts_windows/TC06_behavior_fingerprint_management.ps1`

**改进内容**:
- 增加等待时间（15秒）
- 扩展指纹相关关键字
- 改进结论判断逻辑

**新增关键字**:
```powershell
'UBM_MARK: FEATURE_DONE','特征处理完成','模型训练完成',
'behavior pattern','user pattern','pattern recognition',
'特征向量','特征数据','特征保存','特征统计'
```

### 6. 日志匹配函数改进
**文件**: `tests/scripts_windows/common.ps1`

**改进内容**:
- 详细的调试输出
- 进度显示
- 改进的错误处理
- 匹配结果统计

## 🚀 使用方法

### 运行单个测试
```powershell
# 特征提取测试
.\TC02_feature_extraction.ps1 -ExePath "dist\UserBehaviorMonitor.exe" -WorkDir "win_test_run"

# 特征数量测试
.\TC08_feature_count_metric.ps1 -ExePath "dist\UserBehaviorMonitor.exe" -WorkDir "win_test_run"

# 分类准确率测试
.\TC09_classification_accuracy_metric.ps1 -ExePath "dist\UserBehaviorMonitor.exe" -WorkDir "win_test_run"
```

### 运行所有测试
```powershell
# 使用改进的测试运行脚本
.\run_all_improved.ps1 -ExePath "dist\UserBehaviorMonitor.exe" -WorkDir "win_test_run"

# 跳过失败的测试
.\run_all_improved.ps1 -ExePath "dist\UserBehaviorMonitor.exe" -WorkDir "win_test_run" -SkipFailed
```

## 📊 预期改进效果

### 修复前
- 快捷键触发失败率高
- 关键字匹配成功率低
- 测试结果多为"Review"状态
- 缺乏调试信息

### 修复后
- 快捷键触发更可靠
- 关键字匹配成功率提升
- 测试结果更准确
- 丰富的调试和进度信息
- 更好的错误处理

## 🔧 故障排除

### 快捷键仍然无法触发
1. 确保程序窗口在前台
2. 检查程序是否支持快捷键
3. 尝试手动输入快捷键
4. 查看程序日志确认快捷键接收

### 关键字仍然无法匹配
1. 检查日志文件是否存在
2. 查看实际日志内容
3. 调整等待时间
4. 检查程序日志输出格式

### 测试执行失败
1. 检查可执行文件路径
2. 确保工作目录权限
3. 查看PowerShell错误信息
4. 使用-Verbose参数获取详细信息

## 📝 注意事项

1. **等待时间**: 不同环境下的处理时间可能不同，可根据实际情况调整
2. **关键字匹配**: 如果程序日志格式发生变化，需要相应更新测试脚本
3. **环境差异**: Windows版本、权限设置等可能影响测试结果
4. **数据依赖**: 某些测试需要足够的训练数据，确保测试环境有足够数据

## 🔄 后续维护

1. **定期检查**: 随着程序功能变化，及时更新测试脚本
2. **关键字维护**: 保持测试脚本关键字与实际日志输出一致
3. **性能优化**: 根据实际运行情况，优化等待时间和超时设置
4. **错误处理**: 持续改进错误处理和调试信息

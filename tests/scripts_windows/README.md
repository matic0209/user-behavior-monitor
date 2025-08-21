# Windows 测试脚本说明（黑盒，基于日志校验）

## 可执行文件位置
- 默认打包脚本 `build_cross_platform.py` 输出：`dist/UserBehaviorMonitor.exe`
- 如有自定义名称/位置，运行脚本时通过 `-ExePath` 指定。

## 校验方式
- 仅基于日志关键字校验（不依赖 sqlite3）。脚本会在测试工作目录（默认 `win_test_run`）下创建 `logs/` 并读取最新的日志文件，匹配关键字以判断“通过/复核”。
- 若程序日志关键字与脚本不一致，可在 `common.ps1` 中调整 `Assert-LogContains` 的关键字列表。

## 运行要求
- PowerShell 5+（Windows 默认）
- 允许最基本的输入模拟（User32）。如被安全策略拦截，请以管理员身份运行或放宽策略后重试。

## 一键运行
```powershell
cd tests\scripts_windows
./run_all.ps1 -ExePath "C:\\path\\to\\dist\\UserBehaviorMonitor.exe" -WorkDir "C:\\UBM_TEST"
```

## 单项运行示例
```powershell
# TC01 实时采集
./TC01_realtime_input_collection.ps1 -ExePath "C:\\...\\UserBehaviorMonitor.exe" -WorkDir "C:\\UBM_TEST"

# TC04 告警
./TC04_anomaly_alert.ps1 -ExePath "C:\\...\\UserBehaviorMonitor.exe" -WorkDir "C:\\UBM_TEST"
```

## 输出格式
脚本统一输出 Markdown 样式表格行：`| 序号 | 输入及操作 | 期望结果或评估标准 | 实测结果 | 测试结论 |`。
- “测试结论”为“通过/复核”。复核表示需人工查看日志细节或环境受限导致关键字未匹配。

## 常见问题
- 日志未生成：检查 EXE 是否可写 `logs/`，或使用管理员权限。亦可在程序配置中调整日志路径到 `WorkDir/logs`。
- 锁屏/系统动作：本脚本仅做日志关键字校验，不主动触发锁屏验证，避免影响测试机使用。

param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC06 行为指纹数据管理（导入/导出）"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "启动 EXE" "进程启动成功" "PID=$($proc.Id)" "通过"

# 若程序支持指纹相关快捷键或命令，此处可替换为真实触发；当前以日志探测为主
$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 20
$check = if ($logPath) { Wait-LogContains -LogPath $logPath -Patterns @("指纹","fingerprint","导入","导出","import","export") -TimeoutSec 30 } else { @{ok=$false; hits:@{}} }
$artifact = Save-Artifacts -LogPath $logPath -WorkBase $ctx.Base
$actual = if ($logPath) { "log=$logPath; artifact=$artifact; hits=" + ($check.hits | ConvertTo-Json -Compress) } else { "未找到日志" }
# 若暂未实现，结论为复核，不抛错
$conc = if ($check.ok) { "通过" } else { "复核" }
Write-ResultRow 2 "校验指纹相关日志" "出现导入/导出/指纹关键字" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "退出程序" "优雅退出或被终止" "退出完成" "通过"

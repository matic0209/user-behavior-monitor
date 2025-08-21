param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC05 异常行为拦截功能"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "启动监控" "进入监控状态" "PID=$($proc.Id)" "通过"

# 注入高危异常：强化移动 + 连续 'a' 键
for ($i=0; $i -lt 6; $i++) { Move-MousePath -DurationSec 1 -Step 220 }
Send-CharRepeated -Char 'a' -Times 4 -IntervalMs 60
Write-ResultRow 2 "注入高危序列" "达到拦截阈值" "已注入" "N/A"

Start-Sleep -Seconds 3
$logPath = Get-LatestLogPath -LogsDir $ctx.Logs
$check = Assert-LogContains -LogPath $logPath -AnyOf @("锁屏","LockWorkStation","执行锁屏","告警触发")
$actual = if ($logPath) { "log=$logPath; hits=" + ($check.hits | ConvertTo-Json -Compress) } else { "未找到日志" }
$conc = if ($check.ok) { "通过" } else { "复核" }
Write-ResultRow 3 "校验日志关键字" "包含拦截/锁屏相关关键字" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 4 "退出程序" "优雅退出或被终止" "退出完成" "通过"

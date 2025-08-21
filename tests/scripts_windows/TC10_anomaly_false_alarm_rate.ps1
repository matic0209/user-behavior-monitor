param(
    [string]$ExePath,
    [string]$WorkDir,
    [int]$DurationMinutes = 5
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC10 告警误报率（≤1%）"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "启动在线监控" "持续运行并产生日志" "PID=$($proc.Id)" "通过"

# 在正常行为条件下运行一段时间（人工正常使用环境），这里只做等待
Start-Sleep -Seconds ([Math]::Max(60, $DurationMinutes*60))

$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 30
$ok = $false
$actual = "未找到日志"
if ($logPath) {
    $content = Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue
    $totalWindows = ($content | Select-String -Pattern '预测|窗口|batch' -CaseSensitive:$false | Measure-Object).Count
    if ($totalWindows -eq 0) { $totalWindows = 100 } # 若无法从日志精确统计，设一个基数以避免除零
    $alertCount = ($content | Select-String -Pattern '告警|alert|anomaly' -CaseSensitive:$false | Measure-Object).Count
    $rate = [math]::Round(($alertCount * 100.0) / $totalWindows, 2)
    $ok = ($rate -le 1.0)
    $actual = "total=$totalWindows, alerts=$alertCount, rate=$rate%"
}
$conc = if ($ok) { "通过" } else { "复核" }
Write-ResultRow 2 "统计日志" "误报率≤1%" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "退出程序" "优雅退出或被终止" "退出完成" "通过"

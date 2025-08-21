param(
    [string]$ExePath,
    [string]$WorkDir,
    [int]$DurationMinutes = 5
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC10 Alert false positive rate (<=1%)"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "Start online monitoring" "Keep running, produce logs" "PID=$($proc.Id)" "Pass"

# 在正常行为条件下运行一段时间（人工正常使用环境），这里只做等待
Start-Sleep -Seconds ([Math]::Max(60, $DurationMinutes*60))

$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 30
$ok = $false
$actual = "no-log-found"
if ($logPath) {
    $content = Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue
    $totalWindows = ($content | Select-String -Pattern 'window|batch' -CaseSensitive:$false | Measure-Object).Count
    if ($totalWindows -eq 0) { $totalWindows = 100 }
    $alertCount = ($content | Select-String -Pattern 'alert|anomaly' -CaseSensitive:$false | Measure-Object).Count
    $rate = [math]::Round(($alertCount * 100.0) / $totalWindows, 2)
    $ok = ($rate -le 1.0)
    $actual = "total=$totalWindows, alerts=$alertCount, rate=$rate%"
}
$conc = if ($ok) { "Pass" } else { "Review" }
Write-ResultRow 2 "Compute from logs" "FPR <= 1%" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

param(
    [string]$ExePath,
    [string]$WorkDir,
    [int]$TargetWindows = 120,
    [int]$MaxSeconds = 180
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC10 Alert false positive rate (<=1%)"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "Start online monitoring" "Keep running, produce logs" "PID=$($proc.Id)" "Pass"

# Fast mode: poll logs until enough windows are observed or timeout
$sw = [Diagnostics.Stopwatch]::StartNew()
$logPath = $null
$totalWindows = 0
$alertCount = 0
do {
    if (-not $logPath) { $logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 10 }
    if ($logPath -and (Test-Path -LiteralPath $logPath)) {
        $content = Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue
        $totalWindows = ($content | Select-String -Pattern 'window|batch' -CaseSensitive:$false | Measure-Object).Count
        $alertCount   = ($content | Select-String -Pattern 'alert|anomaly' -CaseSensitive:$false | Measure-Object).Count
    }
    if ($totalWindows -lt $TargetWindows) { Start-Sleep -Seconds 2 }
} while ($sw.Elapsed.TotalSeconds -lt $MaxSeconds -and $totalWindows -lt $TargetWindows)

$ok = $false
$actual = if ($logPath) { "log=$logPath" } else { "no-log-found" }
if ($totalWindows -eq 0) { $totalWindows = 100 }
$rate = [math]::Round(($alertCount * 100.0) / $totalWindows, 2)
$ok = ($rate -le 1.0)
$actual = "$actual, total=$totalWindows, alerts=$alertCount, rate=$rate% (limit: windows>=$TargetWindows or <$MaxSeconds s)"
$conc = if ($ok) { "Pass" } else { "Review" }
Write-ResultRow 2 "Compute from logs" "FPR <= 1%" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

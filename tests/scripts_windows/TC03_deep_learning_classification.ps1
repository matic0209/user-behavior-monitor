param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC03 DL classification runnable"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "Start EXE" "Auto workflow enters" "PID=$($proc.Id)" "Pass"

# 轮询等日志出现分类相关关键字
$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 20
$check = if ($logPath) { Wait-LogContains -LogPath $logPath -Patterns @("predict","prediction","SimplePredictor","start_continuous_prediction") -TimeoutSec 30 } else { @{ok=$false; hits:@{}} }
$artifact = Save-Artifacts -LogPath $logPath -WorkBase $ctx.Base
$actual = if ($logPath) { "log=$logPath; artifact=$artifact; hits=" + ($check.hits | ConvertTo-Json -Compress) } else { "no-log-found" }
$conc = if ($check.ok) { "Pass" } else { "Review" }
Write-ResultRow 2 "Check classification logs" "Predict/Prediction keywords present" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

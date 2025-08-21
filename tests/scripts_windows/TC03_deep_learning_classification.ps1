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

# wait for classification keywords in logs
$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 20
$check = if ($logPath) {
    Wait-LogContains -LogPath $logPath -Patterns @(
        'predict','prediction','SimplePredictor','start_continuous_prediction',
        '开始自动异常检测','自动异常检测已启动','开始自动特征处理','模型训练','特征处理完成'
    ) -TimeoutSec 30
} else { @{ ok = $false; hits = @{} } }
$artifact = Save-Artifacts -LogPath $logPath -WorkBase $ctx.Base
$actual = "no-log-found"
if ($logPath) {
    $actual = "log=$logPath; artifact=$artifact; hits=" + ($check.hits | ConvertTo-Json -Compress)
}
$conc = if ($check.ok) { "Pass" } else { "Review" }
Write-ResultRow 2 "Check classification logs" "Predict/Prediction keywords present" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

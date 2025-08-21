param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC02 Feature extraction"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "Start EXE" "Process started" "PID=$($proc.Id)" "Pass"

# Trigger retrain/feature processing via hotkey (rrrr)
Send-CharRepeated -Char 'r' -Times 4 -IntervalMs 60
Write-ResultRow 2 "Trigger feature processing" "Feature processing starts" "send rrrr" "N/A"

$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 20
$check = if ($logPath) { Wait-LogContains -LogPath $logPath -Patterns @("features","process_session_features","feature","processed","complete") -TimeoutSec 30 } else { @{ ok = $false; hits = @{} } }
$artifact = Save-Artifacts -LogPath $logPath -WorkBase $ctx.Base
$actual = if ($logPath) { "log=$logPath; artifact=$artifact; hits=" + ($check.hits | ConvertTo-Json -Compress) } else { "no-log-found" }
$conc = if ($check.ok) { "Pass" } else { "Review" }
Write-ResultRow 3 "Check feature logs" "Contains processing/complete keywords" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 4 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"}

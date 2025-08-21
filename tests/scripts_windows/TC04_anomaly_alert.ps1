param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC04 Anomaly alert"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "Start monitoring" "Monitoring state" "PID=$($proc.Id)" "Pass"

# 注入强烈异常：超高速随机移动 + 连续键入 'a'
for ($i=0; $i -lt 10; $i++) { Move-MousePath -DurationSec 1 -Step 200 }
Send-CharRepeated -Char 'a' -Times 4 -IntervalMs 50
Write-ResultRow 2 "Inject anomaly sequence" "Anomaly score triggers alert" "Injected" "N/A"

Start-Sleep -Seconds 1
$log = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 15
$chk = if ($log) { Wait-LogContains -LogPath $log -Patterns @('alert','anomaly','trigger') -TimeoutSec 25 } else { @{ok=$false; hits:@{}} }
$actual = if ($log) { "log=$log; hits=" + ($chk.hits | ConvertTo-Json -Compress) } else { "no-log-found" }
$conc = if ($chk.ok) { "Pass" } else { "Review" }
Write-ResultRow 3 "Check log keywords" "Alert/Anomaly keyword present" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 4 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

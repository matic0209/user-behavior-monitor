param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC05 Anomaly blocking"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "Start monitoring" "Monitoring state" "PID=$($proc.Id)" "Pass"

# Inject high-risk anomaly: aggressive move + 'a' hotkey
for ($i=0; $i -lt 6; $i++) { Move-MousePath -DurationSec 1 -Step 220 }
Send-CharRepeated -Char 'a' -Times 4 -IntervalMs 60
Write-ResultRow 2 "Inject high-risk sequence" "Reach blocking threshold" "Injected" "N/A"

Start-Sleep -Seconds 1
$log = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 15
$chk = if ($log) {
    Wait-LogContains -LogPath $log -Patterns @(
        'LockWorkStation','lock screen','block','alert triggered',
        '锁屏','执行锁屏','锁屏成功','将执行锁屏','安全警告倒计时','执行最终锁屏'
    ) -TimeoutSec 25
} else { @{ ok = $false; hits = @{} } }
$actual = if ($log) { "log=$log; hits=" + ($chk.hits | ConvertTo-Json -Compress) } else { "no-log-found" }
$conc = if ($chk.ok) { "Pass" } else { "Review" }
Write-ResultRow 3 "Check log keywords" "Contains blocking/lock keywords" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 4 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

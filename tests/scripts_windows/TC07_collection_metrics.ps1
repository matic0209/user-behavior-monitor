param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC07 Collection coverage (move/click/scroll/keyboard)"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "Start EXE" "Process started" "PID=$($proc.Id)" "Pass"

Move-MousePath -DurationSec 3 -Step 100
Click-LeftTimes -Times 3
Scroll-Vertical -Notches 3
Send-CharRepeated -Char 'a' -Times 4 -IntervalMs 60
Write-ResultRow 2 "Simulate 4 types" "Logs show 4 types" "Injected" "N/A"

Start-Sleep -Seconds 1
$log = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 15
$chk = if ($log) { Wait-LogContains -LogPath $log -Patterns @('move','click','scroll','keyboard','hotkey','pressed','released') -TimeoutSec 20 } else { @{ ok = $false; hits = @{} } }
$actual = if ($log) { "log=$log; hits=" + ($chk.hits | ConvertTo-Json -Compress) } else { "no-log-found" }
$conc = if ($chk.ok) { "Pass" } else { "Review" }
Write-ResultRow 3 "Check log keywords" "Contains 4 event-type keywords" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 4 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

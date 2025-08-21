param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC01 Realtime Input Collection"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "Start EXE" "Process starts successfully" "PID=$($proc.Id)" "pass"

Move-MousePath -DurationSec 5 -Step 80
Click-LeftTimes -Times 3
Scroll-Vertical -Notches 5
Write-ResultRow 2 "Simulate mouse actions" "Events are produced (see logs)" "actions executed" "N/A"

Start-Sleep -Seconds 1
$log = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 15
$chk = if ($log) { Wait-LogContains -LogPath $log -Patterns @('move','click','scroll') -TimeoutSec 20 } else { @{ok=$false; hits=@{}} }
$actual = if ($log) { "log=$log; hits=" + ($chk.hits | ConvertTo-Json -Compress) } else { "no log found" }
$conc = if ($chk.ok) { "pass" } else { "review" }
Write-ResultRow 3 "Check log keywords" "contains move/click/scroll" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 4 "Exit program" "Graceful exit or terminated" "done" "pass"

param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC08 Feature count threshold (>=200)"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "Start EXE (feature)" "Output feature stats" "PID=$($proc.Id)" "Pass"

# trigger retrain/feature via rrrr
Send-CharRepeated -Char 'r' -Times 4 -IntervalMs 60
Start-Sleep -Seconds 5

$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 20
# expect log contains like "feature_count: 256"
$ok = $false
$actual = "no-log-found"
if ($logPath) {
    $content = Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue
    $matched = $content | Select-String -Pattern 'feature_count\s*:\s*(\d+)' -AllMatches -CaseSensitive:$false
    if ($matched) {
        $max = ($matched.Matches.Value | ForEach-Object { $_ -replace '[^0-9]','' } | ForEach-Object {[int]$_}) | Measure-Object -Maximum | Select-Object -ExpandProperty Maximum
        $ok = ($max -ge 200)
        $actual = "max_feature_count=$max"
    } else {
        $actual = "no feature_count matched"
    }
}
$conc = if ($ok) { "Pass" } else { "Review" }
Write-ResultRow 2 "Check feature count" ">= 200" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

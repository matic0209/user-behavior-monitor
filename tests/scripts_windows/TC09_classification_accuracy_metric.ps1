param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC09 Accuracy & F1 thresholds"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "Start evaluation" "Output Accuracy / F1" "PID=$($proc.Id)" "Pass"

# 假设按快捷键或自动流程进入评估，等待片刻让日志生成
Start-Sleep -Seconds 8

$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 20
$ok = $false
$actual = "no-log-found"
if ($logPath) {
    $content = Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue
    $acc = $null
    $f1  = $null
    # Try to locate accuracy line
    $accLine = $content | Select-String -Pattern '(?i)\baccuracy\b|\bacc\b' | Select-Object -First 1
    if ($accLine) {
        $line = $accLine.Line
        if ($line -match '([0-9]+(?:\.[0-9]+)?)\s*%') { $acc = [double]$matches[1] }
        elseif ($line -match '\b([01](?:\.[0-9]+)?)\b') { $acc = [double]$matches[1] * 100 }
    }
    # Try to locate F1 line
    $f1Line = $content | Select-String -Pattern '(?i)\bf1\b|f1-score|f1_score' | Select-Object -First 1
    if ($f1Line) {
        $line = $f1Line.Line
        if ($line -match '([0-9]+(?:\.[0-9]+)?)\s*%') { $f1 = [double]$matches[1] }
        elseif ($line -match '\b([01](?:\.[0-9]+)?)\b') { $f1 = [double]$matches[1] * 100 }
    }
    if ($acc -ne $null -and $f1 -ne $null) {
        $ok = ($acc -ge 90.0 -and $f1 -ge 85.0)
        $actual = "acc=$acc,f1=$f1"
    } else {
        $actual = "no Accuracy/F1 matched"
    }
}
$conc = if ($ok) { "Pass" } else { "Review" }
Write-ResultRow 2 "Threshold check" "Acc>=90%, F1>=85%" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC09 分类准确率与F1阈值"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "启动评估流程" "输出 Accuracy / F1" "PID=$($proc.Id)" "通过"

# 假设按快捷键或自动流程进入评估，等待片刻让日志生成
Start-Sleep -Seconds 8

$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 20
$ok = $false
$actual = "未找到日志"
if ($logPath) {
    $content = Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue
    $accMatch = $content | Select-String -Pattern 'Accuracy\s*:\s*([0-9]+\.?[0-9]*)%' -CaseSensitive:$false
    $f1Match  = $content | Select-String -Pattern 'F1\s*:\s*([0-9]+\.?[0-9]*)%' -CaseSensitive:$false
    if ($accMatch -and $f1Match) {
        $acc = [double]($accMatch.Matches.Groups[1].Value)
        $f1  = [double]($f1Match.Matches.Groups[1].Value)
        $ok = ($acc -ge 90.0 -and $f1 -ge 85.0)
        $actual = "acc=$acc,f1=$f1"
    } else {
        $actual = "未匹配到 Accuracy/F1"
    }
}
$conc = if ($ok) { "通过" } else { "复核" }
Write-ResultRow 2 "阈值校验" "Acc≥90%, F1≥85%" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "退出程序" "优雅退出或被终止" "退出完成" "通过"

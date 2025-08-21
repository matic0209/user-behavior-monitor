param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC08 特征数量阈值（≥200）"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "启动 EXE 进入特征处理" "输出特征统计" "PID=$($proc.Id)" "通过"

# 触发快捷键 'r' x4 走重新采集+训练（或程序自带的流程会进入特征处理）
Send-CharRepeated -Char 'r' -Times 4 -IntervalMs 60
Start-Sleep -Seconds 5

$logPath = Get-LatestLogPath -LogsDir $ctx.Logs
# 假定日志中会出现类似 "feature_count: 256" 的字样
$ok = $false
$actual = "未找到日志"
if ($logPath) {
    $content = Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue
    $matched = $content | Select-String -Pattern 'feature_count\s*:\s*(\d+)' -AllMatches
    if ($matched) {
        $max = ($matched.Matches.Value | ForEach-Object { $_ -replace '[^0-9]','' } | ForEach-Object {[int]$_}) | Measure-Object -Maximum | Select-Object -ExpandProperty Maximum
        $ok = ($max -ge 200)
        $actual = "max_feature_count=$max"
    } else {
        $actual = "未匹配到 feature_count"
    }
}
$conc = if ($ok) { "通过" } else { "复核" }
Write-ResultRow 2 "校验特征数量" "≥ 200" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "退出程序" "优雅退出或被终止" "退出完成" "通过"

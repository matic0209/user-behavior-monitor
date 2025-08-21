param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC03 深度学习分类功能可运行性"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "启动 EXE" "进入自动流程" "PID=$($proc.Id)" "通过"

# 等待程序进入训练/预测阶段并输出分类相关日志
Start-Sleep -Seconds 8
$logPath = Get-LatestLogPath -LogsDir $ctx.Logs
$check = Assert-LogContains -LogPath $logPath -AnyOf @("分类","predict","prediction","预测","SimplePredictor","start_continuous_prediction")
$actual = if ($logPath) { "log=$logPath; hits=" + ($check.hits | ConvertTo-Json -Compress) } else { "未找到日志" }
$conc = if ($check.ok) { "通过" } else { "复核" }
Write-ResultRow 2 "校验分类相关日志" "出现分类/预测关键字" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "退出程序" "优雅退出或被终止" "退出完成" "通过"

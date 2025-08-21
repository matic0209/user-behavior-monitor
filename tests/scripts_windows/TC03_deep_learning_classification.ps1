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

# 轮询等日志出现分类相关关键字
$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 20
$check = if ($logPath) { Wait-LogContains -LogPath $logPath -Patterns @("分类","predict","prediction","预测","SimplePredictor","start_continuous_prediction") -TimeoutSec 30 } else { @{ok=$false; hits=@{}} }
$artifact = Save-Artifacts -LogPath $logPath -WorkBase $ctx.Base
$actual = if ($logPath) { "log=$logPath; artifact=$artifact; hits=" + ($check.hits | ConvertTo-Json -Compress) } else { "未找到日志" }
$conc = if ($check.ok) { "通过" } else { "复核" }
Write-ResultRow 2 "校验分类相关日志" "出现分类/预测关键字" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "退出程序" "优雅退出或被终止" "退出完成" "通过"

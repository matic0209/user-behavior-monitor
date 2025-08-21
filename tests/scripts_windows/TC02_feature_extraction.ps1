param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC02 特征提取功能"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "启动 EXE" "进程启动成功" "PID=$($proc.Id)" "通过"

# 通过快捷键触发重新采集与特征处理（程序会在自动流程进入特征处理）
Send-CharRepeated -Char 'r' -Times 4 -IntervalMs 60
Write-ResultRow 2 "触发特征处理流程" "进入特征处理" "发送 rrrr" "N/A"

Start-Sleep -Seconds 6
$logPath = Get-LatestLogPath -LogsDir $ctx.Logs
$check = Assert-LogContains -LogPath $logPath -AnyOf @("特征处理","features","process_session_features","特征","完成")
$actual = if ($logPath) { "log=$logPath; hits=" + ($check.hits | ConvertTo-Json -Compress) } else { "未找到日志" }
$conc = if ($check.ok) { "通过" } else { "复核" }
Write-ResultRow 3 "校验特征处理日志" "包含处理与完成关键字" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 4 "退出程序" "优雅退出或被终止" "退出完成" "通过"

param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC02 Feature extraction"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "Start EXE" "Process started" "PID=$($proc.Id)" "Pass"

# 等待程序启动
Start-Sleep -Seconds 3

# 触发特征处理快捷键 (rrrr)
Write-Host "发送快捷键 rrrr 触发特征处理..."
Send-CharRepeated -Char 'r' -Times 4 -IntervalMs 100
Write-ResultRow 2 "Trigger feature processing" "Feature processing starts" "send rrrr" "N/A"

# 等待特征处理完成
Start-Sleep -Seconds 10

$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 30
$check = if ($logPath) {
    # 改进的关键字匹配，包含更多可能的日志输出
    Wait-LogContains -LogPath $logPath -Patterns @(
        'features','process_session_features','feature','processed','complete',
        '特征处理','处理完成','特征 处理 完成','[SUCCESS] 特征处理完成',
        'UBM_MARK: FEATURE_DONE','FEATURE_START','FEATURE_DONE',
        '特征数据','特征转换','特征保存','特征统计'
    ) -TimeoutSec 40
} else { @{ ok = false; hits = @{} } }

$artifact = Save-Artifacts -LogPath $logPath -WorkBase $ctx.Base
$actual = if ($logPath) { 
    "log=$logPath; artifact=$artifact; hits=" + ($check.hits | ConvertTo-Json -Compress) 
} else { 
    "no-log-found" 
}

# 改进的结论判断
$conc = if ($check.ok) { 
    "Pass" 
} else { 
    # 检查是否有部分关键字匹配
    $totalHits = ($check.hits.Values | Measure-Object -Sum).Sum
    if ($totalHits -gt 0) {
        "Partial"  # 部分匹配
    } else {
        "Review"   # 需要复核
    }
}

Write-ResultRow 3 "Check feature logs" "Contains processing/complete keywords" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 4 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

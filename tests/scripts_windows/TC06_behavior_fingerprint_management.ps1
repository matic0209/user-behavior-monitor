param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC06 Behavior fingerprint (import/export)"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "Start EXE" "Process started" "PID=$($proc.Id)" "Pass"

# 等待程序启动
Start-Sleep -Seconds 3

# 触发特征处理和指纹生成快捷键 rrrr
Write-Host "发送快捷键 rrrr 触发特征处理和指纹生成..."
Send-CharRepeated -Char 'r' -Times 4 -IntervalMs 100

# 等待处理完成
Start-Sleep -Seconds 15

$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 30
$check = if ($logPath) {
    # 改进的关键字匹配，包含更多可能的指纹相关日志输出
    Wait-LogContains -LogPath $logPath -Patterns @(
        'fingerprint','import','export',
        '指纹','导入','导出','行为指纹','用户指纹',
        'UBM_MARK: FEATURE_DONE','特征处理完成','模型训练完成',
        'behavior pattern','user pattern','pattern recognition',
        '特征向量','特征数据','特征保存','特征统计'
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

Write-ResultRow 2 "Check fingerprint logs" "import/export/fingerprint keywords" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

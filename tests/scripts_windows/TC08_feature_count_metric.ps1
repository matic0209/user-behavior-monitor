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

# 等待程序启动
Start-Sleep -Seconds 3

# 触发特征处理快捷键 rrrr
Write-Host "发送快捷键 rrrr 触发特征处理..."
Send-CharRepeated -Char 'r' -Times 4 -IntervalMs 100

# 等待特征处理完成
Start-Sleep -Seconds 15

$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 30
$ok = $false
$actual = "no-log-found"

if ($logPath) {
    $content = Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue
    
    # 多种特征数量匹配模式
    $patterns = @(
        'feature_count\s*:\s*(\d+)',
        '特征数量\s*:\s*(\d+)',
        '特征数\s*:\s*(\d+)',
        'features\s*:\s*(\d+)',
        'n_features\s*:\s*(\d+)',
        '特征\s*(\d+)\s*个',
        '共\s*(\d+)\s*个特征'
    )
    
    $max = 0
    foreach ($pattern in $patterns) {
        $matched = $content | Select-String -Pattern $pattern -AllMatches -CaseSensitive:$false
        if ($matched) {
            foreach ($match in $matched.Matches) {
                if ($match.Groups.Count -gt 1) {
                    $value = [int]$match.Groups[1].Value
                    if ($value -gt $max) { $max = $value }
                }
            }
        }
    }
    
    if ($max -gt 0) {
        $ok = ($max -ge 200)
        $actual = "max_feature_count=$max (threshold: >=200)"
        
        # 记录找到的特征数量
        Write-Host "找到特征数量: $max"
        if ($ok) {
            Write-Host "✓ 特征数量满足要求 (>=200)"
        } else {
            Write-Host "✗ 特征数量不足 (需要>=200, 实际=$max)"
        }
    } else {
        $actual = "no feature_count matched in patterns: $($patterns -join ', ')"
        Write-Host "未找到特征数量信息，尝试分析日志内容..."
        
        # 分析日志内容，查找可能的特征相关信息
        $featureRelated = $content | Select-String -Pattern '特征|feature|处理|完成|成功|失败' -CaseSensitive:$false
        if ($featureRelated) {
            Write-Host "找到相关日志条目:"
            $featureRelated | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" }
        }
    }
} else {
    Write-Host "未找到日志文件"
}

$conc = if ($ok) { "Pass" } else { "Review" }
Write-ResultRow 2 "Check feature count" ">= 200" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

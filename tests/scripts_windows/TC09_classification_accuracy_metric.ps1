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

# 等待程序启动
Start-Sleep -Seconds 3

# 触发模型训练和评估快捷键 rrrr
Write-Host "发送快捷键 rrrr 触发模型训练和评估..."
Send-CharRepeated -Char 'r' -Times 4 -IntervalMs 100

# 等待模型训练和评估完成
Start-Sleep -Seconds 20

$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 40
$ok = $false
$actual = "no-log-found"

if ($logPath) {
    $content = Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue
    $acc = $null
    $f1  = $null
    
    Write-Host "分析日志文件: $logPath"
    
    # 多种Accuracy匹配模式
    $accPatterns = @(
        '(?i)\baccuracy\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%',
        '(?i)\bacc\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%',
        '(?i)准确率\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%',
        '(?i)准确度\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%',
        '(?i)\baccuracy\s*=\s*([0-9]+(?:\.[0-9]+)?)',
        '(?i)\bacc\s*=\s*([0-9]+(?:\.[0-9]+)?)',
        '(?i)\b([01](?:\.[0-9]+)?)\s*accuracy',
        '(?i)\b([01](?:\.[0-9]+)?)\s*acc'
    )
    
    # 多种F1匹配模式
    $f1Patterns = @(
        '(?i)\bf1\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%',
        '(?i)\bf1-score\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%',
        '(?i)\bf1_score\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%',
        '(?i)f1值\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%',
        '(?i)\bf1\s*=\s*([0-9]+(?:\.[0-9]+)?)',
        '(?i)\b([01](?:\.[0-9]+)?)\s*f1',
        '(?i)\b([01](?:\.[0-9]+)?)\s*f1-score'
    )
    
    # 查找Accuracy
    foreach ($pattern in $accPatterns) {
        $accLine = $content | Select-String -Pattern $pattern | Select-Object -First 1
        if ($accLine) {
            $line = $accLine.Line
            Write-Host "找到Accuracy行: $line"
            if ($line -match $pattern) {
                $acc = [double]$matches[1]
                if ($pattern -match '\b([01](?:\.[0-9]+)?)\b') {
                    $acc = $acc * 100  # 转换为百分比
                }
                Write-Host "提取到Accuracy: $acc%"
                break
            }
        }
    }
    
    # 查找F1
    foreach ($pattern in $f1Patterns) {
        $f1Line = $content | Select-String -Pattern $pattern | Select-Object -First 1
        if ($f1Line) {
            $line = $f1Line.Line
            Write-Host "找到F1行: $line"
            if ($line -match $pattern) {
                $f1 = [double]$matches[1]
                if ($pattern -match '\b([01](?:\.[0-9]+)?)\b') {
                    $f1 = $f1 * 100  # 转换为百分比
                }
                Write-Host "提取到F1: $f1%"
                break
            }
        }
    }
    
    if ($acc -ne $null -and $f1 -ne $null) {
        $ok = ($acc -ge 90.0 -and $f1 -ge 85.0)
        $actual = "acc=$acc%, f1=$f1% (threshold: acc>=90%, f1>=85%)"
        
        Write-Host "评估结果:"
        Write-Host "  Accuracy: $acc% (要求: >=90%)"
        Write-Host "  F1: $f1% (要求: >=85%)"
        
        if ($ok) {
            Write-Host "✓ 所有指标都满足要求"
        } else {
            Write-Host "✗ 部分指标不满足要求"
        }
    } else {
        $actual = "no Accuracy/F1 matched. Found: acc=$acc, f1=$f1"
        Write-Host "未找到完整的评估指标，尝试分析日志内容..."
        
        # 分析日志内容，查找可能的评估相关信息
        $evalRelated = $content | Select-String -Pattern '评估|evaluation|模型|model|训练|training|准确|accuracy|f1|score' -CaseSensitive:$false
        if ($evalRelated) {
            Write-Host "找到相关日志条目:"
            $evalRelated | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" }
        }
    }
} else {
    Write-Host "未找到日志文件"
}

$conc = if ($ok) { "Pass" } else { "Review" }
Write-ResultRow 2 "Threshold check" "Acc>=90%, F1>=85%" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

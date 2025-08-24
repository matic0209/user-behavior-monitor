param(
    [string]$ExePath = "",
    [string]$WorkDir = "",
    [switch]$Verbose,
    [switch]$SkipFailed
)

. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Windows UBM 测试套件 - 改进版本" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 验证可执行文件
try {
    $exe = Resolve-ExePath $ExePath
    Write-Host "✓ 找到可执行文件: $exe" -ForegroundColor Green
} catch {
    Write-Error "❌ 可执行文件未找到: $ExePath"
    Write-Host "请确保 UserBehaviorMonitor.exe 已构建并位于 dist/ 目录中" -ForegroundColor Yellow
    exit 1
}

# 准备工作目录
try {
    $ctx = Prepare-WorkDir $WorkDir
    Write-Host "✓ 工作目录已准备: $($ctx.Base)" -ForegroundColor Green
    Write-Host "  数据目录: $($ctx.Data)" -ForegroundColor Gray
    Write-Host "  日志目录: $($ctx.Logs)" -ForegroundColor Gray
    Write-Host "  数据库: $($ctx.Db)" -ForegroundColor Gray
} catch {
    Write-Error "❌ 工作目录准备失败: $_"
    exit 1
}

# 测试用例列表
$testCases = @(
    @{ Name = "TC02"; Script = "TC02_feature_extraction.ps1"; Description = "特征提取功能" },
    @{ Name = "TC06"; Script = "TC06_behavior_fingerprint_management.ps1"; Description = "行为指纹管理" },
    @{ Name = "TC08"; Script = "TC08_feature_count_metric.ps1"; Description = "特征数量阈值" },
    @{ Name = "TC09"; Script = "TC09_classification_accuracy_metric.ps1"; Description = "分类准确率指标" },
    @{ Name = "TC10"; Script = "TC10_anomaly_false_alarm_rate.ps1"; Description = "异常误报率" }
)

# 测试结果统计
$results = @{
    Total = $testCases.Count
    Passed = 0
    Failed = 0
    Skipped = 0
    StartTime = Get-Date
}

Write-Host "`n开始执行测试用例..." -ForegroundColor Yellow
Write-Host "总计: $($results.Total) 个测试用例" -ForegroundColor Yellow
Write-Host "开始时间: $($results.StartTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Yellow
Write-Host ""

# 执行测试用例
foreach ($testCase in $testCases) {
    $testName = $testCase.Name
    $scriptPath = Join-Path $PSScriptRoot $testCase.Script
    $description = $testCase.Description
    
    Write-Host "==========================================" -ForegroundColor DarkGray
    Write-Host "执行测试: $testName - $description" -ForegroundColor White
    Write-Host "脚本: $testCase.Script" -ForegroundColor Gray
    Write-Host "==========================================" -ForegroundColor DarkGray
    
    if (-not (Test-Path $scriptPath)) {
        Write-Warning "⚠️  测试脚本不存在: $scriptPath"
        $results.Skipped++
        continue
    }
    
    try {
        # 执行测试脚本
        $testStartTime = Get-Date
        Write-Host "开始时间: $($testStartTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
        
        & $scriptPath -ExePath $exe -WorkDir $ctx.Base
        
        $testEndTime = Get-Date
        $duration = $testEndTime - $testStartTime
        
        Write-Host "完成时间: $($testEndTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
        Write-Host "执行时长: $($duration.TotalSeconds.ToString('F1')) 秒" -ForegroundColor Gray
        
        # 检查测试结果
        $logPath = Get-LatestLogPath -LogsDir $ctx.Logs
        if ($logPath) {
            Write-Host "✓ 测试完成，日志文件: $logPath" -ForegroundColor Green
            $results.Passed++
        } else {
            Write-Warning "⚠️  测试完成但未找到日志文件"
            $results.Failed++
        }
        
    } catch {
        Write-Error "❌ 测试执行失败: $_"
        $results.Failed++
        
        if (-not $SkipFailed) {
            Write-Host "是否继续执行下一个测试? (Y/N)" -ForegroundColor Yellow
            $response = Read-Host
            if ($response -notmatch '^[Yy]') {
                Write-Host "用户选择停止测试" -ForegroundColor Yellow
                break
            }
        }
    }
    
    Write-Host ""
}

# 测试结果汇总
$endTime = Get-Date
$totalDuration = $endTime - $results.StartTime

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "测试执行完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "结束时间: $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Yellow
Write-Host "总耗时: $($totalDuration.TotalMinutes.ToString('F1')) 分钟" -ForegroundColor Yellow
Write-Host ""
Write-Host "测试结果统计:" -ForegroundColor White
Write-Host "  总计: $($results.Total)" -ForegroundColor Gray
Write-Host "  通过: $($results.Passed)" -ForegroundColor Green
Write-Host "  失败: $($results.Failed)" -ForegroundColor Red
Write-Host "  跳过: $($results.Skipped)" -ForegroundColor Yellow
Write-Host "  成功率: $([math]::Round(($results.Passed / $results.Total) * 100, 1))%" -ForegroundColor Cyan

# 生成测试报告
$reportPath = Join-Path $ctx.Base "test_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
try {
    $report = @"
Windows UBM 测试报告
====================
测试时间: $($results.StartTime.ToString('yyyy-MM-dd HH:mm:ss')) - $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))
总耗时: $($totalDuration.TotalMinutes.ToString('F1')) 分钟

测试结果:
  总计: $($results.Total)
  通过: $($results.Passed)
  失败: $($results.Failed)
  跳过: $($results.Skipped)
  成功率: $([math]::Round(($results.Passed / $results.Total) * 100, 1))%

工作目录: $($ctx.Base)
可执行文件: $exe

详细日志请查看: $($ctx.Logs)
"@
    
    $report | Out-File -FilePath $reportPath -Encoding UTF8
    Write-Host "`n测试报告已保存: $reportPath" -ForegroundColor Green
    
} catch {
    Write-Warning "测试报告保存失败: $_"
}

Write-Host "`n测试执行完成！" -ForegroundColor Green

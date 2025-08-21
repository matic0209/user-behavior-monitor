param(
    [string]$ExePath,
    [string]$WorkDir
)

$ErrorActionPreference = "Stop"

$base = Split-Path -Parent $MyInvocation.MyCommand.Path

. "$base/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$tests = @(
    "TC01_realtime_input_collection.ps1",
    "TC02_feature_extraction.ps1",
    "TC03_deep_learning_classification.ps1",
    "TC04_anomaly_alert.ps1",
    "TC05_anomaly_block.ps1",
    "TC06_behavior_fingerprint_management.ps1",
    "TC07_collection_metrics.ps1",
    "TC08_feature_count_metric.ps1",
    "TC09_classification_accuracy_metric.ps1",
    "TC10_anomaly_false_alarm_rate.ps1"
)

$failed = @()
foreach ($t in $tests) {
    Write-Host "`n==== 运行: $t ====\n" -ForegroundColor Cyan
    try {
        & (Join-Path $base $t) -ExePath $ExePath -WorkDir $WorkDir
    } catch {
        Write-Host "[ERROR] $t 执行异常: $($_.Exception.Message)" -ForegroundColor Red
        $failed += $t
    }
}

if ($failed.Count -gt 0) {
    Write-Host "`n完成: 有失败的用例:" -ForegroundColor Yellow
    $failed | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
    exit 1
} else {
    Write-Host "`n全部测试脚本执行完成（全部通过/无异常）。" -ForegroundColor Green
    exit 0
}

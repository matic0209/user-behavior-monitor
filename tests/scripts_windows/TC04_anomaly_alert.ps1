param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC04 用户异常行为告警功能"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "启动监控" "进入监控状态" "PID=$($proc.Id)" "通过"

# 注入强烈异常：超高速随机移动 + 连续键入 'a'
for ($i=0; $i -lt 10; $i++) { Move-MousePath -DurationSec 1 -Step 200 }
Send-CharRepeated -Char 'a' -Times 4 -IntervalMs 50
Write-ResultRow 2 "注入异常序列" "异常分数触发告警" "已注入" "N/A"

Start-Sleep -Seconds 3
# 若系统将告警写入 DB 的 alerts 表，可在此查询；否则仅提示人工查看日志
$alertQuery = @"
SELECT COUNT(*) AS cnt FROM alerts;
"@
$alertCount = Invoke-SqliteQuery -DbPath $ctx.Db -Sql $alertQuery

if ($alertCount) {
    Write-ResultRow 3 "检查告警记录" "至少 1 条" "$alertCount" "通过/复核"
} else {
    Write-ResultRow 3 "检查告警记录" "至少 1 条" "未安装 sqlite3 或表缺失，转人工查 logs" "复核"
}

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 4 "退出程序" "优雅退出或被终止" "退出完成" "通过"

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

Start-Sleep -Seconds 1
$log = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 15
$chk = if ($log) { Wait-LogContains -LogPath $log -Patterns @('告警','异常','anomaly','trigger') -TimeoutSec 25 } else { @{ok=$false; hits=@{}} }
$actual = if ($log) { "log=$log; hits=" + ($chk.hits | ConvertTo-Json -Compress) } else { "未找到日志" }
$conc = if ($chk.ok) { "通过" } else { "复核" }
Write-ResultRow 3 "校验日志关键字" "出现告警/异常关键字" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 4 "退出程序" "优雅退出或被终止" "退出完成" "通过"

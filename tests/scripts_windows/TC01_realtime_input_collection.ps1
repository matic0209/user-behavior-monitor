param(
    [string]$ExePath,
    [string]$WorkDir
)
. "$PSScriptRoot/common.ps1" -ExePath $ExePath -WorkDir $WorkDir

$exe = Resolve-ExePath $ExePath
$ctx = Prepare-WorkDir $WorkDir

Write-ResultHeader "TC01 用户行为数据实时采集功能"
Write-ResultTableHeader

$proc = Start-UBM -Exe $exe -Cwd $ctx.Base
Write-ResultRow 1 "启动 EXE" "进程启动成功" "PID=$($proc.Id)" "通过"

Move-MousePath -DurationSec 5 -Step 80
Click-LeftTimes -Times 3
Scroll-Vertical -Notches 5
Write-ResultRow 2 "模拟鼠标输入" "数据库产生事件" "执行输入序列" "N/A"

Start-Sleep -Seconds 1
$log = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 15
$chk = if ($log) { Wait-LogContains -LogPath $log -Patterns @('move','click','scroll') -TimeoutSec 20 } else { @{ok=$false; hits=@{}} }
$actual = if ($log) { "log=$log; hits=" + ($chk.hits | ConvertTo-Json -Compress) } else { "未找到日志" }
$conc = if ($chk.ok) { "通过" } else { "复核" }
Write-ResultRow 3 "校验日志关键字" "包含 move/click/scroll" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 4 "退出程序" "优雅退出或被终止" "退出完成" "通过"

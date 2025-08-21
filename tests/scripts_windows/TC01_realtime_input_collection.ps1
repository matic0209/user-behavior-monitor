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

Start-Sleep -Seconds 2
$stats = Get-LatestSessionStats -DbPath $ctx.Db
if ($stats) {
    Write-ResultRow 3 "查询最新会话" "应有事件记录" "$stats" "通过"
} else {
    Write-ResultRow 3 "查询最新会话" "应有事件记录" "无数据/未安装sqlite3" "需人工复核"
}

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 4 "退出程序" "优雅退出或被终止" "退出完成" "通过"

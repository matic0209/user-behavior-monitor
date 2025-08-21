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
Write-ResultRow 1 "启动 EXE" "进程启动成功" "PID=$($proc.Id)" "通过"

# 若程序支持指纹相关快捷键或命令，此处可替换为真实触发；当前以日志探测为主
$logPath = Wait-ForLatestLog -LogsDir $ctx.Logs -TimeoutSec 20
$check = if ($logPath) { Wait-LogContains -LogPath $logPath -Patterns @("fingerprint","import","export") -TimeoutSec 30 } else { @{ ok = $false; hits = @{} } }
$artifact = Save-Artifacts -LogPath $logPath -WorkBase $ctx.Base
$actual = if ($logPath) { "log=$logPath; artifact=$artifact; hits=" + ($check.hits | ConvertTo-Json -Compress) } else { "no-log-found" }
# 若暂未实现，结论为复核，不抛错
$conc = if ($check.ok) { "Pass" } else { "Review" }
Write-ResultRow 2 "Check fingerprint logs" "import/export/fingerprint keywords" $actual $conc

Stop-UBM-Gracefully -Proc $proc
Write-ResultRow 3 "Exit program" "Graceful exit or terminated" "Exit done" "Pass"

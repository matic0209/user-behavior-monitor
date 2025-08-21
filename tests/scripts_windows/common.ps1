param(
    [string]$ExePath = "",
    [string]$WorkDir = "",
    [switch]$VerboseLog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# 计算项目根目录与默认路径
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$testsDir  = Split-Path -Parent $scriptDir
$projectRoot = Split-Path -Parent $testsDir

if ([string]::IsNullOrWhiteSpace($ExePath)) {
    $ExePath = Join-Path $projectRoot "dist/UserBehaviorMonitor.exe"
}
if ([string]::IsNullOrWhiteSpace($WorkDir)) {
    $WorkDir = Join-Path $projectRoot "win_test_run"
}

Add-Type -AssemblyName System.Windows.Forms

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Get-Timestamp {
    return (Get-Date).ToString("yyyy-MM-dd_HH-mm-ss")
}

function Resolve-ExePath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "ExePath 为空，且未能推导默认路径。"
    }
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "未找到可执行文件: $Path"
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

function Prepare-WorkDir {
    param([string]$BaseDir)
    if ([string]::IsNullOrWhiteSpace($BaseDir)) {
        $BaseDir = $WorkDir
    }
    Ensure-Dir $BaseDir
    $abs = (Resolve-Path -LiteralPath $BaseDir).Path

    $dataDir = Join-Path $abs "data"
    $logsDir = Join-Path $abs "logs"
    Ensure-Dir $dataDir
    Ensure-Dir $logsDir

    # 使用环境变量强制指定数据库路径（程序支持 UBM_DATABASE）
    $env:UBM_DATABASE = Join-Path $abs "data\mouse_data.db"
    return @{ Base=$abs; Data=$dataDir; Logs=$logsDir; Db=$env:UBM_DATABASE }
}

# User32 输入模拟（低依赖）
Add-Type -Namespace WinAPI -Name NativeMethods -MemberDefinition @'
    [System.Runtime.InteropServices.DllImport("user32.dll")]
    public static extern bool SetCursorPos(int X, int Y);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    public static extern void mouse_event(int dwFlags, int dx, int dy, int dwData, int dwExtraInfo);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    public static extern short VkKeyScan(char ch);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, System.UIntPtr dwExtraInfo);
'@

$MOUSEEVENTF_LEFTDOWN = 0x02
$MOUSEEVENTF_LEFTUP   = 0x04
$MOUSEEVENTF_WHEEL    = 0x0800
$KEYEVENTF_KEYUP      = 0x0002

function Move-MousePath {
    param([int]$DurationSec = 5, [int]$Step = 50)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $width  = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width
    $height = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height
    $y = [int]($height/2)
    for ($x = 100; $x -lt $width-100 -and $sw.Elapsed.TotalSeconds -lt $DurationSec; $x += $Step) {
        [WinAPI.NativeMethods]::SetCursorPos($x, $y) | Out-Null
        Start-Sleep -Milliseconds 30
    }
}

function Click-LeftTimes {
    param([int]$Times = 3)
    for ($i=0; $i -lt $Times; $i++) {
        [WinAPI.NativeMethods]::mouse_event($MOUSEEVENTF_LEFTDOWN,0,0,0,0)
        Start-Sleep -Milliseconds 50
        [WinAPI.NativeMethods]::mouse_event($MOUSEEVENTF_LEFTUP,0,0,0,0)
        Start-Sleep -Milliseconds 120
    }
}

function Scroll-Vertical {
    param([int]$Notches = 3)
    for ($i=0; $i -lt [Math]::Abs($Notches); $i++) {
        $delta = if ($Notches -ge 0) { 120 } else { -120 }
        [WinAPI.NativeMethods]::mouse_event($MOUSEEVENTF_WHEEL,0,0,$delta,0)
        Start-Sleep -Milliseconds 150
    }
}

function Send-CharRepeated {
    param([char]$Char='a', [int]$Times=4, [int]$IntervalMs=60)
    $vk = [byte]([WinAPI.NativeMethods]::VkKeyScan($Char) -band 0xFF)
    for ($i=0; $i -lt $Times; $i++) {
        [WinAPI.NativeMethods]::keybd_event($vk,0,0,[UIntPtr]::Zero)
        Start-Sleep -Milliseconds $IntervalMs
        [WinAPI.NativeMethods]::keybd_event($vk,0,$KEYEVENTF_KEYUP,[UIntPtr]::Zero)
        Start-Sleep -Milliseconds $IntervalMs
    }
}

function Start-UBM {
    param([string]$Exe, [string]$Cwd)
    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = $Exe
    $pinfo.WorkingDirectory = $Cwd
    $pinfo.UseShellExecute = $true
    $pinfo.WindowStyle = "Minimized"
    $proc = [System.Diagnostics.Process]::Start($pinfo)
    return $proc
}

function Stop-UBM-Gracefully {
    param([System.Diagnostics.Process]$Proc)
    # 发送 qqqq 触发程序退出快捷键
    Send-CharRepeated -Char 'q' -Times 4 -IntervalMs 80
    Start-Sleep -Seconds 2
    if ($Proc -and -not $Proc.HasExited) { $Proc.Kill() }
}

function Get-Sqlite3Path {
    $candidate = "sqlite3.exe"
    $inPath = (Get-Command $candidate -ErrorAction SilentlyContinue)
    if ($inPath) { return $inPath.Path }
    $local = Join-Path (Get-Location) $candidate
    if (Test-Path -LiteralPath $local) { return $local }
    return $null
}

function Invoke-SqliteQuery {
    param([string]$DbPath,[string]$Sql)
    $sqlite = Get-Sqlite3Path
    if (-not $sqlite) { return $null }
    if (-not (Test-Path -LiteralPath $DbPath)) { return $null }
    $args = @("-header","-csv", $DbPath, $Sql)
    $out = & $sqlite @args
    return $out
}

function Get-LatestSessionStats {
    param([string]$DbPath)
    $sql = @"
SELECT user_id, session_id, COUNT(*) AS event_count, MAX(timestamp) AS last_ts
FROM mouse_events
GROUP BY user_id, session_id
ORDER BY last_ts DESC
LIMIT 1;
"@
    return (Invoke-SqliteQuery -DbPath $DbPath -Sql $sql)
}

function Get-LatestLogPath {
    param([string]$LogsDir)
    if (-not (Test-Path -LiteralPath $LogsDir)) { return $null }
    $files = Get-ChildItem -LiteralPath $LogsDir -Filter *.log -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($files -and $files.Count -gt 0) { return $files[0].FullName }
    return $null
}

function Assert-LogContains {
    param([string]$LogPath, [string[]]$AnyOf)
    if (-not $LogPath -or -not (Test-Path -LiteralPath $LogPath)) { return @{ ok=$false; hits=@{} } }
    $result = @{}
    $ok = $false
    foreach ($p in $AnyOf) {
        $m = Select-String -LiteralPath $LogPath -Pattern $p -SimpleMatch -ErrorAction SilentlyContinue
        $count = if ($m) { $m.Count } else { 0 }
        $result[$p] = $count
        if ($count -gt 0) { $ok = $true }
    }
    return @{ ok=$ok; hits=$result }
}

function Write-ResultHeader {
    param([string]$Title)
    "# $Title" | Out-Host
}

function Write-ResultTableHeader {
    "| 序号 | 输入及操作 | 期望结果或评估标准 | 实测结果 | 测试结论 |" | Out-Host
    "| --- | --- | --- | --- | --- |" | Out-Host
}

function Write-ResultRow {
    param([int]$Index,[string]$Action,[string]$Expect,[string]$Actual,[string]$Conclusion)
    "| $Index | $Action | $Expect | $Actual | $Conclusion |" | Out-Host
}

if ($VerboseLog) { Write-Host "[common] 已加载通用函数" }

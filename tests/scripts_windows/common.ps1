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
        throw "ExePath is empty and no default could be resolved."
    }
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Executable not found: $Path"
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

# Database helper functions removed (not needed for log-only checks)

function Get-LatestLogPath {
    param([string]$LogsDir)
    if (-not (Test-Path -LiteralPath $LogsDir)) { return $null }
    $files = Get-ChildItem -LiteralPath $LogsDir -Filter *.log -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($files -and $files.Count -gt 0) { return $files[0].FullName }
    return $null
}

function Assert-LogContains {
    param(
        [string]$LogPath,
        [string[]]$Patterns,
        [switch]$Regex,
        [switch]$CaseSensitive
    )
    if (-not $LogPath -or -not (Test-Path -LiteralPath $LogPath)) { return @{ ok=$false; hits=@{} } }
    $result = @{}
    $ok = $false
    foreach ($p in $Patterns) {
        $params = @{ LiteralPath = $LogPath; Pattern = $p; ErrorAction = 'SilentlyContinue' }
        if ($Regex) { $params.Remove('Pattern') | Out-Null; $params['Pattern'] = $p }
        if (-not $CaseSensitive) { $params['CaseSensitive'] = $false }
        $m = Select-String @params
        $count = if ($m) { $m.Count } else { 0 }
        $result[$p] = $count
        if ($count -gt 0) { $ok = $true }
    }
    return @{ ok=$ok; hits=$result }
}

function Wait-ForLatestLog {
    param([string]$LogsDir, [int]$TimeoutSec = 15, [int]$IntervalMs = 500)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $p = Get-LatestLogPath -LogsDir $LogsDir
        if ($p) { return $p }
        Start-Sleep -Milliseconds $IntervalMs
    }
    return $null
}

function Wait-LogContains {
    param(
        [string]$LogPath,
        [string[]]$Patterns,
        [int]$TimeoutSec = 30,
        [int]$IntervalMs = 500,
        [switch]$Regex,
        [switch]$CaseSensitive
    )
    if (-not $LogPath -or -not (Test-Path -LiteralPath $LogPath)) { return @{ ok=$false; hits=@{} } }
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $lastHits = @{}
    while ((Get-Date) -lt $deadline) {
        $res = Assert-LogContains -LogPath $LogPath -Patterns $Patterns -Regex:$Regex -CaseSensitive:$CaseSensitive
        $lastHits = $res.hits
        if ($res.ok) { return @{ ok=$true; hits=$res.hits } }
        Start-Sleep -Milliseconds $IntervalMs
    }
    return @{ ok=$false; hits=$lastHits }
}

function Save-Artifacts {
    param([string]$LogPath, [string]$WorkBase)
    if (-not $LogPath -or -not (Test-Path -LiteralPath $LogPath)) { return $null }
    $ts = Get-Timestamp
    $targetDir = Join-Path $WorkBase (Join-Path 'artifacts' $ts)
    Ensure-Dir $targetDir
    $dest = Join-Path $targetDir (Split-Path $LogPath -Leaf)
    Copy-Item -LiteralPath $LogPath -Destination $dest -Force
    return $dest
}

function Write-ResultHeader {
    param([string]$Title)
    $line = "# $Title"
    $line | Out-Host
    if ($env:UBM_RESULT_FILE) { Add-Content -LiteralPath $env:UBM_RESULT_FILE -Value $line -Encoding UTF8 }
}

function Write-ResultTableHeader {
    $line1 = "| Index | Action | Expectation | Actual | Conclusion |"
    $line2 = "| --- | --- | --- | --- | --- |"
    $line1 | Out-Host
    $line2 | Out-Host
    if ($env:UBM_RESULT_FILE) {
        Add-Content -LiteralPath $env:UBM_RESULT_FILE -Value $line1 -Encoding UTF8
        Add-Content -LiteralPath $env:UBM_RESULT_FILE -Value $line2 -Encoding UTF8
    }
}

function Write-ResultRow {
    param([int]$Index,[string]$Action,[string]$Expect,[string]$Actual,[string]$Conclusion)
    $line = "| $Index | $Action | $Expect | $Actual | $Conclusion |"
    $line | Out-Host
    if ($env:UBM_RESULT_FILE) { Add-Content -LiteralPath $env:UBM_RESULT_FILE -Value $line -Encoding UTF8 }
}

if ($VerboseLog) { Write-Host "[common] helpers loaded" }

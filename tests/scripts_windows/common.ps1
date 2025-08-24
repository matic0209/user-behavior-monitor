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
    
    # 改进的快捷键发送函数
    try {
        $vk = [byte]([WinAPI.NativeMethods]::VkKeyScan($Char) -band 0xFF)
        
        # 确保程序窗口获得焦点
        Start-Sleep -Milliseconds 500
        
        for ($i=0; $i -lt $Times; $i++) {
            # 按下键
            [WinAPI.NativeMethods]::keybd_event($vk,0,0,[UIntPtr]::Zero)
            Start-Sleep -Milliseconds $IntervalMs
            
            # 释放键
            [WinAPI.NativeMethods]::keybd_event($vk,0,$KEYEVENTF_KEYUP,[UIntPtr]::Zero)
            Start-Sleep -Milliseconds $IntervalMs
            
            # 额外延迟确保按键被识别
            Start-Sleep -Milliseconds 100
        }
        
        # 等待程序处理快捷键
        Start-Sleep -Seconds 2
        
        Write-Host "已发送快捷键: $Char 重复 $Times 次"
        
    } catch {
        Write-Warning "快捷键发送失败: $_"
        # 备用方案：使用SendKeys
        try {
            Add-Type -AssemblyName System.Windows.Forms
            for ($i=0; $i -lt $Times; $i++) {
                [System.Windows.Forms.SendKeys]::SendWait($Char)
                Start-Sleep -Milliseconds $IntervalMs
            }
            Write-Host "使用备用方案发送快捷键成功"
        } catch {
            Write-Error "备用快捷键发送也失败: $_"
        }
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
    if (-not $LogPath -or -not (Test-Path -LiteralPath $LogPath)) { 
        Write-Warning "日志文件不存在: $LogPath"
        return @{ ok=$false; hits=@{} } 
    }
    
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $lastHits = @{}
    $attempts = 0
    
    Write-Host "等待日志包含关键字，超时时间: ${TimeoutSec}秒"
    Write-Host "搜索模式: $($Patterns -join ', ')"
    
    while ((Get-Date) -lt $deadline) {
        $attempts++
        $currentHits = @{}
        $foundAny = $false
        
        foreach ($pattern in $Patterns) {
            try {
                $params = @{ LiteralPath = $LogPath; Pattern = $pattern; ErrorAction = 'SilentlyContinue' }
                if ($Regex) { 
                    $params.Remove('Pattern') | Out-Null; 
                    $params['Pattern'] = $pattern 
                }
                if (-not $CaseSensitive) { 
                    $params['CaseSensitive'] = $false 
                }
                
                $matches = Select-String @params
                $count = if ($matches) { $matches.Count } else { 0 }
                $currentHits[$pattern] = $count
                
                if ($count -gt 0) {
                    $foundAny = $true
                    if ($attempts -eq 1) {
                        Write-Host "✓ 找到关键字 '$pattern': $count 次"
                    }
                }
            } catch {
                Write-Warning "搜索模式 '$pattern' 时出错: $_"
                $currentHits[$pattern] = 0
            }
        }
        
        # 检查是否有新的匹配
        $newMatches = $false
        foreach ($pattern in $Patterns) {
            $current = $currentHits[$pattern]
            $last = $lastHits[$pattern]
            if ($current -gt $last) {
                $newMatches = $true
                break
            }
        }
        
        if ($foundAny) {
            if ($newMatches) {
                Write-Host "发现新的日志匹配 (尝试 $attempts)"
            }
            
            # 如果所有模式都找到了，提前返回
            $allFound = $true
            foreach ($pattern in $Patterns) {
                if ($currentHits[$pattern] -eq 0) {
                    $allFound = $false
                    break
                }
            }
            
            if ($allFound) {
                Write-Host "✓ 所有关键字都已找到，提前返回"
                return @{ ok=$true; hits=$currentHits }
            }
        }
        
        $lastHits = $currentHits.Clone()
        
        # 每5次尝试显示一次进度
        if ($attempts % 5 -eq 0) {
            $remaining = [math]::Round(($deadline - (Get-Date)).TotalSeconds, 1)
            Write-Host "等待中... 剩余时间: ${remaining}秒 (尝试 $attempts)"
        }
        
        Start-Sleep -Milliseconds $IntervalMs
    }
    
    Write-Warning "超时，未找到所有关键字"
    Write-Host "最终匹配结果:"
    foreach ($pattern in $Patterns) {
        $count = $lastHits[$pattern]
        $status = if ($count -gt 0) { "✓" } else { "✗" }
        Write-Host "  $status $pattern`: $count 次"
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

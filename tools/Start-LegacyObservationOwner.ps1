param(
    [Parameter(Mandatory = $true)][string]$Slot,
    [switch]$Detach
)
$ErrorActionPreference = 'Stop'
$taskSlot = (Resolve-Path -LiteralPath $Slot).Path
if ($Detach) {
    # 启动前使用隐藏宿主；聚焦之后只通过文件投递，不再启动终端。
    Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -WindowStyle Hidden -ArgumentList @(
        '-NoProfile', '-File', ('"' + $PSCommandPath + '"'), '-Slot', ('"' + $taskSlot + '"')
    ) | Out-Null
    return
}
$taskPlan = Get-Content -LiteralPath (Join-Path $taskSlot 'live-plan.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskRepository = Split-Path -Parent $PSScriptRoot
$taskOwner = Join-Path $taskRepository 'tools/legacy_observation_owner.py'
$taskStart = New-Object System.Diagnostics.ProcessStartInfo
$taskStart.FileName = $taskPlan.base_python
$taskStart.Arguments = '"' + $taskOwner + '" "' + $taskSlot + '"'
$taskStart.WorkingDirectory = $taskSlot
$taskStart.UseShellExecute = $false
$taskStart.CreateNoWindow = $true
$taskStart.RedirectStandardOutput = $true
$taskStart.RedirectStandardError = $true
$taskStart.EnvironmentVariables['PYTHONUTF8'] = '1'
$taskProcess = New-Object System.Diagnostics.Process
$taskProcess.StartInfo = $taskStart
$taskStarted = $taskProcess.Start()
try {
    $taskHeld = @{
        pid = $taskProcess.Id
        original_handle = $taskProcess.Handle.ToInt64()
        creation_filetime = $taskProcess.StartTime.ToUniversalTime().ToFileTimeUtc()
        actual_image = $taskProcess.MainModule.FileName
        creator = 'PowerShell 原 System.Diagnostics.Process 对象，持续持柄并 WaitForExit'
    }
    $taskHeld | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskSlot 'owner-created.json') -Encoding UTF8
    $taskStdout = $taskProcess.StandardOutput.ReadToEndAsync()
    $taskStderr = $taskProcess.StandardError.ReadToEndAsync()
    $taskProcess.WaitForExit()
    $taskStdout.Result | Set-Content -LiteralPath (Join-Path $taskSlot 'owner-stdout.log') -Encoding UTF8
    $taskStderr.Result | Set-Content -LiteralPath (Join-Path $taskSlot 'owner-stderr.log') -Encoding UTF8
    @{identity = $taskHeld; wait_return = $taskProcess.ExitCode; at = [DateTime]::UtcNow.ToString('o')} |
        ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskSlot 'owner-exit.json') -Encoding UTF8
}
finally {
    # 创建后身份记录异常也不遗弃原进程；不使用 Kill 或其它退出替代路径。
    if (-not $taskProcess.HasExited) { $taskProcess.WaitForExit() }
    $taskProcess.Dispose()
}

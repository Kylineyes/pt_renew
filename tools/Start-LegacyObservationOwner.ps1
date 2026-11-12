param(
    [Parameter(Mandatory = $true)][string]$Slot,
    [switch]$Detach,
    [switch]$OfflineCheck,
    [switch]$PreflightOnly
)
$ErrorActionPreference = 'Stop'
# Windows PowerShell 5.1 的 -File 对无 BOM 文件使用本机传统编码；本文件必须保留 UTF-8 BOM。
if ($OfflineCheck) {
    $taskBytes = [IO.File]::ReadAllBytes($PSCommandPath)
    if ($taskBytes.Length -lt 3 -or $taskBytes[0] -ne 239 -or $taskBytes[1] -ne 187 -or $taskBytes[2] -ne 191) {
        throw '启动器缺少 UTF-8 BOM，拒绝继续'
    }
    @{
        offline_check = $true
        detach_boundary = [bool]$Detach
        before_any_process_creation = $true
        script = $PSCommandPath
        version = $PSVersionTable.PSVersion.ToString()
        utf8_bom = $true
    } | ConvertTo-Json
    exit 0
}
function Assert-LegacyObservationStart {
    param($Plan, $Approval, [string]$PlanSha256, [string]$ResolvedSlot, [DateTimeOffset]$NowUtc)
    if ($Approval.approved_plan_sha256 -cne $PlanSha256) { throw '入口拒绝：GO 未批准当前计划摘要' }
    foreach ($taskKey in @('session', 'task', 'dispatch')) {
        if ($Approval.$taskKey -cne $Plan.$taskKey) { throw '入口拒绝：GO 身份不符' }
    }
    if ([IO.Path]::GetFullPath($Plan.slot) -cne [IO.Path]::GetFullPath($ResolvedSlot)) {
        throw '入口拒绝：计划槽路径不符'
    }
    $taskStartUtc = [DateTimeOffset]::Parse($Approval.start_utc).ToUniversalTime()
    $taskDeadlineUtc = [DateTimeOffset]::Parse($Approval.deadline_utc).ToUniversalTime()
    $taskBudget = ($taskDeadlineUtc - $taskStartUtc).TotalSeconds
    if ($taskBudget -le 420 -or $taskBudget -gt 3600) { throw '入口拒绝：完整时段须超过七分钟且不超过六十分钟' }
    if ($NowUtc -lt $taskStartUtc) { throw '入口拒绝：尚未到 GO 开始时间，零现场进程创建' }
    if ($NowUtc -ge $taskDeadlineUtc.AddSeconds(-420)) { throw '入口拒绝：已过业务起跑截止，零现场进程创建' }
}
$taskSlot = [IO.Path]::GetFullPath($Slot)
$taskPlanPath = Join-Path $taskSlot 'live-plan.json'
$taskPlan = Get-Content -LiteralPath $taskPlanPath -Raw -Encoding UTF8 | ConvertFrom-Json
$taskApproval = Get-Content -LiteralPath (Join-Path $taskSlot 'go-start.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskPlanSha = (Get-FileHash -LiteralPath $taskPlanPath -Algorithm SHA256).Hash.ToLowerInvariant()
Assert-LegacyObservationStart -Plan $taskPlan -Approval $taskApproval -PlanSha256 $taskPlanSha -ResolvedSlot $taskSlot -NowUtc ([DateTimeOffset]::UtcNow)
foreach ($taskMarker in @('owner-created.json', 'driver-created.json', 'runner-started.json')) {
    if (Test-Path -LiteralPath (Join-Path $taskSlot $taskMarker)) { throw '入口拒绝：该槽已有启动记录，不重试' }
}
if ($PreflightOnly) {
    @{ preflight_only = $true; before_any_process_creation = $true; allowed = $true; detach_boundary = [bool]$Detach } | ConvertTo-Json
    exit 0
}
if ($Detach) {
    # 两层正式入口都先做只读Python语义检查；失败不创建owner或其输出。
    $taskValidator = Join-Path (Split-Path -Parent $PSScriptRoot) 'tools/legacy_runtime_config.py'
    & $taskPlan.base_python -B $taskValidator --plan $taskPlanPath | Out-Null
    if ($LASTEXITCODE -ne 0) { throw '入口拒绝：隔离计划语义预检失败，零owner/driver创建' }
    Assert-LegacyObservationStart -Plan $taskPlan -Approval $taskApproval -PlanSha256 $taskPlanSha -ResolvedSlot $taskSlot -NowUtc ([DateTimeOffset]::UtcNow)
    # 启动前使用隐藏宿主；聚焦之后只通过文件投递，不再启动终端。
    Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -WindowStyle Hidden -ArgumentList @(
        '-NoProfile', '-File', ('"' + $PSCommandPath + '"'), '-Slot', ('"' + $taskSlot + '"')
    ) | Out-Null
    return
}
$taskValidator = Join-Path (Split-Path -Parent $PSScriptRoot) 'tools/legacy_runtime_config.py'
& $taskPlan.base_python -B $taskValidator --plan $taskPlanPath | Out-Null
if ($LASTEXITCODE -ne 0) { throw '入口拒绝：隔离计划语义预检失败，零owner/driver创建' }
$taskRepository = Split-Path -Parent $PSScriptRoot
$taskOwner = Join-Path $taskRepository 'tools/legacy_observation_owner.py'
$taskStart = New-Object System.Diagnostics.ProcessStartInfo
$taskStart.FileName = $taskPlan.base_python
$taskStart.Arguments = '-B "' + $taskOwner + '" "' + $taskSlot + '"'
$taskStart.WorkingDirectory = $taskSlot
$taskStart.UseShellExecute = $false
$taskStart.CreateNoWindow = $true
$taskStart.RedirectStandardOutput = $true
$taskStart.RedirectStandardError = $true
$taskStart.EnvironmentVariables['PYTHONUTF8'] = '1'
$taskProcess = New-Object System.Diagnostics.Process
$taskProcess.StartInfo = $taskStart
Assert-LegacyObservationStart -Plan $taskPlan -Approval $taskApproval -PlanSha256 $taskPlanSha -ResolvedSlot $taskSlot -NowUtc ([DateTimeOffset]::UtcNow)
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

# 仅等待一个已投递动作的文件证据；不启动进程、不查询桌面、不修改任何控制文件。
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Slot,
    [Parameter(Mandatory=$true)][string]$Task,
    [Parameter(Mandatory=$true)][string]$Dispatch,
    [Parameter(Mandatory=$true)][string]$Session,
    [Parameter(Mandatory=$true)][string]$Previous,
    [Parameter(Mandatory=$true)][string]$Nonce,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9-]+$')][string]$Name,
    [ValidateRange(100,15000)][int]$TimeoutMs=10000,
    [ValidateRange(250,1000)][int]$PollMs=250
)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$watch=[Diagnostics.Stopwatch]::StartNew()
$phase='初始化'
function Finish([string]$Status,[string]$Reason,[int]$Code=0,$State=$null) {
    $result=[ordered]@{status=$Status;reason=$Reason;phase=$phase;elapsed_ms=$watch.ElapsedMilliseconds;name=$Name}
    if ($null -ne $State) { $result.state=$State }
    [Console]::Out.WriteLine(($result | ConvertTo-Json -Depth 40 -Compress))
    exit $Code
}
function AssertPlain([string]$Path) {
    # 逐级拒绝重解析点；不把已退出旧场景或公共目录当作新槽。
    $item=Get-Item -LiteralPath $Path -Force
    while ($null -ne $item) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw '文件等待路径含重解析点' }
        $item=if ($item.PSIsContainer) { $item.Parent } else { $item.Directory }
    }
}
function ReadJson([string]$Path) {
    AssertPlain $Path
    $stream=[IO.FileStream]::new($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
    $reader=[IO.StreamReader]::new($stream,[Text.Encoding]::UTF8,$true)
    try { return ($reader.ReadToEnd() | ConvertFrom-Json) }
    finally { $reader.Dispose(); $stream.Dispose() }
}
function AssertBinding($Value) {
    if ($Value.task -cne $Task -or $Value.dispatch -cne $Dispatch -or $Value.session -cne $Session) {
        throw '文件证据身份不符'
    }
}
try {
    if ($Previous -cnotmatch '^step-([0-9]{3})-[a-z0-9-]+$' -or $Nonce -cnotmatch '^[a-f0-9]{32}$') {
        throw '当前步骤或nonce格式错误'
    }
    $sequence=[int]$Previous.Substring(5,3)+1
    $prefix=('step-{0:d3}-{1}' -f $sequence,$Name)
    $expected=$prefix+'-post'
    $slotPath=[IO.Path]::GetFullPath($Slot).TrimEnd('\','/')
    $analysis=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../.local-analysis')).TrimEnd('\','/')+'\'
    if (-not $slotPath.StartsWith($analysis,[StringComparison]::OrdinalIgnoreCase)) { throw '等待路径不属于本工作树忽略目录' }
    AssertPlain $slotPath
    $queue=Join-Path $slotPath 'submit-queue'
    AssertPlain $queue
    $packetName='packet-'+$Name
    $resultPath=Join-Path $queue ($packetName+'.result')
    $completePath=Join-Path $slotPath ($prefix+'-complete.json')
    $statePath=Join-Path $slotPath 'current-state.json'
    while ($true) {
        foreach ($signal in @('stopped-error.json','stop-business.json','submit-thread-error.json')) {
            if ([IO.File]::Exists((Join-Path $slotPath $signal))) { Finish 'refused' ('本槽已有停止或拒绝证据：'+$signal) 3 }
        }
        $phase='原投递包'
        $packet=$null
        $packetPath=$null
        foreach ($suffix in @('.json','.submitted','.rejected')) {
            $candidate=Join-Path $queue ($packetName+$suffix)
            if ([IO.File]::Exists($candidate)) {
                if ($null -ne $packet -and [IO.File]::Exists($packetPath)) { throw '同名投递包有多个版本，拒绝选择' }
                # owner可能刚把.json改名；只读共享删除句柄，不能阻塞原rename。
                try { $nextPacket=ReadJson $candidate }
                catch [IO.FileNotFoundException] { continue }
                if ($null -ne $packet -and ($packet | ConvertTo-Json -Depth 40 -Compress) -cne ($nextPacket | ConvertTo-Json -Depth 40 -Compress)) {
                    throw '原投递包改名时内容变化'
                }
                $packet=$nextPacket
                $packetPath=$candidate
            }
        }
        if ($null -eq $packet) { throw '没有可核验的原投递包，不创建或重发' }
        AssertBinding $packet
        if ($packet.previous -cne $Previous -or $packet.nonce -cne $Nonce -or $packet.request.name -cne $Name) {
            throw '原投递包不是当前请求'
        }
        $phase='owner结果'
        if ([IO.File]::Exists($resultPath)) {
            $receipt=ReadJson $resultPath
            if ($receipt.packet -cne ($packetName+'.json')) { throw 'owner结果不是当前包' }
            if ($receipt.submitted -ne $true) { Finish 'refused' ('owner拒绝：'+$receipt.error) 3 }
            $phase='原driver完成'
            if ([IO.File]::Exists($completePath)) {
                $complete=ReadJson $completePath
                if ($complete.completed -ne $true) { throw '原driver完成证据无效' }
                $phase='精确新状态'
                $state=ReadJson $statePath
                AssertBinding $state
                if ($state.step -cne $expected -or $state.nonce -ceq $Nonce -or $state.nonce -cnotmatch '^[a-f0-9]{32}$') {
                    throw '完成后仍是旧步骤、旧nonce或非预期状态'
                }
                if (@($state.host).Count -lt 1) { throw '新状态缺少host原图' }
                $frozen=ReadJson (Join-Path $slotPath ($expected+'-observation.json'))
                if (($frozen | ConvertTo-Json -Depth 40 -Compress) -cne ($state | ConvertTo-Json -Depth 40 -Compress)) {
                    throw '新状态与原观测不符'
                }
                Finish 'ready' '同一动作已完成且发布精确新状态' 0 $state
            }
        }
        $remaining=$TimeoutMs-$watch.ElapsedMilliseconds
        if ($remaining -le 0) { Finish 'pending' '有界等待结束；只能续等同一包，不能重发或读取旧图' }
        [Threading.Thread]::Sleep([Math]::Min($PollMs,$remaining))
    }
} catch {
    Finish 'error' $_.Exception.Message 2
}

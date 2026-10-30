param([Parameter(Mandatory=$true)][string]$StepName,[Parameter(Mandatory=$true)][string]$Kind,[Parameter(ValueFromRemainingArguments=$true)][string[]]$StepValues)
$ErrorActionPreference='Stop'
if($StepName -notmatch '^[a-zA-Z0-9_-]+$'){throw '步骤名不合法'}
$liveRoot=$PSScriptRoot
$payloadPath=Join-Path $liveRoot ($StepName+'-driver-args.json')
if(Test-Path $payloadPath){throw '同一步骤已提交，禁止重发'}
$payload=@{name=$StepName;kind=$Kind;values=@($StepValues)}
$payload|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 $payloadPath
$driver=Start-Process -FilePath 'C:/Users/rikideng/scoop/persist/uv/python/versions/cpython-3.14.8-windows-x86_64-none/pythonw.exe' -ArgumentList @((Join-Path $PSScriptRoot 'driver.py'),$payloadPath) -PassThru
$driverWaitMs=if($Kind -eq 'close-owned'){50000}else{45000}
if(-not $driver.WaitForExit($driverWaitMs)){throw '请求仍未结束；不得排队/重发，先只读查状态'}
if($driver.ExitCode -ne 0){throw (Get-Content -Raw -Encoding UTF8 (Join-Path $liveRoot ($StepName+'-driver-error.txt')))}
$result=Get-Content -Raw -Encoding UTF8 (Join-Path $liveRoot ($StepName+'-complete.json'))|ConvertFrom-Json
if(-not $result.completed){throw '步骤未成功，停止当前链'}
$result|ConvertTo-Json -Depth 6

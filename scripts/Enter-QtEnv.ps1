param(
    [string]$QtPrefix = (Join-Path $HOME 'Qt\6.12.0\msvc2022_64')
)

$ErrorActionPreference = 'Stop'

# 只修改当前终端进程，不写入系统环境变量或用户级 PATH。
if (-not (Test-Path (Join-Path $QtPrefix 'lib\cmake\Qt6\Qt6Config.cmake'))) {
    throw "未找到 Qt 6 开发包：$QtPrefix。请通过 -QtPrefix 指定安装目录。"
}

$installerDirectory = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer'
$vswhere = Join-Path $installerDirectory 'vswhere.exe'
if (-not (Test-Path $vswhere)) {
    throw '未找到 Visual Studio 安装查询工具，请先安装 MSVC C++ 桌面开发工具。'
}
$vsPath = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vsPath) {
    throw '未找到包含 MSVC x64/x86 编译器的 Visual Studio 安装。'
}
$developerScript = Join-Path $vsPath 'Common7\Tools\VsDevCmd.bat'

# 将开发者命令行环境导入当前 PowerShell，使 cl、link、CMake、Ninja 可用。
$previousPath = $env:PATH
$env:PATH = "$installerDirectory;$previousPath"
$command = 'call "{0}" -no_logo -arch=x64 -host_arch=x64 >nul && set' -f $developerScript
$environmentLines = & $env:ComSpec /d /c $command
if ($LASTEXITCODE -ne 0) {
    $env:PATH = $previousPath
    throw '初始化 MSVC x64 开发环境失败。'
}
foreach ($line in $environmentLines) {
    if ($line -match '^([^=][^=]*)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}

$env:QTDIR = (Resolve-Path $QtPrefix).Path
$env:PATH = "$(Join-Path $env:QTDIR 'bin');$env:PATH"
if ($env:CMAKE_PREFIX_PATH) {
    $env:CMAKE_PREFIX_PATH = "$env:QTDIR;$env:CMAKE_PREFIX_PATH"
} else {
    $env:CMAKE_PREFIX_PATH = $env:QTDIR
}
Write-Host "已启用 Qt 开发环境：$env:QTDIR"
Write-Host "已启用 MSVC x64 工具集：$env:VCToolsVersion"

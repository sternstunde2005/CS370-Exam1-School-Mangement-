$ErrorActionPreference = 'Stop'
$bundleRoot = Split-Path -Parent $PSScriptRoot
$statePath = Join-Path $bundleRoot 'logs\server.json'
if (-not (Test-Path -LiteralPath $statePath)) { Write-Output 'No recorded server.'; exit 0 }
$state = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
$processInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$($state.process_id)" -ErrorAction SilentlyContinue
if ($processInfo) {
    $expectedPython = Join-Path $bundleRoot 'runtime\python.exe'
    $expectedManage = Join-Path $bundleRoot 'website\manage.py'
    if ($processInfo.ExecutablePath -ne $expectedPython -or -not $processInfo.CommandLine.Contains($expectedManage)) {
        throw 'Recorded PID belongs to a different process; refusing to stop it.'
    }
    Stop-Process -Id $state.process_id
    Write-Output 'StudentHub stopped.'
}
Remove-Item -LiteralPath $statePath

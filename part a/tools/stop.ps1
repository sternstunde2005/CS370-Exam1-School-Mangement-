$ErrorActionPreference = 'Stop'
$bundleRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $bundleRoot 'runtime\python.exe'
$servePath = Join-Path $bundleRoot 'tools\serve.py'
$statePath = Join-Path $bundleRoot 'logs\server.json'

$processId = $null
if (Test-Path -LiteralPath $statePath) {
    try { $processId = (Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json).process_id } catch { $processId = $null }
}
if (-not $processId) {
    $listener = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) { $processId = $listener.OwningProcess }
}

if ($processId) {
    $existing = Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
    $isThisWebsite = $existing -and $existing.ExecutablePath -eq $pythonPath -and $existing.CommandLine -and $existing.CommandLine.Contains($servePath)
    if ($isThisWebsite) {
        Stop-Process -Id $processId -Force
        Write-Output "Stopped School Management website (PID $processId)."
    } elseif ($existing) {
        throw "PID $processId does not belong to this package; it was not stopped."
    }
} else {
    Write-Output 'Website is not running.'
}

Remove-Item -LiteralPath $statePath -Force -ErrorAction SilentlyContinue

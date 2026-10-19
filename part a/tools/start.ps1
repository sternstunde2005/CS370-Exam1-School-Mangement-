param([switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$bundleRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $bundleRoot 'runtime\python.exe'
$servePath = Join-Path $bundleRoot 'tools\serve.py'
$logsPath = Join-Path $bundleRoot 'logs'
$statePath = Join-Path $logsPath 'server.json'
$url = 'http://127.0.0.1:5000/'

try {
    New-Item -ItemType Directory -Path $logsPath -Force | Out-Null
    $listener = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        $existing = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction SilentlyContinue
        $isThisWebsite = $existing -and $existing.ExecutablePath -eq $pythonPath -and $existing.CommandLine -and $existing.CommandLine.Contains($servePath)
        if (-not $isThisWebsite) {
            throw 'Port 5000 is already used by another program. Close it or follow the manual-port instructions in README.md.'
        }
        if (-not $NoBrowser) { Start-Process $url }
        Write-Output "Already running: $url"
        exit 0
    }

    $env:PYTHONUTF8 = '1'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $serverArgs = '"' + $servePath + '"'
    $process = Start-Process -FilePath $pythonPath -ArgumentList $serverArgs -WorkingDirectory $bundleRoot -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logsPath 'server.stdout.log') `
        -RedirectStandardError (Join-Path $logsPath 'server.stderr.log') -PassThru
    @{ process_id = $process.Id; python = $pythonPath; script = $servePath; url = $url } |
        ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8

    $ready = $false
    for ($attempt = 0; $attempt -lt 50; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch {
            Start-Sleep -Milliseconds 300
        }
        $process.Refresh()
        if ($process.HasExited) { break }
    }
    if (-not $ready) { throw 'Website did not start. See logs\server.stderr.log.' }

    Write-Output "Running: $url (PID $($process.Id))"
    if (-not $NoBrowser) { Start-Process $url }
} catch {
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $logsPath 'startup-error.log') -Encoding UTF8
    if (-not $NoBrowser) {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'School Management startup') | Out-Null
    }
    Write-Error $_
    exit 1
}

param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$bundleRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $bundleRoot 'runtime\python.exe'
$managePath = Join-Path $bundleRoot 'website\manage.py'
$statePath = Join-Path $bundleRoot 'logs\server.json'
$url = 'http://127.0.0.1:8000/'
try {
    $listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        $existing = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
        if ($existing.ExecutablePath -ne $pythonPath -or -not $existing.CommandLine.Contains($managePath)) {
            throw 'Port 8000 is used by another program. Close that program or use the manual start instructions.'
        }
        if (-not $NoBrowser) { Start-Process $url }
        Write-Output "Already running: $url"
        exit 0
    }
    $env:PYTHONUTF8 = '1'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:DJANGO_DEBUG = 'True'
    $env:DJANGO_ALLOWED_HOSTS = '127.0.0.1,localhost'
    if (-not (Test-Path -LiteralPath (Join-Path $bundleRoot 'website\db.sqlite3'))) {
        & $pythonPath $managePath migrate --noinput
        if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
        & $pythonPath $managePath seed_part_a
        if ($LASTEXITCODE -ne 0) { throw 'Demo data initialization failed.' }
    }
    $serverArgs = '"' + $managePath + '" runserver 127.0.0.1:8000 --noreload'
    $proc = Start-Process -FilePath $pythonPath -ArgumentList $serverArgs -WorkingDirectory (Join-Path $bundleRoot 'website') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $bundleRoot 'logs\server.stdout.log') -RedirectStandardError (Join-Path $bundleRoot 'logs\server.stderr.log') -PassThru
    @{ process_id=$proc.Id; python=$pythonPath; manage=$managePath; url=$url } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
    $ready = $false
    for ($attempt=0; $attempt -lt 50; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) { $ready=$true; break }
        } catch { Start-Sleep -Milliseconds 300 }
        $proc.Refresh()
        if ($proc.HasExited) { break }
    }
    if (-not $ready) { throw 'Server did not start. See logs\server.stderr.log.' }
    Write-Output "Running: $url (PID $($proc.Id))"
    if (-not $NoBrowser) { Start-Process $url }
} catch {
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $bundleRoot 'logs\startup-error.log') -Encoding UTF8
    if (-not $NoBrowser) {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'StudentHub startup') | Out-Null
    }
    Write-Error $_
    exit 1
}

[CmdletBinding()]
param(
  [string]$ProxyPath = '',
  [string]$PythonPath = ''
)

$ErrorActionPreference = 'SilentlyContinue'

if (-not $ProxyPath) {
  $ProxyPath = Join-Path $PSScriptRoot 'opus5_proxy.py'
}

if (-not $PythonPath) {
  $pw = Get-Command pythonw -ErrorAction SilentlyContinue
  if ($pw -and $pw.Source) {
    $PythonPath = $pw.Source
  } else {
    $p = Get-Command python -ErrorAction SilentlyContinue
    if ($p -and $p.Source) {
      $candidate = Join-Path (Split-Path $p.Source -Parent) 'pythonw.exe'
      if (Test-Path -LiteralPath $candidate) { $PythonPath = $candidate }
    }
  }
}

$runtimeDir = Split-Path -Parent $ProxyPath
if (-not $runtimeDir) { $runtimeDir = $PSScriptRoot }
$watchdogLog = Join-Path $runtimeDir 'watchdog.log'

$mutex = New-Object System.Threading.Mutex($false, 'Local\PGPTProxy-Supervisor')
$hasLock = $false
try { $hasLock = $mutex.WaitOne(0, $false) } catch { exit 1 }
if (-not $hasLock) { exit 0 }

try {
  while ($true) {
    try {
      $running = @(Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' or Name='python.exe'" -ErrorAction SilentlyContinue |
                   Where-Object { $_.CommandLine -like '*opus5_proxy.py*' })
      if ($running.Count -eq 0 -and (Test-Path -LiteralPath $ProxyPath) -and (Test-Path -LiteralPath $PythonPath)) {
        Start-Process -FilePath $PythonPath -ArgumentList ('"' + $ProxyPath + '"') -WindowStyle Hidden | Out-Null
        Add-Content -LiteralPath $watchdogLog -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' supervisor started proxy')
      }
    } catch {
      Add-Content -LiteralPath $watchdogLog -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' supervisor error: ' + $_.Exception.Message)
    }
    Start-Sleep -Seconds 5
  }
} finally {
  if ($hasLock) { try { $mutex.ReleaseMutex() } catch {} }
  $mutex.Dispose()
}

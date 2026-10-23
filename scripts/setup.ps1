$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $projectRoot '.venv'
$pythonExe = Join-Path $venvPath 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    & py -3.12 -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { throw 'Creating the Python 3.12 environment failed.' }
}
& $pythonExe -m pip install --no-cache-dir -r (Join-Path $projectRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
Push-Location $projectRoot
try {
    & $pythonExe -m research doctor
    if ($LASTEXITCODE -ne 0) { throw 'Environment check failed. See the diagnostic above.' }
} finally {
    Pop-Location
}

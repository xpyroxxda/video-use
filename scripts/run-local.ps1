[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true, Mandatory = $true)]
    [string[]]$HelperArgs
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw 'Local environment missing. Run scripts/setup-windows.ps1 first.'
}

if (-not $env:VIDEO_USE_MODEL) { $env:VIDEO_USE_MODEL = 'large-v3-turbo' }
if (-not $env:VIDEO_USE_DEVICE) { $env:VIDEO_USE_DEVICE = 'cuda' }
if (-not $env:VIDEO_USE_COMPUTE_TYPE) { $env:VIDEO_USE_COMPUTE_TYPE = 'float16' }
if (-not $env:VIDEO_USE_ENCODER) { $env:VIDEO_USE_ENCODER = 'h264_nvenc' }
$env:PYTHONUTF8 = '1'

Push-Location $repoRoot
try {
    & $venvPython @HelperArgs
    exit $LASTEXITCODE
} finally {
    Pop-Location
}

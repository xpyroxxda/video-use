[CmdletBinding()]
param(
    [switch]$SkipModelDownload
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'

Push-Location $repoRoot
try {
    if (-not (Test-Path -LiteralPath $venvPython)) {
        if (Get-Command py -ErrorAction SilentlyContinue) {
            & py -3.12 -m venv .venv
        } elseif (Get-Command python -ErrorAction SilentlyContinue) {
            & python -m venv .venv
        } else {
            throw 'Python 3.10 or newer is required. Install it from python.org, then rerun this script.'
        }
    }

    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -e '.[dev]'

    foreach ($tool in 'ffmpeg', 'ffprobe', 'nvidia-smi') {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
            throw "$tool was not found on PATH. Install it, reopen PowerShell, then rerun this script."
        }
    }

    $encoders = & cmd.exe /d /c "ffmpeg -encoders 2>&1"
    if (($encoders -join "`n") -notmatch 'h264_nvenc') {
        throw 'FFmpeg does not expose h264_nvenc. Update the NVIDIA driver or install an FFmpeg build with NVENC enabled.'
    }

    Write-Host 'Local setup is ready.'
    Write-Host 'The selected open Whisper model downloads on the first transcription only.'
    Write-Host 'No paid transcription key is required.'
    if ($SkipModelDownload) {
        Write-Host 'Model download was intentionally deferred.'
    }
} finally {
    Pop-Location
}

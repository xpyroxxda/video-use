[CmdletBinding()]
param(
    [switch]$SkipNvencEncode
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw 'Local environment missing. Run scripts/setup-windows.ps1 first.'
}

& $venvPython -c "import faster_whisper; print('faster-whisper import: OK')"
& nvidia-smi --query-gpu=name,driver_version --format=csv,noheader

$encoders = & ffmpeg -encoders 2>&1
if ($encoders -notmatch 'h264_nvenc') {
    throw 'h264_nvenc is not available in this FFmpeg build.'
}
Write-Host 'FFmpeg h264_nvenc: available'

if (-not $SkipNvencEncode) {
    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("video-use-nvenc-check-" + [guid]::NewGuid())
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    $output = Join-Path $tempDir 'nvenc-check.mp4'
    try {
        & ffmpeg -y -f lavfi -i 'testsrc2=size=320x180:rate=30' -t 1 -c:v h264_nvenc -preset p5 -cq 28 -b:v 0 -an $output
        if (-not (Test-Path -LiteralPath $output)) { throw 'NVENC test produced no output file.' }
        Write-Host 'NVENC encode: OK'
    } finally {
        Remove-Item -LiteralPath $tempDir -Recurse -Force
    }
}

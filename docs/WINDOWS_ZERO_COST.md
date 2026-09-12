# Windows + RTX 4080: local, zero-cost workflow

This fork processes media on this PC. It uses `faster-whisper` for transcription and FFmpeg `h264_nvenc` for video encoding. Normal editing needs no paid API key, account, cloud render, or hosted storage.

## First-time setup

Open PowerShell in the repository and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1
powershell -ExecutionPolicy Bypass -File scripts/verify-local.ps1
```

The first real transcription downloads the selected public Whisper model once into the local model cache. That needs internet only for the download; later media processing stays on the PC. The tool has no recurring API fee, although local electricity and disk space are still used.

## CUDA transcription prerequisite

NVENC video encoding and CUDA Whisper inference are separate NVIDIA components. This PC needs the CUDA 12 `cuBLAS` and cuDNN 9 runtime DLLs for `faster-whisper` inference. This installation keeps them under `.local\cuda12`; `run-local.ps1` prepends that directory to PATH only for the local project process. If transcription reports a missing `cublas64_12.dll`, restore those CUDA 12/cuDNN 9 runtime libraries there and rerun the smoke test. `faster-whisper` documents these as its GPU requirements; the CPU fallback below remains usable without them.

## Normal workflow

Keep source footage in its own folder. Outputs remain beside it in `edit\`.

```powershell
cd C:\path\to\footage
C:\Users\xpyro\Documents\video-use-local\scripts\run-local.ps1 C:\Users\xpyro\Documents\video-use-local\helpers\transcribe_batch.py .
C:\Users\xpyro\Documents\video-use-local\scripts\run-local.ps1 C:\Users\xpyro\Documents\video-use-local\helpers\pack_transcripts.py --edit-dir .\edit
```

Then use your coding agent in the footage directory, read `takes_packed.md`, confirm an editing strategy, create the EDL, and render it:

```powershell
C:\Users\xpyro\Documents\video-use-local\scripts\run-local.ps1 C:\Users\xpyro\Documents\video-use-local\helpers\render.py .\edit\edl.json -o .\edit\final.mp4 --build-subtitles
```

## Local defaults

- Transcription: `large-v3-turbo`, `cuda`, `float16`.
- Render: `h264_nvenc` with NVENC constant-quality settings.
- Batch GPU workers: one by default, to prevent multiple model copies exhausting VRAM.

Override an environment variable only for the current PowerShell session:

```powershell
$env:VIDEO_USE_ENCODER = 'libx264'       # no NVIDIA encoder available
$env:VIDEO_USE_DEVICE = 'cpu'             # CUDA unavailable
$env:VIDEO_USE_COMPUTE_TYPE = 'int8'      # lower memory CPU mode
```

For NVENC problems, run `scripts/verify-local.ps1`. It reports whether FFmpeg exposes `h264_nvenc` and creates a disposable one-second GPU test clip. Update the NVIDIA driver or install an FFmpeg build with NVENC enabled if that check fails.

## Privacy and limitations

The original hosted Scribe provider included speaker diarization and audio-event tags. This zero-cost local default preserves word timestamps but uses `speaker_0` for all words; it does not claim speaker diarization. A later local WhisperX extension can add alignment/diarization without changing the transcript consumer format.

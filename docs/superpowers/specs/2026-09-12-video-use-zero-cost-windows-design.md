# Video Use: Zero-Cost Windows Standalone Design

## Goal

Create a standalone copy of browser-use/video-use under the user's Documents folder. Preserve the agent-directed editor workflow while eliminating recurring transcription/API cost on Windows with an RTX 4080. Do not integrate any other app, database, or Supabase project.

## Selected Architecture

Use faster-whisper as the default local transcription engine with CUDA and float16. It downloads an open model into the local cache once, needs no account or paid key, and provides word timestamps needed by the existing packing and editing workflow. The default model is large-v3-turbo. Keep a clean adapter boundary for a future WhisperX alignment/diarization option.

Use FFmpeg h264_nvenc for final GPU encodes and keep libx264 as a documented software fallback. The editor remains a folder of CLI helpers and an agent skill; no web UI, server, cloud rendering, hosted storage, or third-party application integration is part of this work.

## Runtime Flow

1. User invokes the standalone workflow in a folder containing footage.
2. FFmpeg extracts local audio and faster-whisper runs it on CUDA.
3. The adapter writes native-compatible word-level JSON under edit/transcripts.
4. Existing packing, EDL, subtitles, QC, and output-folder conventions continue unchanged.
5. FFmpeg renders with h264_nvenc. The user can explicitly select CPU/libx264 fallback.

## Defaults and Fallbacks

- Default model: large-v3-turbo.
- Default device and compute type: cuda and float16.
- Default encoder: h264_nvenc.
- Config variables: VIDEO_USE_MODEL, VIDEO_USE_DEVICE, VIDEO_USE_COMPUTE_TYPE, VIDEO_USE_ENCODER.
- Fallbacks: device=cpu, compute_type=int8, encoder=libx264.
- Setup must diagnose missing FFmpeg, NVIDIA driver, CUDA support, or NVENC with clear next steps.
- No default code path reads or requires an ElevenLabs key.

## Windows Deliverables

- PowerShell setup script for .venv, local packages, FFmpeg, GPU and NVENC checks.
- Run script that keeps local defaults and calls existing helpers.
- Verification script that checks Python imports, command interfaces, h264_nvenc, and a disposable local encode.
- Windows guide with commands, first-model download behavior, local-only privacy/cost details, fallbacks, and troubleshooting.

## Verification

Tests are written before implementation for runtime configuration, transcript schema conversion, render encoder selection, and script documentation/safety. Final verification includes existing tests, all new tests, helper --help, FFmpeg NVENC detection and local encode, and an optional faster-whisper smoke transcription using only the public model.

The tool has no recurring paid API fee. External coding agents selected separately, electrical power, storage, and the initial public model download are outside that statement.

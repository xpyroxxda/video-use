# Zero-Cost Windows CUDA Video Use Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run this fork as a standalone Windows video editor using local CUDA transcription and RTX 4080 NVENC rendering, with no paid transcription service.

**Architecture:** The existing Scribe HTTP helper becomes a faster-whisper adapter that emits the same word-level JSON consumed by `pack_transcripts.py`. A narrow runtime module supplies CUDA/NVENC defaults and CPU/libx264 fallbacks. PowerShell scripts create and verify a local virtual environment without registering other apps.

**Tech Stack:** Python 3.10+, faster-whisper/CTranslate2 CUDA, FFmpeg, NVENC, PowerShell, pytest.

**Spec:** `docs/superpowers/specs/2026-09-12-video-use-zero-cost-windows-design.md`

## Global Constraints

- Project: `C:\Users\xpyro\Documents\video-use-local` only; no app, database, or Supabase integration.
- Normal transcription uses no paid API or credential.
- Defaults: `large-v3-turbo`, `cuda`, `float16`, and `h264_nvenc`.
- Keep CPU / `int8` / `libx264` fallbacks.
- User outputs remain in `<videos_dir>\edit\`.
- Network use is limited to clone, installation, and one public-model download.

---

### Task 1: Local runtime configuration

**Files:**
- Create: `helpers/local_runtime.py`
- Create: `tests/test_local_runtime.py`
- Modify: `pyproject.toml` and `.env.example`

**Interfaces:**
- `LocalRuntime(model: str, device: str, compute_type: str, encoder: str)`
- `load_runtime(env: Mapping[str, str] | None = None) -> LocalRuntime`
- `video_encoder_args(runtime: LocalRuntime, quality: str) -> list[str]`

- [ ] **Step 1: Write the failing test**

```python
from helpers.local_runtime import load_runtime, video_encoder_args

def test_defaults_target_cuda_and_nvenc():
    actual = load_runtime({})
    assert (actual.model, actual.device, actual.compute_type, actual.encoder) == (
        "large-v3-turbo", "cuda", "float16", "h264_nvenc"
    )

def test_cpu_override_uses_software_encoder():
    runtime = load_runtime({"VIDEO_USE_ENCODER": "libx264"})
    assert video_encoder_args(runtime, "final") == [
        "-c:v", "libx264", "-preset", "fast", "-crf", "20"
    ]
```

- [ ] **Step 2: Verify red**

Run: `python -m pytest tests/test_local_runtime.py -v`

Expected: FAIL because `helpers.local_runtime` does not exist.

- [ ] **Step 3: Implement the narrow configuration module**

Use a frozen `LocalRuntime` dataclass. Resolve defaults from `VIDEO_USE_MODEL`, `VIDEO_USE_DEVICE`, `VIDEO_USE_COMPUTE_TYPE`, and `VIDEO_USE_ENCODER`. Return `["-c:v", "h264_nvenc", "-preset", "p5", "-cq", quality, "-b:v", "0"]` for NVENC and retain existing x264 preset/CRF values for the fallback.

Add `faster-whisper` to production dependencies and `pytest` as a `dev` optional dependency. Replace the key example with non-secret `VIDEO_USE_*` defaults.

- [ ] **Step 4: Verify green and commit**

Run: `python -m pytest tests/test_local_runtime.py -v`

Run: `git add helpers/local_runtime.py tests/test_local_runtime.py pyproject.toml .env.example; git commit -m "feat: add local CUDA runtime configuration"`

Expected: tests pass.

### Task 2: Local faster-whisper transcript adapter

**Files:**
- Modify: `helpers/transcribe.py` and `helpers/transcribe_batch.py`
- Create: `tests/test_local_transcript.py`

**Interfaces:**
- `to_transcript_payload(info, segments) -> dict`
- `transcribe_audio_locally(audio_path: Path, runtime: LocalRuntime, language: str | None) -> dict`
- `transcribe_one(..., runtime: LocalRuntime, ...) -> Path`

- [ ] **Step 1: Write the failing schema test**

```python
from types import SimpleNamespace
from helpers.transcribe import to_transcript_payload

def test_local_words_work_with_packed_transcripts():
    segment = SimpleNamespace(words=[
        SimpleNamespace(word=" hello", start=0.0, end=0.3),
        SimpleNamespace(word=" world", start=0.4, end=0.8),
    ])
    payload = to_transcript_payload(SimpleNamespace(language="en"), [segment])
    assert payload["text"] == "hello world"
    assert payload["words"] == [
        {"text": "hello", "start": 0.0, "end": 0.3, "type": "word", "speaker_id": "speaker_0"},
        {"text": "world", "start": 0.4, "end": 0.8, "type": "word", "speaker_id": "speaker_0"},
    ]
```

- [ ] **Step 2: Verify red**

Run: `python -m pytest tests/test_local_transcript.py -v`

Expected: FAIL because `to_transcript_payload` does not exist.

- [ ] **Step 3: Implement local inference**

Remove `requests`, Scribe URL, API-key reading, and upload calls. Lazy-import `WhisperModel` so help commands never initialize CUDA. Call:

```python
model = WhisperModel(runtime.model, device=runtime.device, compute_type=runtime.compute_type)
segments, info = model.transcribe(str(audio_path), word_timestamps=True,
                                 language=language, vad_filter=True)
```

Materialize segments once. Each non-empty `word.word.strip()` maps to `text`, rounded `start` / `end`, `type: "word"` and `speaker_id: "speaker_0"`. Include top-level `text`, `language_code`, and `provider: "faster-whisper"`. Keep current WAV extraction, silence detection, cache, source validation, and output paths. Batch mode loads `load_runtime()`, defaults to one worker, and warns for CUDA with more than one worker.

- [ ] **Step 4: Verify green and commit**

Run: `python -m pytest tests/test_local_transcript.py tests/test_local_runtime.py -v`

Run: `git add helpers/transcribe.py helpers/transcribe_batch.py tests/test_local_transcript.py; git commit -m "feat: replace Scribe with local faster-whisper"`

Expected: no code path asks for an API key.

### Task 3: NVENC default in every render pass

**Files:**
- Modify: `helpers/render.py`
- Create: `tests/test_render_encoder.py`

**Interfaces:**
- `encoder_args_for_render(runtime, preview: bool, draft: bool) -> list[str]`
- One runtime flows from `main()` to `extract_all_segments`, `extract_segment`, and `build_final_composite`.

- [ ] **Step 1: Write the failing test**

```python
from helpers.local_runtime import load_runtime
from helpers.render import encoder_args_for_render

def test_final_defaults_to_nvenc():
    assert encoder_args_for_render(load_runtime({}), False, False) == [
        "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "20", "-b:v", "0"
    ]

def test_draft_x264_keeps_existing_profile():
    runtime = load_runtime({"VIDEO_USE_ENCODER": "libx264"})
    assert encoder_args_for_render(runtime, False, True) == [
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28"
    ]
```

- [ ] **Step 2: Verify red**

Run: `python -m pytest tests/test_render_encoder.py -v`

Expected: FAIL because `encoder_args_for_render` does not exist.

- [ ] **Step 3: Implement encoder selection**

Use:

```python
def encoder_args_for_render(runtime, preview, draft):
    quality = "draft" if draft else ("preview" if preview else "final")
    return video_encoder_args(runtime, quality)
```

Replace hard-coded x264 fragments in both `extract_segment` and `build_final_composite`. Preserve audio settings, yuv420p, concatenation, subtitle-last ordering, and loudnorm. Document `VIDEO_USE_ENCODER=libx264`.

- [ ] **Step 4: Verify green and commit**

Run: `python -m pytest tests/test_render_encoder.py tests/test_render_fps.py tests/test_render_orientation.py -v`

Run: `git add helpers/render.py tests/test_render_encoder.py; git commit -m "feat: use NVENC by default for local renders"`

Expected: new and existing render tests pass.

### Task 4: Windows setup, run, and verification

**Files:**
- Create: `scripts/setup-windows.ps1`, `scripts/run-local.ps1`, `scripts/verify-local.ps1`
- Create: `tests/test_windows_scripts.py`

**Interfaces:**
- `setup-windows.ps1 [-SkipModelDownload]` creates `.venv`, installs `.[dev]`, validates requirements.
- `run-local.ps1 <arguments>` uses `.venv\Scripts\python.exe` and only supplies absent `VIDEO_USE_*` defaults.
- `verify-local.ps1 [-SkipNvencEncode]` reports local requirements and tests NVENC on generated media.

- [ ] **Step 1: Write failing script tests**

```python
from pathlib import Path

def test_setup_has_no_paid_api_requirement():
    script = Path("scripts/setup-windows.ps1").read_text(encoding="utf-8")
    assert "ELEVENLABS" not in script
    assert "API_KEY" not in script

def test_verify_checks_nvenc():
    script = Path("scripts/verify-local.ps1").read_text(encoding="utf-8")
    assert "ffmpeg -encoders" in script
    assert "h264_nvenc" in script
```

- [ ] **Step 2: Verify red**

Run: `python -m pytest tests/test_windows_scripts.py -v`

Expected: FAIL because scripts do not exist.

- [ ] **Step 3: Implement scripts**

Setup locates the root from `$PSScriptRoot`, creates a virtual environment with `py -3.11 -m venv` then `python -m venv` fallback, installs `.[dev]`, and checks `ffmpeg`, `ffprobe`, `nvidia-smi`, and `ffmpeg -hide_banner -encoders` for `h264_nvenc`. It never asks for a secret.

Run checks the virtual environment, sets missing local defaults, and forwards arguments to its Python executable.

Verify imports `faster_whisper`, displays driver state, lists NVENC, and—unless skipped—uses `lavfi testsrc2` to produce one-second NVENC output under a known temporary directory which it alone deletes.

- [ ] **Step 4: Verify green and commit**

Run: `python -m pytest tests/test_windows_scripts.py -v`

Run: `git add scripts tests/test_windows_scripts.py; git commit -m "feat: add Windows local setup scripts"`

Expected: scripts pass static tests.

### Task 5: Documentation

**Files:**
- Create: `docs/WINDOWS_ZERO_COST.md`
- Modify: `README.md`, `install.md`, `SKILL.md`, `tests/test_windows_scripts.py`

- [ ] **Step 1: Write failing guide test**

```python
def test_windows_guide_uses_local_stack():
    guide = Path("docs/WINDOWS_ZERO_COST.md").read_text(encoding="utf-8")
    assert "faster-whisper" in guide
    assert "h264_nvenc" in guide
    assert "ELEVENLABS_API_KEY" not in guide
```

- [ ] **Step 2: Verify red**

Run: `python -m pytest tests/test_windows_scripts.py::test_windows_guide_uses_local_stack -v`

Expected: FAIL because guide does not exist.

- [ ] **Step 3: Implement documentation**

Document exact setup, verify, transcription, batch, and render commands; state that the model downloads once and the video tool has no paid API cost (electricity/disk are local resources). Document CPU/int8/x264 fallback. Replace operational requirements for Scribe upload, credits, and `ELEVENLABS_API_KEY` in the existing docs while preserving strategy confirmation, output-directory contract, caching, and the agent workflow.

- [ ] **Step 4: Verify green and commit**

Run: `python -m pytest tests/test_windows_scripts.py -v`

Run: `git add docs/WINDOWS_ZERO_COST.md README.md install.md SKILL.md tests/test_windows_scripts.py; git commit -m "docs: document Windows zero-cost workflow"`

Expected: guide test passes, with no paid API setup left.

### Task 6: Fresh local verification and push

**Files:**
- Modify only when a check shows a tested defect.

- [ ] **Step 1: Build environment and run all tests**

Run: `powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -SkipModelDownload`

Run: `.\.venv\Scripts\python.exe -m pytest -v`

Expected: every original and new test passes.

- [ ] **Step 2: Exercise commands**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify-local.ps1`

Run: `.\scripts\run-local.ps1 helpers\transcribe.py --help`

Run: `.\scripts\run-local.ps1 helpers\render.py --help`

Expected: help commands return zero; verification reports FFmpeg, local provider, and NVENC.

- [ ] **Step 3: Local transcript smoke test**

Generate a short sine WAV with FFmpeg; transcribe it using the local helper, then pack its transcript. Allow only public-model download; never call hosted APIs.

- [ ] **Step 4: Inspect and push**

Run: `git diff upstream/main...HEAD --check`

Run: `git status --short`

Run: `git push -u origin main`

Expected: no whitespace errors and tested commits published to `https://github.com/xpyroxxda/video-use`.

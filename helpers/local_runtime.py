"""Resolve local-only CUDA transcription and FFmpeg encoder settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class LocalRuntime:
    model: str
    device: str
    compute_type: str
    encoder: str


def load_runtime(env: Mapping[str, str] | None = None) -> LocalRuntime:
    """Read local settings, preferring RTX 4080-friendly defaults."""
    values = os.environ if env is None else env
    return LocalRuntime(
        model=values.get("VIDEO_USE_MODEL", "large-v3-turbo"),
        device=values.get("VIDEO_USE_DEVICE", "cuda"),
        compute_type=values.get("VIDEO_USE_COMPUTE_TYPE", "float16"),
        encoder=values.get("VIDEO_USE_ENCODER", "h264_nvenc"),
    )


def video_encoder_args(runtime: LocalRuntime, quality: str) -> list[str]:
    """Return FFmpeg video encoder arguments for final, preview, or draft."""
    try:
        value = {"final": "20", "preview": "22", "draft": "28"}[quality]
    except KeyError as exc:
        raise ValueError(f"unknown render quality: {quality}") from exc

    if runtime.encoder == "h264_nvenc":
        return ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", value, "-b:v", "0"]

    preset = {"final": "fast", "preview": "medium", "draft": "ultrafast"}[quality]
    return ["-c:v", "libx264", "-preset", preset, "-crf", value]

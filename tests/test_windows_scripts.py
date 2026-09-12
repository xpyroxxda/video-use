from pathlib import Path


def test_setup_has_no_paid_api_requirement():
    script = Path("scripts/setup-windows.ps1").read_text(encoding="utf-8")

    assert "ELEVENLABS" not in script
    assert "API_KEY" not in script


def test_verify_checks_nvenc():
    script = Path("scripts/verify-local.ps1").read_text(encoding="utf-8")

    assert "ffmpeg -encoders" in script
    assert "h264_nvenc" in script

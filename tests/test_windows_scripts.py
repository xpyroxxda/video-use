from pathlib import Path


def test_setup_has_no_paid_api_requirement():
    script = Path("scripts/setup-windows.ps1").read_text(encoding="utf-8")

    assert "ELEVENLABS" not in script
    assert "API_KEY" not in script


def test_runner_forces_utf8_for_windows_console_output():
    script = Path("scripts/run-local.ps1").read_text(encoding="utf-8")

    assert "$env:PYTHONUTF8 = '1'" in script


def test_verify_checks_nvenc():
    script = Path("scripts/verify-local.ps1").read_text(encoding="utf-8")

    assert "ffmpeg -encoders" in script
    assert "h264_nvenc" in script


def test_encoder_listing_uses_windows_native_stderr_suppression():
    for path in ("scripts/setup-windows.ps1", "scripts/verify-local.ps1"):
        script = Path(path).read_text(encoding="utf-8")
        assert 'cmd.exe /d /c "ffmpeg -encoders 2>&1"' in script
        assert '($encoders -join "`n") -notmatch' in script


def test_windows_guide_uses_local_stack():
    guide = Path("docs/WINDOWS_ZERO_COST.md").read_text(encoding="utf-8")

    assert "faster-whisper" in guide
    assert "h264_nvenc" in guide
    assert "ELEVENLABS_API_KEY" not in guide

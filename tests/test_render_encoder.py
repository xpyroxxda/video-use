from helpers.local_runtime import load_runtime
from helpers.render import encoder_args_for_render


def test_final_defaults_to_nvenc():
    assert encoder_args_for_render(load_runtime({}), preview=False, draft=False) == [
        "-c:v",
        "h264_nvenc",
        "-preset",
        "p5",
        "-cq",
        "20",
        "-b:v",
        "0",
    ]


def test_draft_x264_keeps_existing_profile():
    runtime = load_runtime({"VIDEO_USE_ENCODER": "libx264"})

    assert encoder_args_for_render(runtime, preview=False, draft=True) == [
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "28",
    ]

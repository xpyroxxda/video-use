from helpers.local_runtime import load_runtime, video_encoder_args


def test_defaults_target_cuda_and_nvenc():
    runtime = load_runtime({})

    assert (runtime.model, runtime.device, runtime.compute_type, runtime.encoder) == (
        "large-v3-turbo",
        "cuda",
        "float16",
        "h264_nvenc",
    )


def test_cpu_override_uses_software_encoder():
    runtime = load_runtime({"VIDEO_USE_ENCODER": "libx264"})

    assert video_encoder_args(runtime, "final") == [
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "20",
    ]


def test_nvenc_final_uses_constant_quality():
    assert video_encoder_args(load_runtime({}), "final") == [
        "-c:v",
        "h264_nvenc",
        "-preset",
        "p5",
        "-cq",
        "20",
        "-b:v",
        "0",
    ]

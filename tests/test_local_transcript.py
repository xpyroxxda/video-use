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
        {
            "text": "hello",
            "start": 0.0,
            "end": 0.3,
            "type": "word",
            "speaker_id": "speaker_0",
        },
        {
            "text": "world",
            "start": 0.4,
            "end": 0.8,
            "type": "word",
            "speaker_id": "speaker_0",
        },
    ]
    assert payload["language_code"] == "en"
    assert payload["provider"] == "faster-whisper"

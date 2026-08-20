from pathlib import Path

from fastapi.testclient import TestClient

from app.main import TranscriptionResult, app


client = TestClient(app)


def test_upload_uses_transcription_provider(monkeypatch) -> None:
    class FakeProvider:
        def transcribe(self, audio_path: Path) -> TranscriptionResult:
            return TranscriptionResult(
                text="provider transcription", language_code="uz"
            )

    monkeypatch.setattr("app.main.get_transcription_provider", lambda: FakeProvider())

    response = client.post(
        "/api/v1/documents",
        files={"file": ("sample-lecture.mp3", b"fake-audio-bytes", "audio/mpeg")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["raw_text"] == "provider transcription"
    assert payload["language_code"] == "uz"


def test_local_whisper_uses_uzbek_language_hint(monkeypatch) -> None:
    captured = {}

    class FakeModel:
        def transcribe(self, path, **kwargs):
            captured["path"] = path
            captured["kwargs"] = kwargs
            return {"text": "uzbek transcription", "language": "uz"}

    class FakeWhisperModule:
        @staticmethod
        def load_model(model_size):
            captured["model_size"] = model_size
            return FakeModel()

    monkeypatch.setattr(
        "whisper.load_model", FakeWhisperModule.load_model, raising=False
    )
    monkeypatch.setenv("WHISPER_LANGUAGE", "uz")
    monkeypatch.setenv("WHISPER_MODEL_SIZE", "tiny")

    from app.main import LocalWhisperProvider

    provider = LocalWhisperProvider(model_size="tiny")
    result = provider.transcribe(Path("/tmp/sample.mp3"))

    assert captured["model_size"] == "tiny"
    assert captured["kwargs"]["language"] == "uz"
    assert result.text == "uzbek transcription"
    assert result.language_code == "uz"


def test_create_document_and_list_documents() -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("sample-lecture.mp3", b"fake-audio-bytes", "audio/mpeg")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["original_filename"] == "sample-lecture.mp3"
    assert payload["status"] == "transcribed"
    assert payload["raw_text"]
    assert payload["language_code"] == "uz"

    list_response = client.get("/api/v1/documents")
    assert list_response.status_code == 200, list_response.text
    items = list_response.json()
    assert any(item["id"] == payload["id"] for item in items)


def test_reject_invalid_file_type() -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("notes.txt", b"this is not audio", "text/plain")},
    )

    assert response.status_code == 400
    assert "audio" in response.json()["detail"].lower()

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/mp3-book-uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".webm", ".mp4"}
ALLOWED_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/m4a",
    "audio/mp4",
    "audio/ogg",
    "audio/webm",
    "video/mp4",
}

app = FastAPI(
    title="MP3 into a Book API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class TranscriptionResult:
    text: str
    language_code: str = "uz"


class TranscriptionProvider(Protocol):
    def transcribe(self, audio_path: Path) -> TranscriptionResult: ...


class LocalWhisperProvider:
    def __init__(self, model_size: str = "tiny") -> None:
        import whisper

        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        language = (os.getenv("WHISPER_LANGUAGE") or "uz").strip().lower() or "uz"
        result = self.model.transcribe(
            str(audio_path),
            fp16=False,
            language=language,
            task="transcribe",
            temperature=0.0,
        )
        text = (result.get("text") or "").strip()
        detected_language = (result.get("language") or language).strip() or language
        if not text:
            text = "Transcription failed to produce text."
        return TranscriptionResult(text=text, language_code=detected_language)


class OpenAITranscriptionProvider:
    def __init__(self, model: str | None = None) -> None:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI transcription.")

        self.client = OpenAI(api_key=api_key)
        self.model = model or os.getenv(
            "OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-transcribe"
        )

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        with audio_path.open("rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
            )

        text = getattr(response, "text", "") or ""
        if not text.strip():
            text = "Transcription failed to produce text."
        return TranscriptionResult(text=text.strip(), language_code="uz")


def get_transcription_provider() -> TranscriptionProvider:
    provider_name = os.getenv("TRANSCRIPTION_PROVIDER", "local_whisper").lower()

    if provider_name == "local_whisper":
        return LocalWhisperProvider(model_size=os.getenv("WHISPER_MODEL_SIZE", "tiny"))
    if provider_name == "openai":
        return OpenAITranscriptionProvider()

    raise ValueError(f"Unsupported transcription provider: {provider_name}")


class DocumentRecord(BaseModel):
    id: int
    title: str
    original_filename: str
    safe_filename: str
    mime_type: str | None = None
    file_size_bytes: int
    status: str = "transcribed"
    raw_text: str
    cleaned_text: str | None = None
    language_code: str = "uz"
    created_at: datetime
    updated_at: datetime


_documents: dict[int, DocumentRecord] = {}
_next_document_id = 1


def sanitize_filename(original_name: str) -> str:
    name = Path(original_name).name
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    safe_stem = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in stem)
    safe_stem = safe_stem.strip("_") or "document"
    return f"{safe_stem}{suffix if suffix in ALLOWED_EXTENSIONS else '.mp3'}"


def validate_upload(file: UploadFile) -> None:
    if file.filename is None:
        raise HTTPException(status_code=400, detail="A file is required.")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload an audio file such as MP3, WAV, M4A, OGG, or MP4.",
        )

    mime_type = (file.content_type or "").lower()
    if mime_type and mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid audio MIME type.")


def build_document_record(
    title: str,
    original_filename: str,
    safe_filename: str,
    mime_type: str | None,
    size_bytes: int,
    raw_text: str,
    language_code: str,
) -> DocumentRecord:
    global _next_document_id

    now = datetime.now(timezone.utc)
    document = DocumentRecord(
        id=_next_document_id,
        title=title,
        original_filename=original_filename,
        safe_filename=safe_filename,
        mime_type=mime_type,
        file_size_bytes=size_bytes,
        status="transcribed",
        raw_text=raw_text,
        cleaned_text=raw_text,
        language_code=language_code,
        created_at=now,
        updated_at=now,
    )
    _documents[document.id] = document
    _next_document_id += 1
    return document


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/documents", response_model=DocumentRecord)
async def create_document(file: UploadFile = File(...)) -> DocumentRecord:
    validate_upload(file)

    original_filename = file.filename or "upload.mp3"
    safe_name = sanitize_filename(original_filename)
    destination = UPLOAD_DIR / safe_name

    contents = await file.read()
    destination.write_bytes(contents)

    title = Path(original_filename).stem.replace("_", " ").strip() or "Untitled lecture"
    provider = get_transcription_provider()
    transcription = provider.transcribe(destination)
    document = build_document_record(
        title=title,
        original_filename=original_filename,
        safe_filename=safe_name,
        mime_type=file.content_type,
        size_bytes=len(contents),
        raw_text=transcription.text,
        language_code=transcription.language_code,
    )
    return document


@app.get("/api/v1/documents", response_model=list[DocumentRecord])
async def list_documents() -> list[DocumentRecord]:
    return sorted(_documents.values(), key=lambda item: item.created_at, reverse=True)


@app.get("/api/v1/documents/{document_id}", response_model=DocumentRecord)
async def get_document(document_id: int) -> DocumentRecord:
    document = _documents.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.get("/api/v1/documents/{document_id}/download")
async def download_document(document_id: int, format: str = "txt") -> Any:
    document = _documents.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    text = document.cleaned_text or document.raw_text
    file_format = format.lower()
    if file_format not in {"txt", "docx", "pdf"}:
        raise HTTPException(status_code=400, detail="Unsupported export format")

    if file_format == "txt":
        return {"filename": f"{document.title}.txt", "content": text}

    if file_format == "docx":
        return {"filename": f"{document.title}.docx", "content": text}

    return {"filename": f"{document.title}.pdf", "content": text}


@app.delete("/api/v1/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: int) -> None:
    if document_id not in _documents:
        raise HTTPException(status_code=404, detail="Document not found")
    _documents.pop(document_id)

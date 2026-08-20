# MP3 into a Book

A local-first web application for turning lecture audio into editable book material.

The first version focuses on Uzbek lectures that may contain Arabic quotations. Users upload an audio file, the backend transcribes it, stores the transcript, and provides downloadable `.txt`, `.docx`, and `.pdf` versions.

## Project goals

### Phase 1 — MVP

- React + Vite + shadcn/ui frontend
- Python + FastAPI backend
- Upload MP3 and common audio formats
- Transcribe Uzbek + Arabic mixed speech
- Store source-file metadata and transcript in PostgreSQL
- Download transcript as TXT, DOCX, and PDF
- Keep the transcription provider behind a small interface so local/open-source ASR can be swapped in later
- Basic health check and automated tests

### Phase 2 — Local Docker environment

- Dockerfile for frontend
- Dockerfile for backend
- `docker-compose.yml`
- PostgreSQL with pgvector enabled
- Alembic migrations
- Environment-variable based configuration
- No API keys in source code

### Future phases

1. Better transcript editing and chapter/book organization
2. Chunking + embeddings
3. Semantic search / RAG over the book
4. Video transcription
5. Image/OCR ingestion
6. Speaker diarization
7. AI-assisted cleanup, chaptering, titles, summaries, and book formatting
8. Authentication and multi-user support
9. Production object storage and background workers

---

## Architecture

```text
                         MP3 into a Book
                              │
                              ▼
                  ┌─────────────────────┐
                  │ React + Vite +      │
                  │ shadcn/ui           │
                  │ Upload / Results    │
                  └──────────┬──────────┘
                             │ HTTP
                             ▼
                  ┌─────────────────────┐
                  │ FastAPI             │
                  │ REST API            │
                  ├─────────────────────┤
                  │ Upload service      │
                  │ Job service         │
                  │ Transcript service  │
                  │ Export service      │
                  │ ASR provider        │
                  └───────┬───────┬─────┘
                          │       │
                    SQLAlchemy    │ ASR
                          │       │
                          ▼       ▼
                  ┌────────────┐  ┌──────────────────────┐
                  │ PostgreSQL │  │ ASR Provider         │
                  │ + pgvector │  │                      │
                  │            │  │ Default: OpenAI API │
                  │ documents  │  │ Future: local        │
                  │ transcripts│  │ Whisper/Qwen/etc.    │
                  │ chunks     │  └──────────────────────┘
                  │ embeddings │
                  └────────────┘

             Future RAG path:
             Transcript
                 │
                 ▼
              Chunking
                 │
                 ▼
             Embedding model
                 │
                 ▼
        PostgreSQL + pgvector
                 │
                 ▼
       Semantic / hybrid search
                 │
                 ▼
                RAG
```

## Why PostgreSQL + pgvector?

This is intentionally one database instead of introducing a separate vector database.

PostgreSQL will store:

- documents
- uploaded-file metadata
- transcripts
- transcript chunks
- future embeddings
- future book/chapter metadata

When embeddings are introduced, pgvector can store vectors alongside normal relational data and support exact and approximate nearest-neighbor search.

Reference: https://github.com/pgvector/pgvector

---

# Language / transcription strategy

## Recommended MVP approach

Use a provider abstraction:

```text
TranscriptionProvider
       │
       ├── OpenAITranscriptionProvider   ← MVP default
       │
       └── LocalWhisperProvider          ← future/local option
```

The important design decision is **not** to hard-code the application to one ASR vendor.

### Open-source option: Whisper

OpenAI Whisper is multilingual and explicitly includes both Arabic (`ar`) and Uzbek (`uz`) in its supported language set.

Reference:
https://github.com/openai/whisper

For local experimentation, `whisper-large-v3` is a strong baseline. It is especially useful when privacy, recurring API cost, or offline processing becomes important.

There are also Uzbek-specific Whisper fine-tunes on Hugging Face. These may perform better on Uzbek conversational speech, but a model specialized for Uzbek should be evaluated carefully on your actual mixed Uzbek/Arabic lectures before replacing the multilingual baseline.

Example:
https://huggingface.co/maqsudxo1ja/uz-whisper-small-stt-v2

### Qwen3-ASR

Qwen3-ASR is another strong open-source ASR family and supports Arabic plus many other languages, but its published supported-language list does **not currently include Uzbek**. Therefore I would not make it the primary ASR choice for this project.

Reference:
https://github.com/QwenLM/Qwen3-ASR

### OpenAI API

Because you already have an OpenAI API key, the MVP can use OpenAI's speech-to-text endpoint.

Current API documentation lists `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, `whisper-1`, and diarization-capable transcription models.

Reference:
https://platform.openai.com/docs/api-reference/audio

The API key must remain on the FastAPI server and must never be placed in React/browser code.

Reference:
https://platform.openai.com/docs/api-reference/backward-compatibility

## Mixed Uzbek + Arabic recommendation

Do **not** translate Arabic into Uzbek during transcription.

The desired pipeline is:

```text
Audio
  │
  ▼
ASR
  │
  ├── Uzbek speech → Uzbek text
  │
  └── Arabic speech/quotation → Arabic text
  │
  ▼
Raw transcript
  │
  ▼
Optional cleanup stage
  │
  ▼
Editable transcript
```

For the first implementation, preserve the ASR output as the **raw transcript**. Later, an LLM cleanup stage can fix punctuation, paragraphs, obvious transcription artifacts, headings, and formatting without changing the meaning or translating quotations.

This separation is important because the transcript is source material for a book.

---

# Repository structure

```text
mp3-into-a-book/
├── AGENTS.md
├── AGENT_PROMPT.md
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   ├── services/
│   │   └── exporters/
│   └── tests/
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── components.json
│   └── src/
│
└── docs/
    └── architecture.md
```

---

# Prerequisites

Recommended:

- macOS/Linux
- VS Code
- Git
- Docker Desktop
- Docker Compose
- Node.js 22+
- Python 3.12+
- `uv`

You can run the complete application with Docker, so local Python/Node installations are mainly useful for development outside containers.

---

# Environment setup

## 1. Clone the repository

```bash
git clone <your-repository-url>
cd mp3-into-a-book
```

## 2. Create the local environment file

```bash
cp .env.example .env
```

Then update `.env` for your local machine. The app expects a local PostgreSQL database running on `localhost:5432` using your macOS username by default:

```env
APP_ENV=development
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE_MB=500

POSTGRES_DB=mp3book
POSTGRES_USER=$(whoami)
POSTGRES_PASSWORD=
DATABASE_URL=postgresql+asyncpg://$(whoami)@localhost:5432/mp3book

OPENAI_API_KEY=
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-transcribe

UPLOAD_DIR=/tmp/mp3-book-uploads
```

For a real local setup on macOS, use your current username as `POSTGRES_USER` and leave `POSTGRES_PASSWORD` blank unless your PostgreSQL installation requires one.

Never commit `.env`.

## 3. Manage PostgreSQL locally with Homebrew

If you installed PostgreSQL with Homebrew, use these commands to control the local database service:

```bash
# Start PostgreSQL
brew services start postgresql@16

# Stop PostgreSQL
brew services stop postgresql@16

# Restart PostgreSQL
brew services restart postgresql@16

# Check service status
brew services list

# Quick readiness check
pg_isready -h localhost -p 5432
```

This project’s startup script already does this automatically when needed, but these commands are useful when you want to manage the database manually.

## 4. Set up Local Whisper (recommended default)

This project is designed to keep transcription behind a provider interface, so Local Whisper can replace OpenAI without changing the API or frontend. The default provider is `local_whisper`.

### Install the required system dependency

On macOS with Homebrew:

```bash
brew install ffmpeg
```

### Install Python dependencies

From the project root or backend directory:

```bash
cd backend
. .venv/bin/activate
uv pip install openai-whisper
```

### Use Local Whisper in the app

Set this in `.env`:

```env
TRANSCRIPTION_PROVIDER=local_whisper
WHISPER_MODEL_SIZE=tiny
```

The first time the app transcribes an upload, Whisper will download the model automatically. For a local development machine, `tiny` is the quickest and most practical default. You can increase to `base`, `small`, or `medium` later for better quality if needed.

If you want to switch back to OpenAI instead:

```env
TRANSCRIPTION_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-transcribe
```

The backend route code should still be the same; only the provider implementation changes behind the interface.

## 5. Start the app locally (recommended)

This project includes a one-shot startup script that:

- loads `.env` defaults
- starts PostgreSQL if it is not already running
- creates the database if it does not exist
- runs Alembic migrations
- starts the backend and frontend together

```bash
./start-local.sh
```

Expected services:

```text
frontend  → http://localhost:5173
backend   → http://localhost:8000
API docs  → http://localhost:8000/docs
postgres  → localhost:5432
```

If you prefer to start each service manually instead of using the script:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
uv sync --dev
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

In a second terminal:

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev -- --host 0.0.0.0
```

## 6. Stop the app

When using the local script, press `Ctrl+C` in the terminal that launched it.

For manual runs, stop the backend and frontend processes in their respective terminals with `Ctrl+C`.

---

# Docker development (optional)

This project also supports Docker-based startup for local containerized development:

```bash
docker compose up --build
```

Expected services:

```text
frontend  → http://localhost:5173
backend   → http://localhost:8000
API docs  → http://localhost:8000/docs
postgres  → localhost:5432
```

To stop the stack:

```bash
docker compose down
```

To remove the database volume as well:

```bash
docker compose down -v
```

This deletes local PostgreSQL data.

---

# Backend checks and tests

```bash
cd backend
. .venv/bin/activate
uv run pytest
```

Swagger UI is available at:

```text
http://localhost:8000/docs
```

---

# Frontend development

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

The Vite development server should expose:

```text
http://localhost:5173
```

---

# Development workflow

Use this sequence for every feature:

```text
1. Understand requirement
        ↓
2. Update architecture if needed
        ↓
3. Backend schema/API
        ↓
4. Backend service
        ↓
5. Database migration
        ↓
6. Backend tests
        ↓
7. Frontend API integration
        ↓
8. Frontend UI
        ↓
9. End-to-end manual test
        ↓
10. Update documentation
```

Do not add infrastructure simply because it may be useful later.

---

# Initial API

The MVP should evolve around these endpoints:

```text
GET    /health
POST   /api/v1/documents
GET    /api/v1/documents
GET    /api/v1/documents/{document_id}
GET    /api/v1/documents/{document_id}/download?format=txt
GET    /api/v1/documents/{document_id}/download?format=docx
GET    /api/v1/documents/{document_id}/download?format=pdf
DELETE /api/v1/documents/{document_id}
```

For long-running transcription, the API should eventually expose a job model:

```text
POST /api/v1/jobs/transcribe
GET  /api/v1/jobs/{job_id}
```

For the local MVP, FastAPI background processing is acceptable. For production, move transcription to a durable worker queue such as Celery/RQ/Arq with Redis.

---

# Database model

Start simple.

```text
documents
──────────────
id
title
original_filename
mime_type
file_size
storage_path
status
language
created_at
updated_at


transcripts
──────────────
id
document_id
raw_text
cleaned_text
created_at
updated_at


transcript_chunks
──────────────
id
transcript_id
chunk_index
content
start_seconds
end_seconds
embedding     ← future
created_at
```

Do not add the embedding column until the embedding model and dimensions are selected.

This avoids locking the schema to a particular embedding model too early.

---

# Export formats

The export layer should be isolated from the API layer:

```text
Transcript
    │
    ├── TXT exporter
    ├── DOCX exporter
    └── PDF exporter
```

Recommended Python libraries:

- DOCX: `python-docx`
- PDF: `reportlab`

The exported document should initially contain:

```text
Title

Transcript

[paragraphs...]
```

Later, book formatting can add:

- title page
- author
- chapters
- headings
- footnotes
- Arabic quotations
- page numbers
- table of contents

---

# Testing strategy

## Backend

At minimum:

```text
- health endpoint
- upload validation
- document creation
- transcript persistence
- export generation
- unsupported file rejection
- database error handling
```

Use:

- pytest
- pytest-asyncio
- httpx

## Frontend

At minimum:

```text
- upload UI renders
- file selection works
- upload request is sent
- loading state appears
- error state appears
- transcript result renders
- download actions work
```

Later add Playwright for browser-level tests.

---

# Security requirements

Even for local development:

- Never expose `OPENAI_API_KEY` to React.
- Validate file type and size.
- Never trust the uploaded filename.
- Generate server-side storage names.
- Do not execute uploaded files.
- Store uploads outside the source tree.
- Avoid returning arbitrary filesystem paths.
- Add request size limits.
- Add authentication before exposing the app publicly.

---

# Important product rule

The application is creating source material for a book.

Therefore:

**Never silently rewrite the transcript.**

Keep:

```text
RAW TRANSCRIPT
```

and, when AI cleanup is introduced:

```text
CLEANED TRANSCRIPT
```

The user should be able to compare or restore the raw version.

AI cleanup should:

- preserve Uzbek
- preserve Arabic
- preserve quotations
- preserve names
- preserve religious/technical terminology
- fix obvious punctuation and paragraph structure
- avoid inventing missing content
- mark uncertain content when confidence is low

---

# Phase 2 roadmap

After the MVP works:

## Phase 2A — Better transcript editor

```text
Upload
  ↓
Transcribe
  ↓
Edit transcript
  ↓
Save
  ↓
Export
```

## Phase 2B — Book structure

```text
Book
 ├── Chapter 1
 │    ├── Section
 │    └── Section
 ├── Chapter 2
 └── Chapter 3
```

## Phase 2C — Embeddings

```text
Transcript
    ↓
Chunk
    ↓
Embedding model
    ↓
pgvector
```

## Phase 2D — RAG

```text
User question
      ↓
Embedding
      ↓
Vector search
      ↓
Relevant chunks
      ↓
LLM
      ↓
Answer with source references
```

---

# Recommended implementation order

Build in this exact order:

### Milestone 1

```text
Repository
Docker
FastAPI
React
PostgreSQL
Health checks
```

### Milestone 2

```text
Upload MP3
Store metadata
Persist document
```

### Milestone 3

```text
ASR provider interface
OpenAI transcription provider
Persist raw transcript
```

### Milestone 4

```text
TXT export
DOCX export
PDF export
```

### Milestone 5

```text
React upload page
Progress/status
Transcript page
Download buttons
```

### Milestone 6

```text
Tests
Error handling
Documentation
```

Only after these milestones should embeddings/RAG be added.

---

# Definition of done for the MVP

A user should be able to:

1. Open the web application.
2. Select an MP3 lecture.
3. Upload it.
4. Wait while transcription runs.
5. See the transcript.
6. See Uzbek text as Uzbek.
7. See Arabic quotations as Arabic where the ASR recognizes them.
8. Save the transcript in PostgreSQL.
9. Download TXT.
10. Download DOCX.
11. Download PDF.
12. Restart Docker and still see the stored document metadata/transcript.

If all twelve work, Phase 1 is complete.

---

# Current limitations

This starter architecture does not attempt to solve:

- perfect Uzbek ASR
- perfect Arabic quotation recognition
- speaker diarization
- book-level editorial quality
- automatic chapter generation
- OCR
- video processing
- production-scale queues
- authentication
- cloud storage

Those are deliberately later milestones.

The most important first experiment is to upload several representative Uzbek lectures and measure actual transcription quality before committing to a local ASR model or fine-tuning strategy.

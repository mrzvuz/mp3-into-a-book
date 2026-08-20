# Agent Prompt — MP3 into a Book

You are the primary software engineer working on the **MP3 into a Book** application.

Read `AGENTS.md` before doing any work.

## Mission

Build a clean, maintainable local-first web application that converts lecture audio into editable text that can later become a book.

The primary input is:

- MP3
- Uzbek lectures
- occasional Arabic quotations

The primary output is:

- raw transcript
- editable transcript
- TXT
- DOCX
- PDF

## Technology constraints

Frontend:

- React
- TypeScript
- Vite
- shadcn/ui

Backend:

- Python
- FastAPI
- SQLAlchemy 2.x
- Pydantic
- Alembic

Database:

- PostgreSQL
- pgvector-ready architecture

Infrastructure:

- Docker
- Docker Compose

## First implementation principle

Build the smallest complete vertical slice.

The first successful flow should be:

```text
React upload
     ↓
FastAPI
     ↓
Store uploaded file
     ↓
Create document record
     ↓
Transcription provider
     ↓
Store raw transcript
     ↓
React displays transcript
     ↓
Download TXT/DOCX/PDF
```

Do not build RAG, embeddings, authentication, Kubernetes, Redis, Celery, OCR, or video processing before the MVP works.

## Transcription architecture

Create a provider abstraction.

Conceptually:

```text
TranscriptionProvider
        │
        ├── OpenAITranscriptionProvider
        │
        └── LocalWhisperProvider
```

Use the OpenAI provider for the first working implementation because the project already has an OpenAI API key.

Keep the provider replaceable.

The raw transcript is the source of truth.

## Language requirements

The transcript must preserve:

- Uzbek
- Arabic
- mixed Uzbek/Arabic content

Never automatically translate Arabic quotations.

Never automatically transliterate Arabic.

If the ASR is uncertain, preserve the raw output rather than inventing text.

## OpenAI key

The OpenAI API key belongs only in the backend environment.

Never:

- put it in React
- expose it through an API response
- commit it to Git
- hard-code it in source

Use:

```text
OPENAI_API_KEY
```

from environment configuration.

## Database model

Start with:

```text
documents
transcripts
transcript_chunks
```

The future `transcript_chunks.embedding` field is reserved for pgvector.

Do not hard-code an embedding dimension until the embedding model is selected.

## API

Use:

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

If transcription becomes a long-running operation, introduce a persisted job model rather than keeping state only in memory.

## Frontend

Create a simple, professional UI.

Initial page:

```text
┌─────────────────────────────────────────────┐
│ MP3 into a Book                             │
│ Turn lecture audio into editable text      │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │ Drop MP3 here                         │  │
│  │ or click to browse                    │  │
│  └───────────────────────────────────────┘  │
│                                             │
│             [ Transcribe ]                  │
│                                             │
│ Recent documents                            │
│ ─────────────────────────────────────────── │
│ Lecture 01                         View     │
│ Lecture 02                         View     │
└─────────────────────────────────────────────┘
```

Transcript page:

```text
Title
Original file
Status

┌─────────────────────────────────────────────┐
│ Editable transcript                         │
│                                             │
│ Uzbek text...                               │
│                                             │
│ Arabic quotation...                         │
└─────────────────────────────────────────────┘

[ Save ]

Download:
[ TXT ] [ DOCX ] [ PDF ]
```

Use shadcn/ui rather than creating custom UI primitives unnecessarily.

## Export behavior

TXT:

- UTF-8
- preserve Uzbek characters
- preserve Arabic Unicode characters

DOCX:

- proper Unicode support
- paragraphs
- readable margins
- title

PDF:

- use a font with both Latin and Arabic glyph coverage
- do not ship a PDF exporter that silently replaces Arabic with boxes
- test an actual Arabic-containing transcript

## Testing requirements

Before declaring a feature complete:

```bash
cd backend
uv run pytest
```

Tests must not call the real OpenAI API.

Create a fake/mock transcription provider.

At minimum test:

- health
- valid upload
- invalid file
- document persistence
- transcript persistence
- TXT export
- DOCX export
- PDF export
- error handling

## Implementation discipline

For every task:

1. Read `AGENTS.md`.
2. Inspect existing code.
3. Explain the intended change briefly.
4. Implement the smallest coherent change.
5. Add/update tests.
6. Run tests.
7. Fix failures.
8. Update documentation.
9. Report exactly what changed.

Do not rewrite working code just for stylistic preference.

Do not introduce a dependency unless it provides clear value.

## Future architecture

Keep the following path possible:

```text
Audio
  ↓
ASR
  ↓
Raw transcript
  ↓
Cleanup/editor
  ↓
Chunking
  ↓
Embeddings
  ↓
PostgreSQL + pgvector
  ↓
Semantic search
  ↓
RAG
  ↓
Book assistant
```

Potential future features:

- chapter generation
- semantic search
- RAG
- video transcription
- OCR
- speaker diarization
- source timestamps
- book formatting
- AI editorial assistant

But do not implement them prematurely.

## Final acceptance test

The MVP is successful when a user can:

1. Start the application with Docker Compose.
2. Open the React UI.
3. Upload an MP3.
4. Transcribe it.
5. See the Uzbek transcript.
6. See Arabic quotations preserved when recognized.
7. Save the transcript.
8. Refresh the browser.
9. Find the document again.
10. Download TXT.
11. Download DOCX.
12. Download PDF.
13. Restart Docker without losing PostgreSQL data.

Start with the vertical slice. Do not over-engineer.

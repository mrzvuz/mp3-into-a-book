# AGENTS.md

## Project

MP3 into a Book is a local-first web application that converts lecture audio into editable book material.

Primary use case:

- Uzbek-language lectures
- Arabic quotations embedded in Uzbek speech
- transcript preservation
- later editing into a book

## Stack

Frontend:

- React
- TypeScript
- Vite
- shadcn/ui
- Tailwind CSS

Backend:

- Python
- FastAPI
- SQLAlchemy 2.x
- Pydantic
- Alembic

Database:

- PostgreSQL
- pgvector reserved for future embeddings/RAG

Infrastructure:

- Docker
- Docker Compose

## Core architectural rule

Keep external providers behind interfaces.

For example:

```python
class TranscriptionProvider(Protocol):
    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        ...
```

Do not allow OpenAI-specific code to leak throughout the application.

The application must be able to replace:

```text
OpenAI ASR
```

with:

```text
Local Whisper
```

without changing API routes or frontend code.

## Source-of-truth rule

Always preserve the original/raw transcript.

Never overwrite raw transcription with an AI-cleaned version.

Preferred data model:

```text
raw_text
cleaned_text
```

If cleanup is introduced, it must be explicit.

## Language rule

The application must preserve the language present in the source.

Do not translate Arabic quotations into Uzbek.

Do not transliterate Arabic unless the user explicitly requests it.

Do not silently translate Uzbek into another language.

## AI cleanup rule

AI cleanup may:

- add punctuation
- fix obvious spacing
- split paragraphs
- identify likely headings
- normalize obvious transcription artifacts

AI cleanup must not:

- invent missing sentences
- paraphrase religious quotations
- change names
- change theological/technical meaning
- silently remove repeated content
- translate text
- replace uncertain words with confident guesses

When uncertain, preserve the raw wording.

## Backend conventions

Use:

- async FastAPI endpoints where appropriate
- dependency injection
- typed Python
- Pydantic request/response schemas
- SQLAlchemy 2.x style
- service layer for business logic
- repository/data-access layer only where it provides real value
- environment configuration through settings
- migrations through Alembic

Do not put database logic directly inside route handlers.

Bad:

```text
route → SQLAlchemy queries → business logic → export
```

Preferred:

```text
route
  ↓
service
  ↓
repository/model
```

## Frontend conventions

Use:

- TypeScript
- functional React components
- shadcn/ui components
- accessible forms
- explicit loading/error/success states
- API client abstraction

Avoid:

- huge components
- duplicated API calls
- hard-coded backend URLs
- exposing secrets in frontend code

## API conventions

Prefix application routes with:

```text
/api/v1
```

Health endpoint:

```text
/health
```

Use HTTP semantics correctly.

Examples:

```text
POST   /documents
GET    /documents
GET    /documents/{id}
DELETE /documents/{id}
```

## File handling

Never trust the original filename.

Generate safe server-side filenames.

Validate:

- extension
- MIME type where possible
- file size

Never execute uploaded content.

Store uploads in a dedicated data directory.

## Database

Use PostgreSQL from the beginning.

Do not introduce SQLite unless there is a compelling test-specific reason.

The database should be designed so that future embeddings can be added without a major rewrite.

Do not select a fixed embedding dimension until the embedding model is chosen.

## Docker

Development should work with:

```bash
docker compose up --build
```

Services should be easy to understand.

Prefer:

```text
frontend
backend
postgres
```

Do not add Redis, Celery, Kubernetes, or other infrastructure until the application actually requires it.

For long-running production transcription, a durable queue can be introduced later.

## Testing

Every meaningful backend feature should have tests.

At minimum:

- endpoint tests
- service tests
- validation tests
- exporter tests

Tests must not require the real OpenAI API.

Mock external providers.

Use dependency injection to substitute fake transcription providers.

## Documentation

When changing architecture or behavior:

1. Update README.md.
2. Update API documentation if applicable.
3. Update migration notes if the database changes.
4. Keep examples executable.

## Git discipline

Prefer small commits.

Suggested commit style:

```text
feat: add document upload
feat: add transcription provider
feat: add transcript exports
test: add upload validation tests
docs: update local setup
fix: handle transcription failure
```

## Agent behavior

Before changing code:

1. Inspect the repository.
2. Understand existing architecture.
3. Identify the smallest change that solves the requirement.
4. Reuse existing patterns.
5. Avoid unnecessary dependencies.
6. Implement tests.
7. Run tests.
8. Update documentation.

Do not rewrite unrelated files.

Do not introduce speculative architecture.

## Definition of quality

A good implementation is:

- simple
- typed
- testable
- replaceable
- observable
- secure
- understandable by another engineer

Prefer boring, maintainable engineering over clever abstractions.

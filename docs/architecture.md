# Architecture

## System

```text
┌──────────────────────┐
│      Browser         │
│ React + Vite +       │
│ shadcn/ui            │
└──────────┬───────────┘
           │ HTTP/JSON
           ▼
┌──────────────────────┐
│       FastAPI        │
│                      │
│ Routes               │
│   ↓                  │
│ Services             │
│   ↓                  │
│ Providers / Exporters│
└───────┬───────┬──────┘
        │       │
        │       └─────────────────┐
        ▼                         ▼
┌──────────────┐       ┌────────────────────┐
│ PostgreSQL   │       │ Transcription      │
│ + pgvector   │       │ Provider           │
│              │       │                    │
│ documents    │       │ OpenAI (MVP)       │
│ transcripts  │       │ Local Whisper      │
│ chunks       │       │ (future)           │
│ embeddings   │       └────────────────────┘
└──────────────┘
```

## Data flow

```text
MP3
 │
 ▼
Upload validation
 │
 ▼
Safe local storage
 │
 ▼
Document record
 │
 ▼
ASR
 │
 ▼
Raw transcript
 │
 ├──────────────► PostgreSQL
 │
 ▼
Optional cleanup
 │
 ▼
Editable transcript
 │
 ├──► TXT
 ├──► DOCX
 └──► PDF
```

## Future RAG

```text
Transcript
    │
    ▼
Chunking
    │
    ▼
Embedding model
    │
    ▼
pgvector
    │
    ▼
Similarity / hybrid search
    │
    ▼
Retrieved context
    │
    ▼
LLM
    │
    ▼
Answer / book assistant
```

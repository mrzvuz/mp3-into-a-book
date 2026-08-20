#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Load env with defaults so the script still works if .env is missing or partial.
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

export POSTGRES_DB="${POSTGRES_DB:-mp3book}"
export POSTGRES_USER="${POSTGRES_USER:-$(whoami)}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://${POSTGRES_USER}@localhost:5432/${POSTGRES_DB}}"
export APP_ENV="${APP_ENV:-development}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export MAX_UPLOAD_SIZE_MB="${MAX_UPLOAD_SIZE_MB:-500}"
export UPLOAD_DIR="${UPLOAD_DIR:-/tmp/mp3-book-uploads}"
export TRANSCRIPTION_PROVIDER="${TRANSCRIPTION_PROVIDER:-local_whisper}"
export WHISPER_MODEL_SIZE="${WHISPER_MODEL_SIZE:-tiny}"
export OPENAI_TRANSCRIPTION_MODEL="${OPENAI_TRANSCRIPTION_MODEL:-gpt-4o-transcribe}"
export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://localhost:8000}"

# Ensure PostgreSQL is available
if ! command -v pg_isready >/dev/null 2>&1; then
  echo "PostgreSQL client not found. Install it with:"
  echo "  brew install postgresql@16"
  exit 1
fi

if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
  echo "Starting local PostgreSQL..."
  brew services start postgresql@16
fi

# Create database if needed
if ! PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB';" | grep -q 1; then
  echo "Creating database: $POSTGRES_DB"
  createdb -h localhost -U "$POSTGRES_USER" "$POSTGRES_DB" || true
fi

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
if command -v uv >/dev/null 2>&1; then
  uv sync --dev
fi

# Run Alembic migrations
if command -v uv >/dev/null 2>&1; then
  uv run alembic upgrade head || true
fi

# Start backend in background
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd ../frontend
npm install

# Start frontend in background
VITE_API_BASE_URL="$VITE_API_BASE_URL" npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

echo
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo
echo "Press Ctrl+C to stop both services"

trap 'kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true; exit 0' INT TERM

wait
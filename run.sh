#!/usr/bin/env bash
# DeNovoVHH-DB — launch script
# Usage: ./run.sh   (serves at http://127.0.0.1:8000)
set -e
cd "$(dirname "$0")"
PORT="${PORT:-8000}"
echo "Starting DeNovoVHH-DB on http://127.0.0.1:${PORT}"
echo "  - Web UI:        http://127.0.0.1:${PORT}/"
echo "  - API docs:      http://127.0.0.1:${PORT}/docs"
echo "  - OpenAPI JSON:  http://127.0.0.1:${PORT}/openapi.json"
PYTHONPATH=. exec uvicorn app.main:app --host 127.0.0.1 --port "${PORT}"

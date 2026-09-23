# DeNovoVHH-DB — production image (FastAPI + uvicorn, read-only SQLite release)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    WEB_CONCURRENCY=1

WORKDIR /app

# Dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application + bundled read-only database
COPY . .

# Drop privileges
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Managed platforms (Render/Railway/Fly) inject $PORT; default 8000 locally.
# The DB is read-only, so multiple workers are safe — scale with WEB_CONCURRENCY.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers ${WEB_CONCURRENCY}"]

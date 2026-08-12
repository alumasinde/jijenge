# Root convenience image. docker compose uses backend/Dockerfile directly.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv/app

RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential pkg-config default-libmysqlclient-dev     && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 1000 appuser
COPY --chown=appuser:appuser backend/ .
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3   CMD curl -fsS http://127.0.0.1:8000/api/v1/system/health || exit 1

CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}"]

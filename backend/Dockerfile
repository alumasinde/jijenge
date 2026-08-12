# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

# Prevents Python from buffering stdout/stderr — needed so `docker logs` shows
# output immediately instead of holding it in a buffer.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

# System deps needed to build mysql-connector-python / argon2-cffi wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        default-libmysqlclient-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps in their own layer so `docker build` skips this step
# whenever only application code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run as a non-root user.
RUN useradd --create-home --uid 1000 appuser
COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/api/v1/system/health || exit 1

# --workers scales with CPU cores; tune via UVICORN_WORKERS at deploy time.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}"]

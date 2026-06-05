# Backend image for the 游侠百科 FastAPI server.
# Works on Hugging Face Spaces (Docker), Render, Fly.io, Railway, or any VPS.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server ./server

# Ephemeral storage for generated pages. World-writable so it also works on
# platforms that run the container as a non-root user (e.g. HF Spaces uid 1000).
RUN mkdir -p /app/data/pages && chmod -R 777 /app/data
ENV STORAGE_DIR=/app/data/pages

EXPOSE 7860

# $PORT is honored when the platform injects it (Render/Railway); defaults to 7860 (HF Spaces).
CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-7860}"]

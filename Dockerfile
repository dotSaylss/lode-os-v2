# ── LodeOS / Mogul agent backend — FastAPI + Google ADK on Cloud Run ─────────
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY main.py mcp_server.py ./
COPY agents/ ./agents/
COPY services/ ./services/
COPY models/ ./models/
COPY data/ ./data/

# Cloud Run injects $PORT (default 8080). Uvicorn reads it directly via
# --port, and proper exec-form CMD ensures clean signal handling.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT}"]

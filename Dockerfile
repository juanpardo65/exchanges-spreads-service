FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY pyproject.toml ./

# spreads lives in src/spreads; run as module so spreads is importable
ENV PYTHONPATH=/app/src

EXPOSE 8000

# PORT must be set via --env-file .env or -e PORT=...
CMD ["sh", "-c", "uvicorn spreads.main:app --host 0.0.0.0 --port \"$PORT\""]

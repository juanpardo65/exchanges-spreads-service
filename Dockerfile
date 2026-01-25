FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY pyproject.toml ./

ENV PYTHONPATH=/app/src
EXPOSE 8000

# PORT, LOG_LEVEL, HTTP_TIMEOUT, PRICE_UPDATE_INTERVAL required;
# DATABASE_URL, SPREAD_HISTORY_INTERVAL_SECONDS optional. Pass via --env-file .env or -e.
CMD ["sh", "-c", "uvicorn spreads.main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]

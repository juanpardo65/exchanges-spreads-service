#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

[ -f .env ] || { echo "Missing .env. Copy .env.example to .env and set required variables."; exit 1; }
set -a && . ./.env && set +a
: "${PORT:?PORT must be set in .env}"
PYTHONPATH=src uv run uvicorn spreads.main:app --host 0.0.0.0 --port "$PORT"

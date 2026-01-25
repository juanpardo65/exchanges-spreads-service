# Futures Spreads API

Aggregates **USDT-margined perpetual futures** prices from Bybit, Gate, MEXC, and Binance, computes spreads, and exposes a JSON API for arbitrage bots.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| GET | `/v1/prices` | All symbols from cache (updated in the background every few seconds). Fast response. |
| GET | `/v1/prices?symbol=BTCUSDT` | Single symbol from cache |
| GET | `/v1/spread-history?symbol=BTCUSDT&from=...&to=...&interval=5` | Spread % time series for charts (requires `DATABASE_URL`) |

**Background updates:** Every `PRICE_UPDATE_INTERVAL` seconds the service fetches all tickers from all exchanges in parallel, merges by symbol, and writes to an in-memory cache. `/v1/prices` reads from the cache only — no extra exchange requests.

**`/v1/prices` response:** `prices` (bid/ask/last/mark per exchange), `arbitrage` (best_bid, best_ask, spread, spread_bps, direction), `pairwise_spreads` (spreads between exchange pairs), `errors` (exchange fetch errors).

### GET /v1/spread-history

Spread % history for charts and analysis. Requires `DATABASE_URL`; otherwise returns **503** with `{"error": "Spread history is disabled: DATABASE_URL not set"}`.

| Query | Required | Description |
|-------|----------|-------------|
| `symbol` | yes | Symbol, e.g. `BTCUSDT` |
| `from` | no | Start time: ISO 8601 or Unix ms. Default: 24 hours ago. |
| `to` | no | End time: ISO 8601 or Unix ms. Default: now. |
| `interval` | no | Aggregation step in minutes (5, 15, 60). If omitted, raw points. |

**Response:**

```json
{
  "symbol": "BTCUSDT",
  "from": "2026-01-24T12:00:00Z",
  "to": "2026-01-25T12:00:00Z",
  "interval_minutes": 5,
  "series": [
    { "ts": "2026-01-24T12:00:00Z", "spread_pct_abs": 0.05, "net_spread_pct": 0.048 },
    { "ts": "2026-01-24T12:05:00Z", "spread_pct_abs": 0.06, "net_spread_pct": 0.055 }
  ]
}
```

- `spread_pct_abs`: `|best_bid − best_ask| / best_ask × 100`
- `net_spread_pct`: spread including funding (spread_pct_abs + funding adjustment)

## Configuration

No hardcoded defaults: set all variables in `.env` (copy from `.env.example`).

| Variable | Required | Description |
|----------|----------|-------------|
| `HTTP_TIMEOUT` | yes | Timeout for exchange HTTP requests (seconds). |
| `PORT` | yes | Server port. |
| `LOG_LEVEL` | yes | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `PRICE_UPDATE_INTERVAL` | yes | Seconds to wait after each full price refresh before the next. |
| `DATABASE_URL` | no | PostgreSQL URL, e.g. `postgresql://user:pass@localhost:5432/db`. If set: spread history is enabled; if unset: history disabled, `GET /v1/spread-history` returns 503. |
| `SPREAD_HISTORY_INTERVAL_SECONDS` | no | How often to append a spread snapshot to Postgres (seconds). Only used when `DATABASE_URL` is set. |

**Symbol discovery:** The list of USDT perpetual symbols is **loaded at startup** from all exchanges (Bybit, Binance, MEXC, Gate) and kept in memory. **Prices are updated in the background** in parallel for all symbols; the loop runs every `PRICE_UPDATE_INTERVAL` seconds after the previous run. A symbol may exist only on a subset of exchanges; spreads are returned for the exchanges where it is listed.

## Database (for spread history)

`GET /v1/spread-history` needs Postgres. The app creates the `spread_history` table on startup via `ensure_schema`; you only need a running Postgres and a database.

### Local Postgres (no Docker)

**1. Install and start Postgres**

- **macOS (Homebrew):**
  ```bash
  brew install postgresql@16
  brew services start postgresql@16
  export PATH="$(brew --prefix)/opt/postgresql@16/bin:$PATH"   # if psql not found
  ```
- **Linux (Debian/Ubuntu):**
  ```bash
  sudo apt install postgresql postgresql-client
  sudo systemctl start postgresql
  ```
- **Other:** [postgresql.org/download](https://www.postgresql.org/download/)

**2. Create user and database**

From the project root:

```bash
psql -d postgres -f scripts/init-local-db.sql
```

If that fails (e.g. auth), try with the `postgres` system user:

```bash
# Linux sometimes: sudo -u postgres psql -d postgres -f scripts/init-local-db.sql
# macOS Homebrew: psql -d postgres -f scripts/init-local-db.sql
```

This creates user `spreads` with password `spreads` and database `spreads`. To use another password, edit `scripts/init-local-db.sql` and then use it in `DATABASE_URL`.

**3. Add to `.env`**

```
DATABASE_URL=postgresql://spreads:spreads@localhost:5432/spreads
SPREAD_HISTORY_INTERVAL_SECONDS=3600
```

**4. (optional) Check**

```bash
psql "postgresql://spreads:spreads@localhost:5432/spreads" -c "\dt"
```

Empty list is fine; `spread_history` will appear after the first app run.

---

### Docker Compose (alternative)

```bash
docker compose up -d postgres
```

Then in `.env`: `DATABASE_URL=postgresql://spreads:spreads@localhost:5432/spreads` and `SPREAD_HISTORY_INTERVAL_SECONDS=3600`.

### Cloud / existing Postgres

Use your instance URL in `DATABASE_URL` and set `SPREAD_HISTORY_INTERVAL_SECONDS=3600`.

---

If `DATABASE_URL` is unset or empty, spread history is disabled and `GET /v1/spread-history` returns 503.

## Run

### Local

Copy `.env.example` to `.env` and set all required variables (`HTTP_TIMEOUT`, `PORT`, `LOG_LEVEL`, `PRICE_UPDATE_INTERVAL`). Optional: `DATABASE_URL`, `SPREAD_HISTORY_INTERVAL_SECONDS` for spread history.

```bash
cp .env.example .env
# edit .env

# run with uv (sources .env, uses PORT)
./run.sh
```

Or manually (ensure `.env` is loaded and `PORT` is set):

```bash
pip install -r requirements.txt
# [ -f .env ] && set -a && . ./.env && set +a
PYTHONPATH=src uvicorn spreads.main:app --host 0.0.0.0 --port "$PORT"
```

### Docker

Pass required env vars (`HTTP_TIMEOUT`, `PORT`, `LOG_LEVEL`, `PRICE_UPDATE_INTERVAL`). Optional: `DATABASE_URL`, `SPREAD_HISTORY_INTERVAL_SECONDS`.

```bash
docker build -t spreads .
docker run -p 8000:8000 --env-file .env spreads
```

## Development

```bash
# install with dev deps (uv)
uv sync --all-extras

# or pip
pip install -e ".[dev]"

# run tests
pytest
```

## Stack

- Python 3.11+
- FastAPI, httpx, pydantic, pydantic-settings, uvicorn
- asyncpg (for Postgres spread history)

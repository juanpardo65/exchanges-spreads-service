"""Postgres: pool, spread_history table, write and read."""

import logging
from datetime import datetime, timezone
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS spread_history (
    symbol varchar(32) NOT NULL,
    ts timestamptz NOT NULL,
    spread_pct_abs numeric(12,6) NOT NULL,
    net_spread_pct numeric(12,6) NOT NULL,
    best_bid_ex varchar(16) NOT NULL,
    best_ask_ex varchar(16) NOT NULL
);
"""
CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_spread_history_symbol_ts ON spread_history (symbol, ts);
"""


async def create_pool(database_url: str) -> asyncpg.Pool:
    """Create asyncpg pool. min_size=1, max_size=4, command_timeout=10."""
    return await asyncpg.create_pool(
        database_url,
        min_size=1,
        max_size=4,
        command_timeout=10,
    )


async def ensure_schema(pool: asyncpg.Pool) -> None:
    """Create spread_history table and index if not exist."""
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLE)
        await conn.execute(CREATE_INDEX)


async def write_spread_history(
    pool: asyncpg.Pool,
    cache: "dict[str, Any]",  # dict[symbol, PricesResponse]
) -> None:
    """
    Bulk insert current spread snapshots into spread_history.
    On DB error, log and skip (do not raise).
    """
    from .models import PricesResponse

    if not cache:
        return
    now = datetime.now(timezone.utc)
    symbols: list[str] = []
    ts_list: list[datetime] = []
    spread_list: list[float] = []
    net_list: list[float] = []
    bid_ex_list: list[str] = []
    ask_ex_list: list[str] = []
    for r in cache.values():
        if not isinstance(r, PricesResponse):
            continue
        symbols.append(r.symbol)
        ts_list.append(now)
        spread_list.append(float(r.arbitrage.spread_pct_abs))
        net_list.append(float(r.arbitrage.net_spread_pct))
        bid_ex_list.append((r.arbitrage.best_bid.exchange or "")[:16])
        ask_ex_list.append((r.arbitrage.best_ask.exchange or "")[:16])
    if not symbols:
        return
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO spread_history (symbol, ts, spread_pct_abs, net_spread_pct, best_bid_ex, best_ask_ex)
            SELECT * FROM unnest($1::varchar[], $2::timestamptz[], $3::numeric[], $4::numeric[], $5::varchar[], $6::varchar[])
            """,
            symbols,
            ts_list,
            spread_list,
            net_list,
            bid_ex_list,
            ask_ex_list,
        )
    logger.info("spread_history saved: %d rows at %s", len(symbols), now.isoformat())


async def get_spread_history(
    pool: asyncpg.Pool,
    symbol: str,
    from_ts: datetime,
    to_ts: datetime,
    interval_minutes: int | None = None,
) -> list[dict[str, Any]]:
    """
    Select spread_history for symbol in [from_ts, to_ts].
    If interval_minutes is set, aggregate into buckets (AVG spread_pct_abs, net_spread_pct); else raw rows.
    Returns list of dicts with ts, spread_pct_abs, net_spread_pct, best_bid_ex, best_ask_ex.
    """
    async with pool.acquire() as conn:
        if interval_minutes is None or interval_minutes < 1:
            rows = await conn.fetch(
                """
                SELECT ts, spread_pct_abs, net_spread_pct, best_bid_ex, best_ask_ex
                FROM spread_history
                WHERE symbol = $1 AND ts >= $2 AND ts <= $3
                ORDER BY ts
                """,
                symbol,
                from_ts,
                to_ts,
            )
            return [
                {
                    "ts": r["ts"],
                    "spread_pct_abs": float(r["spread_pct_abs"]),
                    "net_spread_pct": float(r["net_spread_pct"]),
                    "best_bid_ex": r["best_bid_ex"] or "",
                    "best_ask_ex": r["best_ask_ex"] or "",
                }
                for r in rows
            ]
        rows = await conn.fetch(
            """
            SELECT
                date_trunc('hour', ts) + (floor(extract(minute from ts)::numeric / $4) * $4) * interval '1 minute' AS bucket,
                avg(spread_pct_abs)::numeric AS spread_pct_abs,
                avg(net_spread_pct)::numeric AS net_spread_pct,
                (array_agg(best_bid_ex))[1] AS best_bid_ex,
                (array_agg(best_ask_ex))[1] AS best_ask_ex
            FROM spread_history
            WHERE symbol = $1 AND ts >= $2 AND ts <= $3
            GROUP BY 1
            ORDER BY 1
            """,
            symbol,
            from_ts,
            to_ts,
            interval_minutes,
        )
        return [
            {
                "ts": r["bucket"],
                "spread_pct_abs": float(r["spread_pct_abs"]),
                "net_spread_pct": float(r["net_spread_pct"]),
                "best_bid_ex": r["best_bid_ex"] or "",
                "best_ask_ex": r["best_ask_ex"] or "",
            }
            for r in rows
        ]

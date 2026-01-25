"""Bybit futures (linear / USDT-margined) provider."""

import httpx

from .base import ExchangePrices, to_canonical_symbol, to_exchange_symbol

BASE = "https://api.bybit.com"


async def fetch_all_symbols_bybit(timeout: float) -> set[str]:
    """
    Fetch all USDT-margined perpetual symbols from Bybit.
    GET /v5/market/tickers?category=linear (no symbol) returns all; list[].symbol is canonical.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/v5/market/tickers", params={"category": "linear"})
        r.raise_for_status()
        data = r.json()
    if data.get("retCode") != 0:
        raise RuntimeError(data.get("retMsg", "Bybit API error"))
    lst = data.get("result", {}).get("list") or []
    return {to_canonical_symbol(t.get("symbol", "")) for t in lst if t.get("symbol")}


async def fetch_all_prices_bybit(timeout: float) -> dict[str, ExchangePrices]:
    """
    Fetch all USDT-margined perpetual tickers from Bybit in one request.
    GET /v5/market/tickers?category=linear (no symbol). Returns dict[canonical_symbol, ExchangePrices].
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/v5/market/tickers", params={"category": "linear"})
        r.raise_for_status()
        data = r.json()
    if data.get("retCode") != 0:
        raise RuntimeError(data.get("retMsg", "Bybit API error"))
    lst = data.get("result", {}).get("list") or []
    out: dict[str, ExchangePrices] = {}
    for t in lst:
        sym = t.get("symbol") or ""
        if not sym:
            continue
        canon = to_canonical_symbol(sym)
        out[canon] = ExchangePrices(
            exchange="bybit",
            bid=str(t.get("bid1Price") or t.get("lastPrice", "0")),
            ask=str(t.get("ask1Price") or t.get("lastPrice", "0")),
            last=str(t.get("lastPrice", "0")),
            mark=str(t.get("markPrice") or t.get("lastPrice", "0")),
            funding=str(t.get("fundingRate") or t.get("fundRate") or "0"),
        )
    return out


async def fetch_bybit(symbol: str, timeout: float) -> ExchangePrices:
    """
    Fetch futures ticker from Bybit. category=linear = USDT-margined perpetuals.
    Uses symbol as-is (BTCUSDT).
    """
    sym = to_exchange_symbol(symbol, "bybit")
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(
            f"{BASE}/v5/market/tickers",
            params={"category": "linear", "symbol": sym},
        )
        r.raise_for_status()
        data = r.json()
    if data.get("retCode") != 0:
        raise RuntimeError(data.get("retMsg", "Bybit API error"))
    lst = data.get("result", {}).get("list") or []
    if not lst:
        raise ValueError(f"No ticker for {sym} on Bybit")
    t = lst[0]
    return ExchangePrices(
        exchange="bybit",
        bid=t.get("bid1Price") or t.get("lastPrice", "0"),
        ask=t.get("ask1Price") or t.get("lastPrice", "0"),
        last=t.get("lastPrice", "0"),
        mark=t.get("markPrice", "0"),
    )

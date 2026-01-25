"""MEXC USDT-margined futures (contract) provider."""

import httpx

from .base import ExchangePrices, to_canonical_symbol, to_exchange_symbol

BASE = "https://contract.mexc.com"


async def fetch_all_symbols_mexc(timeout: float) -> set[str]:
    """
    Fetch all USDT-margined perpetual symbols from MEXC.
    GET /api/v1/contract/detail; filter futureType=1 (perpetual). symbol is e.g. BTC_USDT.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/api/v1/contract/detail")
        r.raise_for_status()
        data = r.json()
    if not data.get("success") or data.get("code") != 0:
        raise RuntimeError(data.get("msg", "MEXC API error"))
    contracts = data.get("data") or []
    return {
        to_canonical_symbol(c.get("symbol", ""))
        for c in (contracts if isinstance(contracts, list) else [contracts])
        if c and (c.get("futureType") or 0) == 1
    }


async def fetch_all_prices_mexc(timeout: float) -> dict[str, ExchangePrices]:
    """
    Fetch all USDT-margined perpetual tickers from MEXC.
    GET /api/v1/contract/ticker without symbol. If data is a list, parse all; if single object, wrap.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/api/v1/contract/ticker")
        r.raise_for_status()
        data = r.json()
    if not data.get("success") or data.get("code") != 0:
        raise RuntimeError(data.get("msg", "MEXC API error"))
    raw = data.get("data")
    items: list = []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict) and raw.get("symbol"):
        items = [raw]
    out: dict[str, ExchangePrices] = {}
    for d in items:
        sym = d.get("symbol") or ""
        if not sym:
            continue
        canon = to_canonical_symbol(sym)
        last = str(d.get("lastPrice", "0"))
        out[canon] = ExchangePrices(
            exchange="mexc",
            bid=str(d.get("bid1", last)),
            ask=str(d.get("ask1", last)),
            last=last,
            mark=str(d.get("fairPrice", last)),
            funding=str(d.get("fundingRate") or d.get("funding_rate") or "0"),
        )
    return out


async def fetch_mexc(symbol: str, timeout: float) -> ExchangePrices:
    """
    Fetch futures ticker from MEXC contract API.
    Symbol format: BTC_USDT.
    """
    sym = to_exchange_symbol(symbol, "mexc")
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(
            f"{BASE}/api/v1/contract/ticker",
            params={"symbol": sym},
        )
        r.raise_for_status()
        data = r.json()
    if not data.get("success") or data.get("code") != 0:
        raise RuntimeError(data.get("msg", "MEXC API error"))
    d = data.get("data") or {}
    if isinstance(d, list):
        d = d[0] if d else {}
    last = str(d.get("lastPrice", "0"))
    bid = str(d.get("bid1", last))
    ask = str(d.get("ask1", last))
    mark = str(d.get("fairPrice", last))
    return ExchangePrices(
        exchange="mexc",
        bid=bid,
        ask=ask,
        last=last,
        mark=mark,
    )

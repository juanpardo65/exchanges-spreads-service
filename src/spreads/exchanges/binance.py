"""Binance USDT-margined futures (fapi) provider."""

import asyncio

import httpx

from .base import ExchangePrices, to_exchange_symbol

BASE = "https://fapi.binance.com"


async def fetch_all_symbols_binance(timeout: float) -> set[str]:
    """
    Fetch all USDT-margined perpetual symbols from Binance fapi.
    GET /fapi/v1/exchangeInfo; filter contractType=PERPETUAL, quoteAsset=USDT.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/fapi/v1/exchangeInfo")
        r.raise_for_status()
        data = r.json()
    symbols = data.get("symbols") or []
    return {
        s["symbol"]
        for s in symbols
        if s.get("contractType") == "PERPETUAL" and (s.get("quoteAsset") or "").upper() == "USDT"
    }


async def fetch_all_prices_binance(timeout: float) -> dict[str, ExchangePrices]:
    """
    Fetch all USDT-margined perpetual tickers from Binance in two requests.
    /fapi/v1/ticker/24hr (no symbol) + /fapi/v1/premiumIndex (no symbol); merge by symbol.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        t24, prem = await asyncio.gather(
            client.get(f"{BASE}/fapi/v1/ticker/24hr"),
            client.get(f"{BASE}/fapi/v1/premiumIndex"),
        )
    t24.raise_for_status()
    prem.raise_for_status()
    list_24 = t24.json()
    list_prem = prem.json()
    if not isinstance(list_24, list):
        list_24 = []
    if not isinstance(list_prem, list):
        list_prem = []
    mark_by_sym: dict[str, str] = {p.get("symbol", ""): str(p.get("markPrice", "0")) for p in list_prem if p.get("symbol")}
    funding_by_sym: dict[str, str] = {p.get("symbol", ""): str(p.get("lastFundingRate", "0")) for p in list_prem if p.get("symbol")}
    out: dict[str, ExchangePrices] = {}
    for t in list_24:
        sym = t.get("symbol") or ""
        if not sym:
            continue
        out[sym] = ExchangePrices(
            exchange="binance",
            bid=str(t.get("bidPrice") or t.get("lastPrice", "0")),
            ask=str(t.get("askPrice") or t.get("lastPrice", "0")),
            last=str(t.get("lastPrice", "0")),
            mark=mark_by_sym.get(sym, str(t.get("lastPrice", "0"))),
            funding=funding_by_sym.get(sym, "0"),
        )
    return out


async def fetch_binance(symbol: str, timeout: float) -> ExchangePrices:
    """
    Fetch futures ticker from Binance fapi.
    Combines /fapi/v1/ticker/24hr (bid/ask/last) and /fapi/v1/premiumIndex (mark).
    """
    sym = to_exchange_symbol(symbol, "binance")
    async with httpx.AsyncClient(timeout=timeout) as client:
        t24, prem = await asyncio.gather(
            client.get(f"{BASE}/fapi/v1/ticker/24hr", params={"symbol": sym}),
            client.get(f"{BASE}/fapi/v1/premiumIndex", params={"symbol": sym}),
        )
    t24.raise_for_status()
    prem.raise_for_status()
    d24 = t24.json()
    dprem = prem.json()
    return ExchangePrices(
        exchange="binance",
        bid=d24.get("bidPrice") or d24.get("lastPrice", "0"),
        ask=d24.get("askPrice") or d24.get("lastPrice", "0"),
        last=d24.get("lastPrice", "0"),
        mark=dprem.get("markPrice", "0"),
    )

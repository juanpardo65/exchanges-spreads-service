import httpx

from .base import ExchangePrices, to_canonical_symbol, to_exchange_symbol

BASE = "https://open-api.bingx.com"


async def fetch_all_symbols_bingx(timeout: float) -> set[str]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/openApi/swap/v2/quote/contracts")
        r.raise_for_status()
        data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(data.get("msg", "BingX API error"))
    lst = data.get("data") or []
    return {
        to_canonical_symbol(c.get("symbol", ""))
        for c in lst
        if (c.get("currency") or "").upper() == "USDT"
    }


async def fetch_all_prices_bingx(timeout: float) -> dict[str, ExchangePrices]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/openApi/swap/v2/quote/ticker")
        r.raise_for_status()
        data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(data.get("msg", "BingX API error"))
    lst = data.get("data") or []
    out: dict[str, ExchangePrices] = {}
    for t in lst:
        sym = t.get("symbol") or ""
        if not sym or "-" not in sym:
            continue
        canon = to_canonical_symbol(sym)
        last = str(t.get("lastPrice") or "0")
        bid = str(t.get("bidPrice") or last)
        ask = str(t.get("askPrice") or last)
        mark = str(t.get("fairPrice") or t.get("openPrice") or last)
        funding = str(t.get("capitalRate") or t.get("fundingRate") or "0")
        out[canon] = ExchangePrices(
            exchange="bingx",
            bid=bid,
            ask=ask,
            last=last,
            mark=mark,
            funding=funding,
        )
    return out


async def fetch_bingx(symbol: str, timeout: float) -> ExchangePrices:
    sym = to_exchange_symbol(symbol, "bingx")
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/openApi/swap/v2/quote/ticker", params={"symbol": sym})
        r.raise_for_status()
        data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(data.get("msg", "BingX API error"))
    t = data.get("data") or {}
    if isinstance(t, list):
        t = t[0] if t else {}
    last = str(t.get("lastPrice") or "0")
    return ExchangePrices(
        exchange="bingx",
        bid=str(t.get("bidPrice") or last),
        ask=str(t.get("askPrice") or last),
        last=last,
        mark=str(t.get("fairPrice") or t.get("openPrice") or last),
    )

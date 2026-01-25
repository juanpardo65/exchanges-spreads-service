import httpx

from .base import ExchangePrices, to_canonical_symbol, to_exchange_symbol

BASE = "https://api-futures.kucoin.com"


async def fetch_all_symbols_kucoin(timeout: float) -> set[str]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/api/v1/allTickers")
        r.raise_for_status()
        data = r.json()
    if data.get("code") != "200000":
        raise RuntimeError(data.get("msg", "KuCoin API error"))
    lst = data.get("data") or []
    return {
        to_canonical_symbol(t.get("symbol", ""))
        for t in lst
        if (t.get("symbol") or "").endswith("USDTM")
    }


async def fetch_all_prices_kucoin(timeout: float) -> dict[str, ExchangePrices]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/api/v1/allTickers")
        r.raise_for_status()
        data = r.json()
    if data.get("code") != "200000":
        raise RuntimeError(data.get("msg", "KuCoin API error"))
    lst = data.get("data") or []
    out: dict[str, ExchangePrices] = {}
    for t in lst:
        sym = t.get("symbol") or ""
        if not sym.endswith("USDTM"):
            continue
        canon = to_canonical_symbol(sym)
        last = str(t.get("price") or "0")
        bid = str(t.get("bestBidPrice") or last)
        ask = str(t.get("bestAskPrice") or last)
        out[canon] = ExchangePrices(
            exchange="kucoin",
            bid=bid,
            ask=ask,
            last=last,
            mark=last,
            funding="0",
        )
    return out


async def fetch_kucoin(symbol: str, timeout: float) -> ExchangePrices:
    sym = to_exchange_symbol(symbol, "kucoin")
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/api/v1/ticker", params={"symbol": sym})
        r.raise_for_status()
        data = r.json()
    if data.get("code") != "200000":
        raise RuntimeError(data.get("msg", "KuCoin API error"))
    t = data.get("data") or {}
    last = str(t.get("price") or "0")
    return ExchangePrices(
        exchange="kucoin",
        bid=str(t.get("bestBidPrice") or last),
        ask=str(t.get("bestAskPrice") or last),
        last=last,
        mark=last,
    )
